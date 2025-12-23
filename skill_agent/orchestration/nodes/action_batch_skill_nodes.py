"""
Action批次级渐进式技能生成节点实现
实现更细粒度的生成：骨架 → Track批次规划 → 批次级Action生成 → Track组装 → 技能组装

优势:
1. Token消耗降低50%（每批次3-5个actions vs 整Track 15个actions）
2. 错误隔离性优秀（单批次失败不影响其他批次）
3. 生成质量提升（避免长输出导致的后半段质量下降）
4. 流式输出支持（实时进度反馈）
"""

import json
import logging
import math
import operator
import time
from functools import lru_cache
from typing import Any, Dict, List, Tuple, TypedDict, Annotated, Optional, Literal

from langchain_core.messages import AIMessage, AnyMessage
from langgraph.graph.message import add_messages
from langgraph.types import StreamWriter
from langgraph.config import get_stream_writer
from pydantic import ValidationError

from .skill_nodes import get_llm, _prepare_payload_text
from ..streaming import (
    ProgressEventType,
    ProgressCalculator,
    emit_progress,
)
from .progressive_skill_nodes import (
    format_similar_skills,
    skeleton_generator_node,  # 复用骨架生成
    should_continue_to_track_generation,  # 复用骨架验证
    skill_assembler_node,  # 复用技能组装
    finalize_progressive_node,  # 复用最终化
    should_finalize_or_fail,  # 复用最终判断
)
from ..schemas import (
    SkillSkeletonSchema,
    ActionBatchPlan,
    ActionBatch,
    SkillAction,
    SkillTrack,
    # 新增：批次上下文相关
    BatchPhase,
    SemanticGroup,
    CompletedActionSummary,
    BatchContextState,
    SemanticRule,
)

# 参数深度验证模块（可选依赖，失败时降级）
try:
    from .parameter_validator import validate_batch_actions_deep
    HAS_DEEP_VALIDATOR = True
except ImportError:
    HAS_DEEP_VALIDATOR = False
    validate_batch_actions_deep = None  # type: ignore

logger = logging.getLogger(__name__)


# ==================== 流式输出辅助函数 ====================

def _get_writer_safe() -> Optional[Any]:
    """
    安全获取StreamWriter

    在非流式执行环境中不会报错
    """
    try:
        return get_stream_writer()
    except Exception:
        return None


def _emit_progress(
    event_type: ProgressEventType,
    message: str,
    state: Optional[Dict[str, Any]] = None,
    **kwargs
):
    """
    发送进度事件的便捷函数

    自动从state中提取上下文信息
    """
    writer = _get_writer_safe()
    if writer is None:
        logger.debug(f"[{event_type.value}] {message}")
        return

    # 从state提取进度信息
    extra_data = {}
    if state:
        track_plan = state.get("track_plan", [])
        current_track_idx = state.get("current_track_index", 0)
        batch_plan = state.get("current_track_batch_plan", [])
        current_batch_idx = state.get("current_batch_index", 0)

        extra_data["track_index"] = current_track_idx
        extra_data["total_tracks"] = len(track_plan)
        extra_data["batch_index"] = current_batch_idx
        extra_data["total_batches"] = len(batch_plan)

        # 计算进度
        if track_plan:
            # 骨架 10% + tracks 80% + 组装 10%
            skeleton_progress = 0.1
            track_progress = 0.0

            total_tracks = len(track_plan)
            if total_tracks > 0:
                completed_tracks = current_track_idx
                # 当前track内的批次进度
                if batch_plan:
                    current_track_batch_progress = current_batch_idx / len(batch_plan)
                else:
                    current_track_batch_progress = 0

                track_progress = (completed_tracks + current_track_batch_progress) / total_tracks
                track_progress *= 0.8  # 80% 权重

            extra_data["progress"] = skeleton_progress + track_progress

        if current_track_idx < len(track_plan):
            extra_data["track_name"] = track_plan[current_track_idx].get("trackName", "")

    # 合并额外参数
    extra_data.update(kwargs)

    emit_progress(writer, event_type, message, **extra_data)


# ==================== 语义验证规则定义 ====================

SEMANTIC_RULES: List[SemanticRule] = [
    # === 伤害相关规则 ===
    {
        "name": "damage_requires_animation",
        "condition": "DamageAction",
        "requires_before": ["AnimationAction", "SpawnEffectAction"],
        "suggests_after": [],
        "suggests_with": ["SpawnEffectAction"],
        "severity": "warning"
    },
    {
        "name": "area_damage_needs_effect",
        "condition": "AreaOfEffectAction",
        "requires_before": [],
        "suggests_after": [],
        "suggests_with": ["SpawnEffectAction", "CameraAction"],
        "severity": "info"
    },
    {
        "name": "projectile_requires_spawn",
        "condition": "ProjectileAction",
        "requires_before": ["AnimationAction"],
        "suggests_after": ["DamageAction"],
        "suggests_with": ["SpawnEffectAction"],
        "severity": "warning"
    },

    # === Buff/Debuff相关规则 ===
    {
        "name": "buff_needs_effect",
        "condition": "BuffAction",
        "requires_before": [],
        "suggests_after": [],
        "suggests_with": ["SpawnEffectAction"],
        "severity": "info"
    },
    {
        "name": "heal_with_effect",
        "condition": "HealAction",
        "requires_before": [],
        "suggests_after": [],
        "suggests_with": ["SpawnEffectAction", "AudioAction"],
        "severity": "info"
    },
    {
        "name": "shield_with_visual",
        "condition": "ShieldAction",
        "requires_before": [],
        "suggests_after": [],
        "suggests_with": ["SpawnEffectAction"],
        "severity": "info"
    },

    # === 移动相关规则 ===
    {
        "name": "movement_followed_by_action",
        "condition": "MovementAction",
        "requires_before": [],
        "suggests_after": ["DamageAction", "SpawnEffectAction"],
        "suggests_with": [],
        "severity": "info"
    },
    {
        "name": "teleport_needs_effect",
        "condition": "TeleportAction",
        "requires_before": [],
        "suggests_after": [],
        "suggests_with": ["SpawnEffectAction", "AudioAction"],
        "severity": "warning"
    },
    {
        "name": "dash_with_trail",
        "condition": "DashAction",
        "requires_before": ["AnimationAction"],
        "suggests_after": ["DamageAction"],
        "suggests_with": ["SpawnEffectAction"],
        "severity": "info"
    },

    # === 音效相关规则 ===
    {
        "name": "audio_with_animation",
        "condition": "AudioAction",
        "requires_before": [],
        "suggests_after": [],
        "suggests_with": ["AnimationAction"],
        "severity": "info"
    },
    {
        "name": "play_sound_with_action",
        "condition": "PlaySoundAction",
        "requires_before": [],
        "suggests_after": [],
        "suggests_with": ["AnimationAction", "SpawnEffectAction"],
        "severity": "info"
    },

    # === 镜头相关规则 ===
    {
        "name": "camera_shake_with_impact",
        "condition": "CameraAction",
        "requires_before": [],
        "suggests_after": [],
        "suggests_with": ["DamageAction", "SpawnEffectAction"],
        "severity": "info"
    },
    {
        "name": "camera_focus_before_skill",
        "condition": "CameraFocusAction",
        "requires_before": [],
        "suggests_after": ["AnimationAction", "SpawnEffectAction"],
        "suggests_with": [],
        "severity": "info"
    },

    # === 召唤相关规则 ===
    {
        "name": "summon_with_effect",
        "condition": "SummonAction",
        "requires_before": ["AnimationAction"],
        "suggests_after": [],
        "suggests_with": ["SpawnEffectAction", "AudioAction"],
        "severity": "warning"
    },

    # === 控制相关规则 ===
    {
        "name": "control_with_animation",
        "condition": "ControlAction",
        "requires_before": ["AnimationAction"],
        "suggests_after": [],
        "suggests_with": ["SpawnEffectAction"],
        "severity": "info"
    },
    {
        "name": "stun_with_effect",
        "condition": "StunAction",
        "requires_before": [],
        "suggests_after": [],
        "suggests_with": ["SpawnEffectAction", "AudioAction"],
        "severity": "info"
    },

    # === 碰撞相关规则 ===
    {
        "name": "collision_after_projectile",
        "condition": "CollisionAction",
        "requires_before": ["ProjectileAction", "SpawnEffectAction"],
        "suggests_after": ["DamageAction"],
        "suggests_with": [],
        "severity": "info"
    },

    # === 资源相关规则 ===
    {
        "name": "resource_with_effect",
        "condition": "ResourceAction",
        "requires_before": [],
        "suggests_after": [],
        "suggests_with": ["SpawnEffectAction"],
        "severity": "info"
    },
]


# === 阶段性规则（根据批次阶段应用不同规则）===

PHASE_RULES: Dict[str, List[str]] = {
    "setup": [
        "动画Action应放在起手阶段",
        "准备特效应在伤害前生成",
        "镜头聚焦适合放在技能开始",
    ],
    "main": [
        "核心伤害和效果应在主体阶段",
        "Buff/Debuff应用通常在主体阶段",
        "AOE伤害适合放在主体阶段中段",
    ],
    "cleanup": [
        "后摇动画应在收尾阶段",
        "消散特效应在收尾阶段",
        "技能结束音效放在收尾",
    ],
}


# === Track类型特定规则 ===

TRACK_TYPE_RULES: Dict[str, Dict[str, Any]] = {
    "animation": {
        "primary_actions": ["AnimationAction"],
        "forbidden_actions": ["DamageAction", "BuffAction"],  # 伤害和Buff不应在动画轨道
        "typical_count": (1, 5),  # 典型action数量范围
    },
    "effect": {
        "primary_actions": ["SpawnEffectAction", "DamageAction", "BuffAction", "HealAction"],
        "forbidden_actions": [],
        "typical_count": (2, 10),
    },
    "audio": {
        "primary_actions": ["AudioAction", "PlaySoundAction"],
        "forbidden_actions": ["DamageAction", "MovementAction"],
        "typical_count": (1, 5),
    },
    "movement": {
        "primary_actions": ["MovementAction", "TeleportAction", "DashAction"],
        "forbidden_actions": [],
        "typical_count": (1, 3),
    },
    "camera": {
        "primary_actions": ["CameraAction", "CameraFocusAction"],
        "forbidden_actions": ["DamageAction", "BuffAction"],
        "typical_count": (1, 3),
    },
}

# 功能关键词到Action类型的映射
SEMANTIC_KEYWORD_MAP: Dict[str, List[str]] = {
    # 动画相关
    "动画": ["AnimationAction"],
    "播放": ["AnimationAction", "PlaySoundAction"],
    "前摇": ["AnimationAction"],
    "后摇": ["AnimationAction"],
    "施法": ["AnimationAction"],
    # 伤害相关
    "伤害": ["DamageAction"],
    "攻击": ["DamageAction"],
    "造成": ["DamageAction"],
    "打击": ["DamageAction"],
    # 特效相关
    "特效": ["SpawnEffectAction"],
    "效果": ["SpawnEffectAction"],
    "生成": ["SpawnEffectAction"],
    "粒子": ["SpawnEffectAction"],
    # Buff/Debuff相关
    "buff": ["BuffAction"],
    "增益": ["BuffAction"],
    "debuff": ["DebuffAction"],
    "减益": ["DebuffAction"],
    "状态": ["BuffAction", "DebuffAction"],
    "燃烧": ["DebuffAction"],
    "冻结": ["DebuffAction"],
    # 移动相关
    "移动": ["MovementAction"],
    "位移": ["MovementAction"],
    "冲刺": ["MovementAction"],
    "传送": ["MovementAction"],
    # 音效相关
    "音效": ["PlaySoundAction"],
    "声音": ["PlaySoundAction"],
}


# ==================== 上下文管理函数 ====================

def create_initial_context(
    track_plan_item: Dict[str, Any],
    skeleton: Dict[str, Any],
    batch_plan: List[Dict[str, Any]]
) -> BatchContextState:
    """
    创建初始批次上下文

    Args:
        track_plan_item: 当前Track的计划信息
        skeleton: 技能骨架信息
        batch_plan: 批次计划列表

    Returns:
        初始化的BatchContextState
    """
    purpose = track_plan_item.get("purpose", "")
    track_name = track_plan_item.get("trackName", "Unknown Track")

    # 解析purpose提取建议的Action类型
    suggested_types = parse_purpose_to_action_types(purpose)

    # 根据Track名称推断初始约束
    must_follow = []
    if "animation" in track_name.lower():
        must_follow.append("动画Action应在其他Action之前")
    elif "effect" in track_name.lower():
        must_follow.append("特效和伤害Action应在动画之后")

    return {
        "batch_id": 0,
        "total_batches": len(batch_plan),
        "phase": BatchPhase.SETUP.value,
        "design_intent": purpose,
        "current_goal": batch_plan[0].get("context", "") if batch_plan else "",
        "completed_actions": [],
        "used_action_types": [],
        "occupied_frames": [],
        "must_follow": must_follow,
        "suggested_types": suggested_types,
        "avoid_patterns": [],
        "prerequisites_met": [],
        "pending_effects": [],
        "violations": [],
    }


def update_context_after_batch(
    context: BatchContextState,
    batch_actions: List[Dict[str, Any]],
    batch_plan: List[Dict[str, Any]],
    next_batch_idx: int
) -> BatchContextState:
    """
    批次生成完成后更新上下文

    Args:
        context: 当前上下文
        batch_actions: 本批次生成的actions
        batch_plan: 批次计划列表
        next_batch_idx: 下一个批次索引

    Returns:
        更新后的BatchContextState
    """
    # 复制上下文（避免直接修改）
    new_context: BatchContextState = dict(context)  # type: ignore

    # 更新已完成actions摘要
    completed = list(context.get("completed_actions", []))
    for action in batch_actions:
        params = action.get("parameters", {})
        odin_type = params.get("_odin_type", "")
        # 提取简化类型名（如 "DamageAction"）
        action_type = extract_action_type_name(odin_type)

        # 提取关键参数
        key_params = extract_key_params(params)

        completed.append({
            "frame": action.get("frame", 0),
            "duration": action.get("duration", 0),
            "action_type": action_type,
            "key_params": key_params,
        })
    new_context["completed_actions"] = completed

    # 更新已使用的Action类型
    used_types = list(context.get("used_action_types", []))
    for action in batch_actions:
        action_type = extract_action_type_name(
            action.get("parameters", {}).get("_odin_type", "")
        )
        if action_type and action_type not in used_types:
            used_types.append(action_type)
    new_context["used_action_types"] = used_types

    # 更新已占用帧区间
    occupied = list(context.get("occupied_frames", []))
    for action in batch_actions:
        frame = action.get("frame", 0)
        duration = action.get("duration", 0)
        occupied.append((frame, frame + duration))
    # 排序并合并重叠区间
    new_context["occupied_frames"] = merge_frame_intervals(occupied)

    # 更新批次信息
    new_context["batch_id"] = next_batch_idx

    # 更新阶段
    if next_batch_idx < len(batch_plan):
        total = len(batch_plan)
        if next_batch_idx < total * 0.3:
            new_context["phase"] = BatchPhase.SETUP.value
        elif next_batch_idx < total * 0.7:
            new_context["phase"] = BatchPhase.MAIN.value
        else:
            new_context["phase"] = BatchPhase.CLEANUP.value

        new_context["current_goal"] = batch_plan[next_batch_idx].get("context", "")

    # 检查语义规则，更新prerequisites_met
    prerequisites_met = list(context.get("prerequisites_met", []))
    if "AnimationAction" in used_types:
        prerequisites_met.append("animation_played")
    if "SpawnEffectAction" in used_types:
        prerequisites_met.append("effect_spawned")
    new_context["prerequisites_met"] = list(set(prerequisites_met))

    return new_context


def format_context_for_prompt(context: BatchContextState) -> str:
    """
    将上下文格式化为prompt文本

    Args:
        context: 批次上下文

    Returns:
        格式化的文本，用于插入prompt
    """
    lines = []

    # 设计意图
    if context.get("design_intent"):
        lines.append(f"**Track设计意图**: {context['design_intent']}")

    # 当前批次目标
    if context.get("current_goal"):
        lines.append(f"**当前批次目标**: {context['current_goal']}")

    # 阶段信息
    phase = context.get("phase", "main")
    phase_desc = {
        "setup": "起手阶段（动画前摇、准备特效）",
        "main": "主体阶段（核心伤害、主要效果）",
        "cleanup": "收尾阶段（后摇、消散特效）"
    }
    lines.append(f"**当前阶段**: {phase_desc.get(phase, phase)}")

    # 已完成actions摘要
    completed = context.get("completed_actions", [])
    if completed:
        lines.append("**已生成Actions**:")
        for action in completed[-8:]:  # 只显示最近8个
            lines.append(
                f"  - 帧{action['frame']}-{action['frame']+action['duration']}: "
                f"{action['action_type']}"
            )
    else:
        lines.append("**已生成Actions**: 无（这是第一个批次）")

    # 已占用帧区间
    occupied = context.get("occupied_frames", [])
    if occupied:
        intervals = ", ".join([f"{s}-{e}" for s, e in occupied[-5:]])
        lines.append(f"**已占用帧区间**: {intervals}")

    # 约束和建议
    if context.get("must_follow"):
        lines.append(f"**必须遵守**: {'; '.join(context['must_follow'])}")

    if context.get("suggested_types"):
        lines.append(f"**建议Action类型**: {', '.join(context['suggested_types'][:5])}")

    if context.get("avoid_patterns"):
        lines.append(f"**应避免**: {'; '.join(context['avoid_patterns'][:3])}")

    return "\n".join(lines)


# ==================== 辅助函数 ====================

def extract_action_type_name(odin_type: str) -> str:
    """
    从_odin_type字符串提取简化的Action类型名

    Args:
        odin_type: 如 "6|SkillSystem.Actions.DamageAction, Assembly-CSharp"

    Returns:
        简化名称如 "DamageAction"
    """
    if not odin_type:
        return "Unknown"

    # 去掉ID前缀
    if "|" in odin_type:
        odin_type = odin_type.split("|", 1)[1]

    # 提取类名
    if "." in odin_type:
        parts = odin_type.split(".")
        # 找到Actions后面的类名
        for i, part in enumerate(parts):
            if part == "Actions" and i + 1 < len(parts):
                # 去掉", Assembly-CSharp"后缀
                class_name = parts[i + 1].split(",")[0].strip()
                return class_name

    # 回退：返回最后一个部分
    return odin_type.split(".")[-1].split(",")[0].strip()


def extract_key_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    提取Action参数中的关键参数（用于摘要）

    Args:
        params: 完整的parameters字典

    Returns:
        只包含关键参数的字典
    """
    # 关键参数白名单
    key_param_names = {
        "damage", "damageAmount", "healAmount",
        "effectPrefab", "effectName",
        "animationClipName", "clipName",
        "buffId", "debuffId", "duration",
        "soundName", "audioClip",
        "moveDistance", "direction",
    }

    result = {}
    for key, value in params.items():
        if key == "_odin_type":
            continue
        if key in key_param_names:
            result[key] = value
        # 也提取数值型参数（可能是伤害、持续时间等）
        elif isinstance(value, (int, float)) and value != 0:
            result[key] = value

    # 限制参数数量
    return dict(list(result.items())[:5])


def merge_frame_intervals(intervals: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """
    合并重叠的帧区间

    Args:
        intervals: 帧区间列表 [(start, end), ...]

    Returns:
        合并后的区间列表
    """
    if not intervals:
        return []

    # 排序
    sorted_intervals = sorted(intervals, key=lambda x: x[0])

    merged = [sorted_intervals[0]]
    for start, end in sorted_intervals[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:  # 有重叠
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))

    return merged


def parse_purpose_to_action_types(purpose: str) -> List[str]:
    """
    从purpose文本解析建议的Action类型

    Args:
        purpose: Track用途描述

    Returns:
        建议使用的Action类型列表
    """
    suggested = []
    purpose_lower = purpose.lower()

    for keyword, action_types in SEMANTIC_KEYWORD_MAP.items():
        if keyword in purpose_lower:
            for action_type in action_types:
                if action_type not in suggested:
                    suggested.append(action_type)

    return suggested


def validate_semantic_rules(
    actions: List[Dict[str, Any]],
    context: BatchContextState,
    track_type: Optional[str] = None
) -> List[str]:
    """
    验证actions是否符合语义规则（增强版）

    Args:
        actions: 当前批次的actions
        context: 批次上下文
        track_type: Track类型（animation/effect/audio等）

    Returns:
        违规信息列表
    """
    violations = []
    used_types = list(context.get("used_action_types", []))
    current_phase = context.get("phase", "main")

    # 收集本批次的Action类型
    batch_types = []
    for action in actions:
        action_type = extract_action_type_name(
            action.get("parameters", {}).get("_odin_type", "")
        )
        batch_types.append(action_type)

    all_types = used_types + batch_types

    # === 1. 基础语义规则验证 ===
    for rule in SEMANTIC_RULES:
        condition = rule["condition"]

        # 检查本批次是否有触发条件的Action
        if condition not in batch_types:
            continue

        # 检查requires_before
        for required in rule.get("requires_before", []):
            if required not in all_types:
                severity = rule.get("severity", "warning")
                if severity == "error":
                    violations.append(
                        f"[错误] {condition} 需要 {required} 先出现"
                    )
                elif severity == "warning":
                    violations.append(
                        f"[警告] 建议在 {condition} 之前添加 {required}"
                    )

        # 检查suggests_with
        for suggested in rule.get("suggests_with", []):
            if suggested not in batch_types and suggested not in used_types:
                violations.append(
                    f"[建议] {condition} 通常与 {suggested} 配合使用"
                )

    # === 2. Track类型特定规则验证 ===
    if track_type and track_type in TRACK_TYPE_RULES:
        track_rules = TRACK_TYPE_RULES[track_type]

        # 检查禁止的Action类型
        forbidden = track_rules.get("forbidden_actions", [])
        for action_type in batch_types:
            if action_type in forbidden:
                violations.append(
                    f"[警告] {action_type} 不应出现在 {track_type} 轨道中"
                )

        # 检查是否使用了推荐的Action类型
        primary = track_rules.get("primary_actions", [])
        has_primary = any(at in primary for at in batch_types)
        if not has_primary and batch_types:
            violations.append(
                f"[建议] {track_type} 轨道建议使用: {', '.join(primary[:3])}"
            )

    # === 3. 阶段特定规则验证 ===
    if current_phase in PHASE_RULES:
        phase_hints = PHASE_RULES[current_phase]

        # 阶段性提示（只在特定情况下添加）
        if current_phase == "setup":
            # 检查起手阶段是否缺少动画
            if "AnimationAction" not in batch_types and "AnimationAction" not in used_types:
                if any(at in batch_types for at in ["DamageAction", "BuffAction"]):
                    violations.append(
                        f"[建议] 起手阶段应先播放动画，再执行伤害/Buff"
                    )

        elif current_phase == "cleanup":
            # 检查收尾阶段是否有不合适的Action
            cleanup_unfriendly = ["DamageAction", "BuffAction", "ProjectileAction"]
            for action_type in batch_types:
                if action_type in cleanup_unfriendly:
                    violations.append(
                        f"[建议] {action_type} 不适合放在收尾阶段"
                    )

    # === 4. 时间轴冲突检测 ===
    occupied_frames = context.get("occupied_frames", [])
    for action in actions:
        frame = action.get("frame", 0)
        duration = action.get("duration", 0)
        action_end = frame + duration

        # 检查是否与已占用帧严重重叠（允许少量重叠）
        for start, end in occupied_frames:
            overlap_start = max(frame, start)
            overlap_end = min(action_end, end)
            overlap = overlap_end - overlap_start

            if overlap > duration * 0.5:  # 超过50%重叠
                action_type = extract_action_type_name(
                    action.get("parameters", {}).get("_odin_type", "")
                )
                violations.append(
                    f"[建议] {action_type}(帧{frame}-{action_end}) 与已有Action重叠较多"
                )
                break

    return violations


def validate_track_type_compliance(
    actions: List[Dict[str, Any]],
    track_type: str
) -> Tuple[List[str], List[str]]:
    """
    验证Track内actions是否符合Track类型要求

    Args:
        actions: Track内的所有actions
        track_type: Track类型

    Returns:
        (errors, warnings) 元组
    """
    errors = []
    warnings = []

    if track_type not in TRACK_TYPE_RULES:
        return errors, warnings

    rules = TRACK_TYPE_RULES[track_type]
    primary_actions = rules.get("primary_actions", [])
    forbidden_actions = rules.get("forbidden_actions", [])
    typical_count = rules.get("typical_count", (1, 20))

    # 收集所有action类型
    action_types = []
    for action in actions:
        action_type = extract_action_type_name(
            action.get("parameters", {}).get("_odin_type", "")
        )
        action_types.append(action_type)

    # 检查禁止的Action
    for action_type in action_types:
        if action_type in forbidden_actions:
            errors.append(
                f"Track类型'{track_type}'不允许包含'{action_type}'"
            )

    # 检查数量范围
    min_count, max_count = typical_count
    actual_count = len(actions)
    if actual_count < min_count:
        warnings.append(
            f"Track '{track_type}' action数量({actual_count})低于建议值({min_count})"
        )
    elif actual_count > max_count:
        warnings.append(
            f"Track '{track_type}' action数量({actual_count})超过建议值({max_count})"
        )

    # 检查是否有主要Action类型
    has_primary = any(at in primary_actions for at in action_types)
    if not has_primary and action_types:
        warnings.append(
            f"Track '{track_type}' 缺少主要Action类型: {', '.join(primary_actions[:2])}"
        )

    return errors, warnings


# ==================== 语义批次规划函数 ====================

def parse_purpose_to_semantic_groups(purpose: str) -> List[SemanticGroup]:
    """
    解析purpose文本为语义功能组

    Args:
        purpose: Track用途描述，如 "播放施法动画、生成火焰特效、造成范围伤害"

    Returns:
        语义功能组列表
    """
    groups: List[SemanticGroup] = []

    # 分割purpose（支持逗号、顿号、和）
    import re
    segments = re.split(r'[,，、;；和]', purpose)

    for i, segment in enumerate(segments):
        segment = segment.strip()
        if not segment:
            continue

        # 解析关键词
        keywords = []
        suggested_types = []
        for keyword, action_types in SEMANTIC_KEYWORD_MAP.items():
            if keyword in segment.lower():
                keywords.append(keyword)
                for at in action_types:
                    if at not in suggested_types:
                        suggested_types.append(at)

        if not keywords:
            # 无法识别的功能，使用默认
            keywords = [segment[:10]]
            suggested_types = []

        # 确定阶段
        total_segments = len(segments)
        if i < total_segments * 0.3:
            phase = BatchPhase.SETUP.value
        elif i < total_segments * 0.7:
            phase = BatchPhase.MAIN.value
        else:
            phase = BatchPhase.CLEANUP.value

        groups.append({
            "name": segment[:20],
            "keywords": keywords,
            "suggested_action_types": suggested_types,
            "estimated_count": max(1, len(suggested_types)),
            "phase": phase,
        })

    return groups


def calculate_semantic_batch_plan(
    track_name: str,
    estimated_actions: int,
    total_duration: int,
    purpose: str
) -> Tuple[List[Dict[str, Any]], BatchContextState]:
    """
    语义化批次规划（替代原有的纯数量驱动划分）

    策略:
    1. 解析purpose提取语义功能组
    2. 基于功能组划分批次（保持语义关联）
    3. 数量上限作为兜底

    Args:
        track_name: Track名称
        estimated_actions: 预估action数量
        total_duration: 技能总时长（帧数）
        purpose: Track用途描述

    Returns:
        (批次计划列表, 初始上下文)
    """
    # 解析语义功能组
    semantic_groups = parse_purpose_to_semantic_groups(purpose)

    if not semantic_groups:
        # 回退到数量驱动策略
        logger.warning(f"⚠️ 无法解析purpose语义，回退到数量驱动策略")
        batch_plan = calculate_batch_plan(
            track_name, estimated_actions, total_duration, purpose
        )
        # 创建基础上下文
        context = create_initial_context(
            {"trackName": track_name, "purpose": purpose},
            {"totalDuration": total_duration},
            batch_plan
        )
        return batch_plan, context

    # 基于语义组生成批次计划
    batch_plan = []
    remaining_actions = estimated_actions
    frame_per_group = total_duration // len(semantic_groups) if semantic_groups else total_duration

    for i, group in enumerate(semantic_groups):
        # 计算本组的action数量
        group_action_count = min(
            group["estimated_count"] + 1,  # 语义组估计 + 1的buffer
            remaining_actions,
            5  # 上限
        )

        if group_action_count <= 0:
            continue

        # 计算帧范围
        start_frame = i * frame_per_group
        end_frame = min((i + 1) * frame_per_group, total_duration)

        # 生成批次上下文（包含语义信息）
        context_desc = f"{group['name']}"
        if group["suggested_action_types"]:
            context_desc += f"（建议: {', '.join(group['suggested_action_types'][:2])}）"

        batch_plan.append({
            "batch_index": len(batch_plan),
            "action_count": group_action_count,
            "start_frame_hint": start_frame,
            "end_frame_hint": end_frame,
            "context": context_desc,
            "semantic_group": group,  # 附加语义信息
        })

        remaining_actions -= group_action_count

    # 如果还有剩余actions，追加到最后一个批次
    if remaining_actions > 0 and batch_plan:
        batch_plan[-1]["action_count"] += remaining_actions

    # 确保至少有一个批次
    if not batch_plan:
        batch_plan.append({
            "batch_index": 0,
            "action_count": estimated_actions,
            "start_frame_hint": 0,
            "end_frame_hint": total_duration,
            "context": purpose[:50],
            "semantic_group": None,
        })

    logger.info(
        f"📊 语义批次规划完成: {track_name}\n"
        f"   - 识别 {len(semantic_groups)} 个功能组 → {len(batch_plan)} 个批次"
    )

    # 创建初始上下文
    context = create_initial_context(
        {"trackName": track_name, "purpose": purpose},
        {"totalDuration": total_duration},
        batch_plan
    )

    # 将语义组信息添加到上下文
    if semantic_groups:
        all_suggested = []
        for group in semantic_groups:
            all_suggested.extend(group["suggested_action_types"])
        context["suggested_types"] = list(set(all_suggested))

    return batch_plan, context


# ==================== State 定义 ====================

class ActionBatchProgressiveState(TypedDict):
    """
    Action批次级渐进式生成State

    扩展自ProgressiveSkillGenerationState,增加批次级字段和语义上下文
    """
    # === 输入 ===
    requirement: str
    similar_skills: List[Dict[str, Any]]

    # === 阶段1: 骨架生成（复用） ===
    skill_skeleton: Dict[str, Any]
    skeleton_validation_errors: List[str]
    track_plan: List[Dict[str, Any]]

    # === 阶段2: Track批次规划（新增） ===
    current_track_index: int  # 当前Track索引
    current_track_batch_plan: List[Dict[str, Any]]  # 当前Track的批次计划

    # === 阶段3: 批次级Action生成（新增） ===
    current_batch_index: int  # 当前批次索引
    current_batch_actions: List[Dict[str, Any]]  # 当前批次生成的actions
    current_batch_errors: List[str]  # 当前批次验证错误
    batch_retry_count: int  # 当前批次重试次数
    max_batch_retries: int  # 单批次最大重试次数（默认2,快速失败）

    # === 语义上下文（新增） ===
    batch_context: BatchContextState  # 批次上下文状态，用于跨批次传递设计意图和约束

    # === Track内actions累积（新增） ===
    accumulated_track_actions: List[Dict[str, Any]]  # 当前Track已完成的所有批次actions

    # === 阶段4: Track组装（复用但修改） ===
    generated_tracks: List[Dict[str, Any]]  # 已完成的Tracks

    # === 阶段5: 技能组装（复用） ===
    assembled_skill: Dict[str, Any]
    final_validation_errors: List[str]

    # === 兼容字段 ===
    final_result: Dict[str, Any]
    is_valid: bool

    # === Token监控字段（新增） ===
    total_tokens_used: int  # 累计使用的token数
    batch_token_history: List[Dict[str, Any]]  # 每批次token使用记录 [{batch_idx, input_tokens, output_tokens}]
    token_budget: int  # Token预算上限（默认100000）
    adaptive_batch_size: int  # 自适应批次大小（根据token使用动态调整）

    # === 流式输出支持（新增） ===
    progress_calculator: Optional[Dict[str, Any]]  # 进度计算器状态

    # === 通用 ===
    # 使用add_messages reducer确保消息正确累积
    messages: Annotated[List[AnyMessage], add_messages]
    thread_id: str


# ==================== Token监控辅助函数 ====================
# P1-2: Token配置从配置模块读取
from ..config import get_skill_gen_config as _get_config

def _get_batch_config():
    """获取批次配置"""
    return _get_config().batch

DEFAULT_TOKEN_BUDGET = _get_config().batch.token_budget
MIN_BATCH_SIZE = _get_config().batch.min_batch_size
MAX_BATCH_SIZE = _get_config().batch.max_batch_size


def estimate_tokens_for_batch(batch_size: int, track_purpose: str) -> int:
    """
    估算批次生成所需的token数

    基于经验值估算：
    - 输入tokens约 = 基础prompt(~1000) + 每action schema(~200) + 上下文(~500)
    - 输出tokens约 = 每action(~150)

    Args:
        batch_size: 批次action数量
        track_purpose: Track用途（复杂用途需要更多token）

    Returns:
        预估token数
    """
    base_input = 1500  # 基础prompt + 系统指令
    schema_tokens = batch_size * 250  # 每个action的schema
    context_tokens = 500  # 语义上下文
    output_tokens = batch_size * 180  # 预估输出

    # 复杂purpose增加10%
    complexity_factor = 1.1 if len(track_purpose) > 50 else 1.0

    return int((base_input + schema_tokens + context_tokens + output_tokens) * complexity_factor)


def calculate_adaptive_batch_size(
    remaining_budget: int,
    default_batch_size: int,
    recent_token_usage: List[Dict[str, Any]],
    remaining_batches: int
) -> int:
    """
    根据token使用情况动态调整batch_size

    策略：
    1. 如果剩余预算紧张，减小batch_size
    2. 如果前几批效率高（token/action低），可以适当增大batch_size
    3. 保持在[MIN_BATCH_SIZE, MAX_BATCH_SIZE]范围内

    Args:
        remaining_budget: 剩余token预算
        default_batch_size: 默认批次大小
        recent_token_usage: 最近几批的token使用记录
        remaining_batches: 剩余批次数

    Returns:
        调整后的batch_size
    """
    if remaining_batches <= 0:
        return default_batch_size

    # 计算平均每批次token使用
    if recent_token_usage:
        total_tokens = sum(r.get("total_tokens", 0) for r in recent_token_usage[-3:])
        avg_tokens_per_batch = total_tokens / len(recent_token_usage[-3:])
    else:
        # 无历史数据，使用估算值
        avg_tokens_per_batch = estimate_tokens_for_batch(default_batch_size, "")

    # 预估剩余所需token
    estimated_remaining_tokens = avg_tokens_per_batch * remaining_batches

    # 如果预算紧张（剩余预算 < 预估所需的1.5倍），减小batch_size
    if remaining_budget < estimated_remaining_tokens * 1.5:
        # 按比例缩减
        reduction_ratio = remaining_budget / (estimated_remaining_tokens * 1.5)
        adjusted_size = max(MIN_BATCH_SIZE, int(default_batch_size * reduction_ratio))
        logger.info(
            f"⚠️ Token预算紧张，调整batch_size: {default_batch_size} -> {adjusted_size}"
        )
        return adjusted_size

    # 如果预算充裕且历史效率高，可以考虑增大（但保守增加）
    if remaining_budget > estimated_remaining_tokens * 3 and recent_token_usage:
        avg_tokens_per_action = sum(
            r.get("total_tokens", 0) / max(1, r.get("action_count", 1))
            for r in recent_token_usage[-3:]
        ) / len(recent_token_usage[-3:])

        # 效率高（每action token < 400）则尝试增大
        if avg_tokens_per_action < 400 and default_batch_size < MAX_BATCH_SIZE:
            adjusted_size = min(MAX_BATCH_SIZE, default_batch_size + 1)
            logger.info(
                f"📈 Token效率良好，调整batch_size: {default_batch_size} -> {adjusted_size}"
            )
            return adjusted_size

    return default_batch_size


def update_token_tracking(
    state: ActionBatchProgressiveState,
    input_tokens: int,
    output_tokens: int,
    batch_idx: int,
    action_count: int
) -> Dict[str, Any]:
    """
    更新token追踪信息

    Args:
        state: 当前State
        input_tokens: 本次调用的输入token数
        output_tokens: 本次调用的输出token数
        batch_idx: 当前批次索引
        action_count: 生成的action数量

    Returns:
        更新字段的字典
    """
    total_used = state.get("total_tokens_used", 0) + input_tokens + output_tokens
    history = list(state.get("batch_token_history", []))
    budget = state.get("token_budget", DEFAULT_TOKEN_BUDGET)

    # 记录本批次token使用
    history.append({
        "batch_idx": batch_idx,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "action_count": action_count,
    })

    # 计算剩余预算和使用率
    remaining = budget - total_used
    usage_rate = total_used / budget if budget > 0 else 1.0

    if usage_rate > 0.8:
        logger.warning(f"⚠️ Token使用已达 {usage_rate*100:.1f}%，剩余 {remaining:,}")

    return {
        "total_tokens_used": total_used,
        "batch_token_history": history,
    }


def get_token_usage_summary(state: ActionBatchProgressiveState) -> str:
    """
    获取token使用摘要

    Args:
        state: 当前State

    Returns:
        格式化的token使用摘要字符串
    """
    total_used = state.get("total_tokens_used", 0)
    budget = state.get("token_budget", DEFAULT_TOKEN_BUDGET)
    history = state.get("batch_token_history", [])

    if not history:
        return "无token使用记录"

    avg_per_batch = total_used / len(history) if history else 0
    total_actions = sum(r.get("action_count", 0) for r in history)
    avg_per_action = total_used / total_actions if total_actions > 0 else 0

    return (
        f"Token使用: {total_used:,}/{budget:,} ({total_used/budget*100:.1f}%)\n"
        f"批次数: {len(history)}, 平均每批次: {avg_per_batch:,.0f}\n"
        f"Actions数: {total_actions}, 平均每Action: {avg_per_action:,.0f}"
    )


# ==================== 批次规划辅助函数 ====================

def calculate_batch_plan(
    track_name: str,
    estimated_actions: int,
    total_duration: int,
    purpose: str
) -> List[Dict[str, Any]]:
    """
    动态计算Track的批次划分方案

    策略:
    - 简单Track (≤5 actions): 不分批
    - 中等Track (6-10 actions): 分2批
    - 复杂Track (11-15 actions): 分3批
    - 超级复杂Track (>15 actions): 每批3-5个actions

    Args:
        track_name: Track名称
        estimated_actions: 预估action数量
        total_duration: 技能总时长（帧数）
        purpose: Track用途描述

    Returns:
        批次计划列表，每项包含batch_index, action_count, start_frame_hint, end_frame_hint, context
    """
    # 确定批次策略
    if estimated_actions <= 5:
        # 简单Track: 不分批
        batch_size = estimated_actions
        num_batches = 1
    elif estimated_actions <= 10:
        # 中等Track: 分2批
        batch_size = math.ceil(estimated_actions / 2)
        num_batches = 2
    elif estimated_actions <= 15:
        # 复杂Track: 分3批
        batch_size = math.ceil(estimated_actions / 3)
        num_batches = 3
    else:
        # 超级复杂Track: 每批最多5个
        batch_size = 5
        num_batches = math.ceil(estimated_actions / batch_size)

    logger.info(
        f"📊 Track '{track_name}' 批次规划: "
        f"{estimated_actions} actions → {num_batches} 批次, 每批约 {batch_size} actions"
    )

    # 生成批次计划
    batch_plan = []
    frame_per_batch = total_duration // num_batches if num_batches > 0 else total_duration

    for i in range(num_batches):
        # 计算本批次的action数量（最后一批可能更少）
        if i == num_batches - 1:
            # 最后一批: 剩余所有actions
            batch_action_count = estimated_actions - (batch_size * i)
        else:
            batch_action_count = min(batch_size, estimated_actions - (batch_size * i))

        # 计算帧范围提示
        start_frame = i * frame_per_batch
        end_frame = min((i + 1) * frame_per_batch, total_duration)

        # 生成批次上下文描述（根据批次在Track中的位置）
        if num_batches == 1:
            context = f"{purpose}"
        elif i == 0:
            context = f"{track_name}的前期阶段: {purpose[:40]}"
        elif i == num_batches - 1:
            context = f"{track_name}的收尾阶段"
        else:
            context = f"{track_name}的中期阶段（批次{i+1}/{num_batches}）"

        batch_plan.append({
            "batch_index": i,
            "action_count": batch_action_count,
            "start_frame_hint": start_frame,
            "end_frame_hint": end_frame,
            "context": context
        })

    return batch_plan


# ==================== 阶段2: Track批次规划节点 ====================

def plan_track_batches_node(state: ActionBatchProgressiveState) -> Dict[str, Any]:
    """
    Track批次规划节点（增强版：语义化批次规划 + 流式输出）

    职责:
    1. 获取当前Track的信息（trackName, purpose, estimatedActions）
    2. 使用语义批次规划算法（解析purpose提取功能组）
    3. 初始化批次上下文，用于跨批次传递设计意图
    4. 发送进度事件

    输出:
    - current_track_batch_plan: 批次计划列表（包含语义信息）
    - current_batch_index: 初始化为0
    - accumulated_track_actions: 初始化为空数组
    - batch_retry_count: 初始化为0
    - batch_context: 批次上下文状态
    """
    skeleton = state.get("skill_skeleton", {})
    track_plan = state.get("track_plan", [])
    current_track_idx = state.get("current_track_index", 0)

    # 新任务开始时（第一个Track）清理缓存
    if current_track_idx == 0:
        clear_action_schema_cache()
        logger.debug("📋 新任务开始，已清理Action Schema缓存")
        # 发送生成开始事件
        _emit_progress(
            ProgressEventType.GENERATION_STARTED,
            f"开始生成技能: {skeleton.get('skillName', 'Unknown')}",
            state,
            phase="skeleton",
            data={"skill_name": skeleton.get("skillName"), "total_tracks": len(track_plan)}
        )

    if current_track_idx >= len(track_plan):
        logger.error(f"❌ current_track_index ({current_track_idx}) 超出范围")
        return {
            "current_track_batch_plan": [],
            "current_batch_index": 0,
            "accumulated_track_actions": [],
            "batch_retry_count": 0,
            "batch_context": {},
            "messages": [AIMessage(content="❌ Track索引错误")]
        }

    current_track = track_plan[current_track_idx]
    track_name = current_track.get("trackName", "Unknown Track")
    purpose = current_track.get("purpose", "")
    estimated_actions = current_track.get("estimatedActions", 5)
    total_duration = skeleton.get("totalDuration", 150)

    logger.info(
        f"📋 规划 Track [{current_track_idx + 1}/{len(track_plan)}]: {track_name} "
        f"({estimated_actions} actions)"
    )

    # 发送Track开始事件
    _emit_progress(
        ProgressEventType.TRACK_STARTED,
        f"开始生成 Track: {track_name}",
        state,
        phase="track",
        data={"track_name": track_name, "purpose": purpose[:50], "estimated_actions": estimated_actions}
    )

    # 使用语义批次规划（替代原有的纯数量驱动）
    batch_plan, batch_context = calculate_semantic_batch_plan(
        track_name=track_name,
        estimated_actions=estimated_actions,
        total_duration=total_duration,
        purpose=purpose
    )

    # 发送批次规划完成事件
    _emit_progress(
        ProgressEventType.BATCH_PLANNING,
        f"批次规划完成: {len(batch_plan)} 个批次",
        state,
        data={"batch_count": len(batch_plan)}
    )

    # 准备消息
    messages = []
    batch_summary = "\n".join([
        f"  批次 {b['batch_index'] + 1}: {b['action_count']} actions "
        f"(帧 {b['start_frame_hint']}-{b['end_frame_hint']}) - {b.get('context', '')[:30]}"
        for b in batch_plan
    ])

    # 添加语义信息到消息
    suggested_types = batch_context.get("suggested_types", [])
    type_info = f"\n建议Action类型: {', '.join(suggested_types[:4])}" if suggested_types else ""

    messages.append(AIMessage(
        content=f"📋 **Track语义批次规划完成**: {track_name}\n"
                f"设计意图: {purpose[:50]}...\n"
                f"共 {len(batch_plan)} 个批次:\n{batch_summary}{type_info}"
    ))

    return {
        "current_track_batch_plan": batch_plan,
        "current_batch_index": 0,
        "accumulated_track_actions": [],
        "batch_retry_count": 0,
        "batch_context": batch_context,
        "messages": messages
    }


# ==================== 阶段3: 批次Action生成节点 ====================

def format_previous_actions_summary(actions: List[Dict[str, Any]]) -> str:
    """
    格式化已生成actions的摘要（仅包含关键信息，避免prompt膨胀）

    Args:
        actions: 已生成的actions列表

    Returns:
        摘要文本
    """
    if not actions:
        return "无（这是第一个批次）"

    summary_items = []
    for action in actions[-10:]:  # 只显示最近10个
        frame = action.get("frame", 0)
        duration = action.get("duration", 0)
        params = action.get("parameters", {})
        action_type = params.get("_odin_type", "Unknown").split(".")[-1].replace(", Assembly-CSharp", "")

        summary_items.append(
            f"  - 帧{frame}-{frame+duration}: {action_type}"
        )

    return "\n".join(summary_items)


def batch_action_generator_node(state: ActionBatchProgressiveState) -> Dict[str, Any]:
    """
    批次Action生成节点（增强版：使用语义上下文 + 流式输出）

    职责:
    1. 提取当前批次的约束条件（帧范围、action数量、语义上下文）
    2. 使用BatchContextState传递设计意图和约束
    3. 构建语义增强的prompt:
       - 技能骨架信息
       - Track信息和设计意图
       - 结构化的已生成actions摘要
       - 语义约束和建议
       - RAG检索的Action schemas
    4. 调用LLM生成actions
    5. 使用structured output确保格式
    6. 发送进度事件

    输出:
    - current_batch_actions: 当前批次生成的actions列表
    """
    from ..prompts.prompt_manager import get_prompt_manager
    from .json_utils import extract_json_from_markdown
    from .progressive_skill_nodes import (
        search_actions_by_track_type,
        infer_track_type,
        format_action_schemas_for_prompt,
    )

    skeleton = state["skill_skeleton"]
    track_plan = state["track_plan"]
    current_track_idx = state["current_track_index"]
    batch_plan = state["current_track_batch_plan"]
    current_batch_idx = state["current_batch_index"]
    accumulated_actions = state.get("accumulated_track_actions", [])
    # 获取语义上下文（新增）
    batch_context_state = state.get("batch_context", {})

    if current_batch_idx >= len(batch_plan):
        logger.error(f"❌ current_batch_index ({current_batch_idx}) 超出范围")
        return {
            "current_batch_actions": [],
            "messages": [AIMessage(content="❌ 批次索引错误")]
        }

    current_track = track_plan[current_track_idx]
    current_batch = batch_plan[current_batch_idx]

    track_name = current_track.get("trackName", "Unknown Track")
    purpose = current_track.get("purpose", "")
    batch_action_count = current_batch["action_count"]
    start_frame_hint = current_batch["start_frame_hint"]
    end_frame_hint = current_batch["end_frame_hint"]
    batch_context_desc = current_batch["context"]

    # 获取当前阶段信息
    current_phase = batch_context_state.get("phase", "main")
    phase_names = {"setup": "起手阶段", "main": "主体阶段", "cleanup": "收尾阶段"}

    logger.info(
        f"🎯 生成批次 [{current_batch_idx + 1}/{len(batch_plan)}] ({phase_names.get(current_phase, current_phase)}): "
        f"{track_name}, {batch_action_count} actions, 帧 {start_frame_hint}-{end_frame_hint}"
    )

    # 发送批次开始事件
    _emit_progress(
        ProgressEventType.BATCH_STARTED,
        f"生成批次 {current_batch_idx + 1}/{len(batch_plan)}: {batch_context_desc[:30]}",
        state,
        phase="batch",
        data={
            "batch_action_count": batch_action_count,
            "frame_range": f"{start_frame_hint}-{end_frame_hint}",
            "phase": current_phase
        }
    )

    # 准备消息
    messages = []
    messages.append(AIMessage(
        content=f"🎯 **批次 [{current_batch_idx + 1}/{len(batch_plan)}]** ({phase_names.get(current_phase, current_phase)})\n"
                f"目标: {batch_context_desc}\n"
                f"生成 {batch_action_count} 个actions（帧 {start_frame_hint}-{end_frame_hint}）"
    ))

    # 发送RAG检索事件
    _emit_progress(
        ProgressEventType.RAG_SEARCHING,
        f"检索相关Action定义...",
        state
    )

    # RAG检索相关Actions（增强版：结合语义上下文精准检索）
    track_type = infer_track_type(track_name)
    suggested_types = batch_context_state.get("suggested_types", [])
    used_types = batch_context_state.get("used_action_types", [])

    relevant_actions = search_actions_by_track_type(
        track_type=track_type,
        purpose=purpose,
        top_k=6,
        suggested_types=suggested_types,
        used_types=used_types,
        batch_context=batch_context_desc
    )

    # 发送RAG检索完成事件
    _emit_progress(
        ProgressEventType.RAG_COMPLETED,
        f"检索到 {len(relevant_actions)} 个相关Action定义",
        state,
        data={"action_count": len(relevant_actions)}
    )

    # RAG 检索容错：无结果时使用默认模板（与 progressive_skill_nodes 保持一致）
    if not relevant_actions:
        from .progressive_skill_nodes import get_default_actions_for_track_type
        logger.warning(f"⚠️ RAG 检索无结果，使用 {track_type} 类型默认模板")
        relevant_actions = get_default_actions_for_track_type(track_type)
        messages.append(AIMessage(
            content=f"⚠️ 未检索到相关 Action，使用 {track_type} 类型默认模板生成"
        ))
    else:
        messages.append(AIMessage(
            content=f"📋 检索到 {len(relevant_actions)} 个相关Action定义"
        ))

    # 格式化prompt输入（使用增强的上下文格式化）
    action_schemas_text = format_action_schemas_for_prompt(relevant_actions)

    # 使用新的上下文格式化函数（替代原有的简单摘要）
    if batch_context_state:
        context_text = format_context_for_prompt(batch_context_state)
    else:
        # 回退到旧的摘要方式
        context_text = format_previous_actions_summary(accumulated_actions)

    # 获取Prompt
    prompt_mgr = get_prompt_manager()
    prompt = prompt_mgr.get_prompt("batch_action_generation")

    # 发送LLM调用事件
    _emit_progress(
        ProgressEventType.LLM_CALLING,
        f"调用LLM生成Actions...",
        state
    )

    llm_start_time = time.time()
    logger.info(f"⏳ 开始调用 DeepSeek API（LangChain streaming）(batch {current_batch_idx + 1}/{len(batch_plan)})...")

    try:
        # 🔥 使用 LangChain LLM（streaming=True）
        # LangGraph Studio 通过 stream_mode="messages" 自动捕获 token 流
        llm = get_llm(streaming=True)
        
        # 创建 chain
        chain = prompt | llm
        
        # 调用 LLM（LangGraph 会自动追踪这个调用并流式输出 token）
        response = chain.invoke({
            "skill_name": skeleton.get("skillName", "Unknown"),
            "total_duration": skeleton.get("totalDuration", 150),
            "track_name": track_name,
            "track_purpose": purpose,
            "batch_action_count": batch_action_count,
            "start_frame_hint": start_frame_hint,
            "end_frame_hint": end_frame_hint,
            "batch_context": batch_context_desc,
            "current_batch_index": current_batch_idx,
            "previous_actions_summary": context_text,
            "relevant_actions": action_schemas_text or "无特定Action参考"
        })

        llm_elapsed = time.time() - llm_start_time
        logger.info(f"⏱️ DeepSeek API 响应耗时: {llm_elapsed:.2f}s")

        # 提取响应内容
        full_content = _prepare_payload_text(response)
        logger.info(f"📝 LLM 响应长度: {len(full_content)} 字符")

        # 解析 JSON 响应
        json_content = extract_json_from_markdown(full_content)
        batch_dict = json.loads(json_content)

        # 使用 Pydantic 验证
        validated = ActionBatch.model_validate(batch_dict)
        batch_actions = [action.model_dump() for action in validated.actions]
        logger.info(f"✅ 批次生成成功（流式）: {len(batch_actions)} actions")

        # 发送LLM完成事件
        _emit_progress(
            ProgressEventType.LLM_COMPLETED,
            f"生成 {len(batch_actions)} 个Actions",
            state,
            data={"action_count": len(batch_actions)}
        )

        messages.append(AIMessage(
            content=f"✅ 批次生成完成: {len(batch_actions)} 个actions"
        ))

        return {
            "current_batch_actions": batch_actions,
            "messages": messages
        }

    except ValidationError as e:
        logger.error(f"❌ 批次Schema验证失败: {e}")
        if full_content:
            logger.error(f"原始LLM输出: {full_content[:500]}...")

        error_details = "\n".join([f"• {err['loc']}: {err['msg']}" for err in e.errors()])
        messages.append(AIMessage(
            content=f"❌ 批次生成失败（格式错误）:\n{error_details}\n"
                    f"提示: 每个action必须包含frame, duration, enabled, parameters四个字段"
        ))

        # 发送错误事件
        _emit_progress(
            ProgressEventType.BATCH_FAILED,
            f"批次生成失败: Schema验证错误",
            state,
            data={"error": str(e)[:100]}
        )

        # 返回空列表触发修复流程
        return {
            "current_batch_actions": [],
            "current_batch_errors": [f"Schema验证失败: {error_details}"],
            "messages": messages
        }

    except Exception as e:
        logger.error(f"❌ 批次生成异常: {e}", exc_info=True)
        messages.append(AIMessage(content=f"❌ 批次生成失败: {str(e)}"))

        # 发送错误事件
        _emit_progress(
            ProgressEventType.BATCH_FAILED,
            f"批次生成失败: {str(e)[:50]}",
            state,
            data={"error": str(e)[:100]}
        )

        return {
            "current_batch_actions": [],
            "current_batch_errors": [f"生成异常: {str(e)}"],
            "messages": messages
        }


# ==================== 阶段3: 批次验证和修复节点 ====================

def validate_batch_actions(
    batch_actions: List[Dict[str, Any]],
    batch_plan_item: Dict[str, Any],
    total_duration: int
) -> List[str]:
    """
    验证批次actions的合法性

    验证规则:
    1. actions数量在合理范围内
    2. 每个action的frame在建议范围内（宽松检查）
    3. frame + duration <= total_duration
    4. parameters包含_odin_type

    Args:
        batch_actions: 批次actions列表
        batch_plan_item: 批次计划项
        total_duration: 技能总时长

    Returns:
        错误列表
    """
    errors = []

    if not batch_actions:
        errors.append("批次actions为空")
        return errors

    expected_count = batch_plan_item["action_count"]
    actual_count = len(batch_actions)

    # 宽松检查数量（允许±2个）
    if abs(actual_count - expected_count) > 2:
        errors.append(
            f"批次action数量异常: 期望{expected_count}个, 实际{actual_count}个"
        )

    start_hint = batch_plan_item["start_frame_hint"]
    end_hint = batch_plan_item["end_frame_hint"]

    for idx, action in enumerate(batch_actions):
        frame = action.get("frame")
        duration = action.get("duration")

        if not isinstance(frame, int) or frame < 0:
            errors.append(f"action[{idx}].frame 无效: {frame}")
            continue

        if not isinstance(duration, int) or duration < 1:
            errors.append(f"action[{idx}].duration 无效: {duration}")
            continue

        # 检查是否超出技能总时长
        if frame + duration > total_duration:
            errors.append(
                f"action[{idx}] 结束帧({frame + duration}) 超出总时长({total_duration})"
            )

        # 宽松检查帧范围（允许±30帧的偏差）
        if frame < start_hint - 30 or frame > end_hint + 30:
            logger.warning(
                f"⚠️ action[{idx}].frame({frame}) 不在建议范围({start_hint}-{end_hint}), 但可接受"
            )

        # 检查parameters
        parameters = action.get("parameters")
        if not parameters or not isinstance(parameters, dict):
            errors.append(f"action[{idx}].parameters 缺失")
        elif "_odin_type" not in parameters:
            errors.append(f"action[{idx}].parameters 缺少 _odin_type")

    return errors


def batch_action_validator_node(state: ActionBatchProgressiveState) -> Dict[str, Any]:
    """
    批次Action验证节点（增强版：支持参数深度验证 + 流式输出）

    职责:
    1. 验证当前批次actions的基础合法性（frame/duration/parameters）
    2. 对照RAG检索的Action Schema进行参数深度验证（类型/枚举/范围）
    3. 发送验证进度事件

    输出:
    - current_batch_errors: 错误列表
    """
    batch_actions = state.get("current_batch_actions", [])
    batch_plan = state["current_track_batch_plan"]
    current_batch_idx = state["current_batch_index"]
    total_duration = state["skill_skeleton"].get("totalDuration", 150)
    track_plan = state.get("track_plan", [])
    current_track_idx = state.get("current_track_index", 0)

    current_batch_plan = batch_plan[current_batch_idx]

    logger.info("🔍 验证批次actions（含参数深度验证）...")

    # 发送验证开始事件
    _emit_progress(
        ProgressEventType.BATCH_VALIDATING,
        f"验证批次 {current_batch_idx + 1}/{len(batch_plan)}...",
        state
    )

    # 基础结构验证
    errors = validate_batch_actions(
        batch_actions=batch_actions,
        batch_plan_item=current_batch_plan,
        total_duration=total_duration
    )

    # 参数深度验证（获取相关Action Schema）- 仅在模块可用时执行
    warnings = []
    if batch_actions and not errors and HAS_DEEP_VALIDATOR:
        # 获取当前Track的purpose用于检索
        track_purpose = ""
        if current_track_idx < len(track_plan):
            track_purpose = track_plan[current_track_idx].get("purpose", "")

        # 检索相关Action Schema
        relevant_schemas = _get_relevant_action_schemas_for_validation(
            batch_actions, track_purpose
        )

        if relevant_schemas and validate_batch_actions_deep is not None:
            # 执行参数深度验证
            deep_errors, deep_warnings = validate_batch_actions_deep(
                batch_actions=batch_actions,
                relevant_action_schemas=relevant_schemas,
                total_duration=total_duration
            )
            errors.extend(deep_errors)
            warnings.extend(deep_warnings)
            logger.info(f"📋 参数深度验证完成: {len(deep_errors)} 错误, {len(deep_warnings)} 警告")
    elif not HAS_DEEP_VALIDATOR:
        logger.debug("⚠️ 参数深度验证模块不可用，跳过深度验证")

    messages = []
    if errors:
        logger.warning(f"⚠️ 批次验证发现 {len(errors)} 个错误")
        errors_list = "\n".join([f"• {err}" for err in errors[:10]])  # 限制显示前10个
        messages.append(AIMessage(
            content=f"⚠️ 批次验证失败 ({len(errors)} 个错误):\n{errors_list}"
        ))
    else:
        logger.info("✅ 批次验证通过")
        msg = "✅ 批次验证通过"
        if warnings:
            msg += f"\n⚠️ {len(warnings)} 个警告:\n" + "\n".join([f"• {w}" for w in warnings[:5]])
        messages.append(AIMessage(content=msg))

    return {
        "current_batch_errors": errors,
        "messages": messages
    }


# RAG检索结果缓存（使用lru_cache需要hashable参数，所以封装一层）
_action_schema_cache: Dict[str, List[Dict[str, Any]]] = {}


def _cached_search_actions(type_name: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    带缓存的Action Schema检索

    Args:
        type_name: Action类型名
        top_k: 返回数量

    Returns:
        检索结果列表
    """
    cache_key = f"{type_name}:{top_k}"

    if cache_key in _action_schema_cache:
        return _action_schema_cache[cache_key]

    from ..tools.rag_tools import search_actions

    try:
        results = search_actions.invoke({"query": type_name, "top_k": top_k})
        if isinstance(results, list):
            _action_schema_cache[cache_key] = results
            return results
    except Exception as e:
        logger.warning(f"⚠️ 检索Action Schema失败 ({type_name}): {e}")

    return []


def clear_action_schema_cache():
    """清除Action Schema缓存（在新任务开始时调用）"""
    global _action_schema_cache
    _action_schema_cache = {}
    logger.debug("已清除Action Schema缓存")


def _get_relevant_action_schemas_for_validation(
    batch_actions: List[Dict[str, Any]],
    track_purpose: str
) -> List[Dict[str, Any]]:
    """
    获取批次中actions对应的Schema定义（带缓存）

    Args:
        batch_actions: 批次actions列表
        track_purpose: Track用途（用于检索）

    Returns:
        Action Schema列表
    """
    schemas = []

    # 收集所有action类型
    action_types = set()
    for action in batch_actions:
        params = action.get("parameters", {})
        odin_type = params.get("_odin_type", "")
        if odin_type:
            # 提取类型名
            type_name = extract_action_type_name(odin_type)
            if type_name:
                action_types.add(type_name)

    # 为每种类型检索Schema（使用缓存）
    for type_name in action_types:
        results = _cached_search_actions(type_name, top_k=3)
        for result in results:
            # 检查是否匹配
            result_type = result.get("typeName", "")
            if result_type == type_name or type_name in result_type:
                schemas.append(result)
                break

    return schemas


def batch_action_fixer_node(state: ActionBatchProgressiveState) -> Dict[str, Any]:
    """
    批次Action修复节点（增强版：流式输出）

    职责: 根据验证错误修复批次actions

    输出:
    - current_batch_actions: 修复后的actions
    - batch_retry_count: +1
    """
    from ..prompts.prompt_manager import get_prompt_manager
    from .json_utils import extract_json_from_markdown

    batch_actions = state["current_batch_actions"]
    errors = state["current_batch_errors"]
    batch_plan = state["current_track_batch_plan"]
    current_batch_idx = state["current_batch_index"]
    total_duration = state["skill_skeleton"].get("totalDuration", 150)

    current_batch_plan = batch_plan[current_batch_idx]

    logger.info(f"🔧 修复批次actions, 错误数: {len(errors)}")

    # 发送修复开始事件
    _emit_progress(
        ProgressEventType.BATCH_FIXING,
        f"修复批次 {current_batch_idx + 1}/{len(batch_plan)} ({len(errors)} 个错误)",
        state,
        data={"error_count": len(errors)}
    )

    # 格式化错误
    errors_text = "\n".join([f"{i+1}. {err}" for i, err in enumerate(errors)])

    messages = []
    messages.append(AIMessage(
        content=f"🔧 发现 {len(errors)} 个错误,正在修复..."
    ))

    # 获取Prompt
    prompt_mgr = get_prompt_manager()
    prompt = prompt_mgr.get_prompt("batch_action_fix")

    llm = get_llm(temperature=0.3)

    try:
        fixer_llm = llm.with_structured_output(
            ActionBatch,
            method="json_mode",
            include_raw=False
        )
    except:
        fixer_llm = llm

    chain = prompt | fixer_llm

    try:
        response = chain.invoke({
            "errors": errors_text,
            "batch_actions_json": json.dumps(batch_actions, ensure_ascii=False, indent=2),
            "batch_index": current_batch_idx,  # 添加批次索引参数
            "total_duration": total_duration,
            "start_frame_hint": current_batch_plan["start_frame_hint"],
            "end_frame_hint": current_batch_plan["end_frame_hint"]
        })

        if isinstance(response, ActionBatch):
            fixed_actions = [action.model_dump() for action in response.actions]
        else:
            payload_text = _prepare_payload_text(response)
            json_content = extract_json_from_markdown(payload_text)
            batch_dict = json.loads(json_content)
            validated = ActionBatch.model_validate(batch_dict)
            fixed_actions = [action.model_dump() for action in validated.actions]

        logger.info("✅ 批次修复成功")
        messages.append(AIMessage(content="✅ 批次已修复,重新验证..."))

        return {
            "current_batch_actions": fixed_actions,
            "batch_retry_count": state.get("batch_retry_count", 0) + 1,
            "messages": messages
        }

    except Exception as e:
        logger.error(f"❌ 批次修复失败: {e}", exc_info=True)
        messages.append(AIMessage(content=f"❌ 批次修复失败: {str(e)}"))

        return {
            "batch_retry_count": state.get("batch_retry_count", 0) + 1,
            "messages": messages
        }


def batch_action_saver_node(state: ActionBatchProgressiveState) -> Dict[str, Any]:
    """
    批次Action保存节点（增强版：更新语义上下文 + 流式输出）

    职责:
    1. 保存验证通过的批次actions
    2. 更新BatchContextState（已生成摘要、已用类型、占用帧区间）
    3. 执行语义验证并记录警告
    4. 移动到下一批次
    5. 发送进度事件

    输出:
    - accumulated_track_actions: 追加当前批次actions
    - current_batch_index: +1
    - batch_retry_count: 重置为0
    - batch_context: 更新后的上下文
    """
    batch_actions = state.get("current_batch_actions", [])
    accumulated = list(state.get("accumulated_track_actions", []))
    current_batch_idx = state.get("current_batch_index", 0)
    batch_plan = state["current_track_batch_plan"]
    batch_context = state.get("batch_context", {})

    # 处理空批次（跳过场景）
    if not batch_actions:
        logger.warning(f"⚠️ 批次 [{current_batch_idx + 1}/{len(batch_plan)}] 为空，跳过保存")
        return {
            "accumulated_track_actions": accumulated,  # 保持不变
            "current_batch_index": current_batch_idx + 1,
            "batch_retry_count": 0,
            "batch_context": batch_context,  # 不更新上下文
            "messages": [AIMessage(
                content=f"⚠️ 批次 [{current_batch_idx + 1}/{len(batch_plan)}] 跳过（生成失败或为空）"
            )]
        }

    logger.info(f"💾 保存批次 [{current_batch_idx + 1}/{len(batch_plan)}]: {len(batch_actions)} actions")

    # 追加到累积列表
    accumulated.extend(batch_actions)

    messages = []
    progress = f"[{current_batch_idx + 1}/{len(batch_plan)}]"

    # 获取当前Track类型（用于语义验证）
    track_plan_list = state.get("track_plan", [])
    current_track_idx = state.get("current_track_index", 0)
    track_type = None
    if current_track_idx < len(track_plan_list):
        track_name = track_plan_list[current_track_idx].get("trackName", "")
        from .progressive_skill_nodes import infer_track_type
        track_type = infer_track_type(track_name)

    # 执行语义验证（增强版：添加track_type参数）
    if batch_context:
        violations = validate_semantic_rules(batch_actions, batch_context, track_type=track_type)
        if violations:
            logger.warning(f"⚠️ 语义验证发现 {len(violations)} 个问题")
            violations_text = "\n".join([f"  • {v}" for v in violations[:3]])
            messages.append(AIMessage(
                content=f"⚠️ 语义验证提示:\n{violations_text}"
            ))
            # 将violations添加到上下文的avoid_patterns
            avoid = list(batch_context.get("avoid_patterns", []))
            for v in violations:
                if "[警告]" in v or "[建议]" in v:
                    avoid.append(v.split("]", 1)[1].strip()[:50])
            batch_context["avoid_patterns"] = avoid[-5:]  # 只保留最近5个

    # 更新上下文（新增）
    next_batch_idx = current_batch_idx + 1
    if batch_context:
        updated_context = update_context_after_batch(
            context=batch_context,
            batch_actions=batch_actions,
            batch_plan=batch_plan,
            next_batch_idx=next_batch_idx
        )
    else:
        updated_context = {}

    # 生成保存消息
    action_types = []
    for action in batch_actions:
        t = extract_action_type_name(action.get("parameters", {}).get("_odin_type", ""))
        if t and t not in action_types:
            action_types.append(t)

    type_info = f" ({', '.join(action_types[:3])})" if action_types else ""

    # 发送批次完成事件
    _emit_progress(
        ProgressEventType.BATCH_COMPLETED,
        f"批次 {progress} 已保存: {len(batch_actions)} actions{type_info}",
        state,
        data={
            "action_count": len(batch_actions),
            "action_types": action_types[:3],
            "accumulated_total": len(accumulated)
        }
    )

    messages.append(AIMessage(
        content=f"💾 批次 {progress} 已保存 ({len(batch_actions)} actions{type_info})"
    ))

    return {
        "accumulated_track_actions": accumulated,
        "current_batch_index": next_batch_idx,
        "batch_retry_count": 0,
        "batch_context": updated_context,
        "messages": messages
    }


# ==================== 阶段4: Track组装节点 ====================

def track_assembler_node_batch(state: ActionBatchProgressiveState) -> Dict[str, Any]:
    """
    Track组装节点（批次级版本 + 流式输出）

    职责:
    1. 将accumulated_track_actions组装为完整Track
    2. 验证Track整体的时间轴连贯性
    3. 添加到generated_tracks
    4. 发送进度事件

    输出:
    - generated_tracks: 追加当前Track
    - current_track_index: +1
    - accumulated_track_actions: 清空
    """
    from .progressive_skill_nodes import validate_track

    skeleton = state["skill_skeleton"]
    track_plan = state["track_plan"]
    current_track_idx = state["current_track_index"]
    accumulated_actions = state.get("accumulated_track_actions", [])
    generated_tracks = list(state.get("generated_tracks", []))

    current_track = track_plan[current_track_idx]
    track_name = current_track.get("trackName", "Unknown Track")
    total_duration = skeleton.get("totalDuration", 150)

    logger.info(
        f"🔧 组装 Track '{track_name}': {len(accumulated_actions)} actions"
    )

    # 发送Track组装事件
    _emit_progress(
        ProgressEventType.ASSEMBLING_TRACK,
        f"组装 Track: {track_name}",
        state,
        data={"track_name": track_name, "action_count": len(accumulated_actions)}
    )

    # 组装Track
    track_data = {
        "trackName": track_name,
        "enabled": True,
        "actions": accumulated_actions
    }

    # 验证Track整体
    errors = validate_track(track_data, total_duration)

    messages = []
    if errors:
        logger.warning(f"⚠️ Track组装后验证发现 {len(errors)} 个问题")
        errors_list = "\n".join([f"• {err}" for err in errors])
        messages.append(AIMessage(
            content=f"⚠️ Track组装验证发现问题:\n{errors_list}\n继续保存..."
        ))

    # 保存Track
    generated_tracks.append(track_data)

    progress = f"[{len(generated_tracks)}/{len(track_plan)}]"

    # 发送Track完成事件
    _emit_progress(
        ProgressEventType.TRACK_COMPLETED,
        f"Track '{track_name}' 组装完成 {progress}",
        state,
        data={
            "track_name": track_name,
            "action_count": len(accumulated_actions),
            "completed_tracks": len(generated_tracks),
            "total_tracks": len(track_plan)
        }
    )

    messages.append(AIMessage(
        content=f"✅ Track '{track_name}' 组装完成 {progress}"
    ))

    return {
        "generated_tracks": generated_tracks,
        "current_track_index": current_track_idx + 1,
        "accumulated_track_actions": [],  # 清空,准备下一个Track
        "messages": messages
    }


# ==================== 条件判断函数 ====================

def should_fix_batch(state: ActionBatchProgressiveState) -> Literal["save", "fix", "skip"]:
    """
    判断批次是否需要修复

    返回:
    - "save": 无错误 → 保存批次
    - "fix": 有错误且未达重试上限 → 修复批次
    - "skip": 有错误但达重试上限 → 跳过批次
    """
    errors = state.get("current_batch_errors", [])
    retry_count = state.get("batch_retry_count", 0)
    max_retries = state.get("max_batch_retries", 2)

    if not errors:
        return "save"

    if retry_count < max_retries:
        return "fix"
    else:
        logger.warning(f"批次达到重试上限({max_retries}),跳过")
        return "skip"


def should_continue_batches(state: ActionBatchProgressiveState) -> Literal["continue", "assemble_track"]:
    """
    判断是否继续生成下一批次

    返回:
    - "continue": 还有批次 → 生成下一批次
    - "assemble_track": 所有批次完成 → 组装Track
    """
    current_batch_idx = state.get("current_batch_index", 0)
    batch_plan = state.get("current_track_batch_plan", [])

    if current_batch_idx < len(batch_plan):
        return "continue"
    else:
        return "assemble_track"


def should_continue_tracks_batch(state: ActionBatchProgressiveState) -> Literal["continue", "assemble_skill"]:
    """
    判断是否继续生成下一个Track

    返回:
    - "continue": 还有Track → 规划下一Track的批次
    - "assemble_skill": 所有Track完成 → 组装技能
    """
    current_track_idx = state.get("current_track_index", 0)
    track_plan = state.get("track_plan", [])

    if current_track_idx < len(track_plan):
        return "continue"
    else:
        return "assemble_skill"

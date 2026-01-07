"""
单Action级渐进式技能生成节点实现
实现最细粒度的生成：骨架 -> Track计划 -> 单Action循环生成 -> Track组装 -> 技能组装

优势:
1. 每次LLM调用上下文最短，避免幻觉
2. 错误隔离最精细（单个Action失败不影响其他）
3. 生成质量最高（每次只专注一个Action）
"""

import json
import logging
import time
from typing import Any, Dict, List, TypedDict, Annotated, Optional, Literal, Tuple

from langchain_core.messages import AIMessage, AnyMessage
from langgraph.graph.message import add_messages
from langgraph.types import StreamWriter
from langgraph.config import get_stream_writer
from pydantic import ValidationError

from .skill_nodes import get_llm, _prepare_payload_text
from .json_utils import extract_json_from_markdown
from ..streaming import ProgressEventType, emit_progress
from ..schemas import (
    SkillAction,
    SingleActionOutput,
    SingleActionPlan,
)

# 复用已有的节点和函数
from .progressive_skill_nodes import (
    skeleton_generator_node,
    should_continue_to_track_generation,
    skill_assembler_node,
    finalize_progressive_node,
    should_finalize_or_fail,
    validate_track,
    infer_track_type,
    search_actions_by_track_type,
    format_action_schemas_for_prompt,
    _save_generated_json,
)
from .action_batch_skill_nodes import (
    extract_action_type_name,
    _get_writer_safe,
)

logger = logging.getLogger(__name__)


# ==================== 配置常量 ====================

MAX_CONTEXT_ACTIONS = 5  # 上下文中最多保留的已完成Action数量
DEFAULT_ACTION_DURATION = 30  # 默认Action持续帧数


# ==================== 默认Action模板（按Track类型） ====================
# 当RAG检索失败时使用，确保LLM有正确的Action类型参考

DEFAULT_ACTIONS_BY_TRACK_TYPE: Dict[str, List[Dict[str, Any]]] = {
    "animation": [
        {
            "action_name": "AnimationAction",
            "action_type": "SkillSystem.Actions.AnimationAction, Assembly-CSharp",
            "description": "播放角色动画（攻击、施法、受击等）",
            "parameters": [
                {"name": "animationClipName", "type": "string", "description": "动画片段名称"},
                {"name": "normalizedTime", "type": "float", "defaultValue": "0"},
                {"name": "crossFadeDuration", "type": "float", "defaultValue": "0.1"},
                {"name": "animationLayer", "type": "int", "defaultValue": "0"}
            ]
        }
    ],
    "effect": [
        {
            "action_name": "SpawnEffectAction",
            "action_type": "SkillSystem.Actions.SpawnEffectAction, Assembly-CSharp",
            "description": "生成特效（火焰、冰霜、闪电等视觉效果）",
            "parameters": [
                {"name": "effectPrefabPath", "type": "string", "description": "特效预制体路径"},
                {"name": "spawnPosition", "type": "Vector3", "defaultValue": "(0,0,0)"},
                {"name": "duration", "type": "float", "defaultValue": "1.0"}
            ]
        },
        {
            "action_name": "DamageAction",
            "action_type": "SkillSystem.Actions.DamageAction, Assembly-CSharp",
            "description": "造成伤害（物理、魔法、真实伤害）",
            "parameters": [
                {"name": "damageAmount", "type": "float", "description": "伤害数值"},
                {"name": "damageType", "type": "DamageType", "defaultValue": "Physical"},
                {"name": "radius", "type": "float", "defaultValue": "1.0"}
            ]
        },
        {
            "action_name": "ApplyBuffAction",
            "action_type": "SkillSystem.Actions.ApplyBuffAction, Assembly-CSharp",
            "description": "施加Buff/Debuff效果（减速、燃烧、冰冻等）",
            "parameters": [
                {"name": "buffId", "type": "string", "description": "Buff ID"},
                {"name": "duration", "type": "float", "description": "持续时间"},
                {"name": "stackCount", "type": "int", "defaultValue": "1"}
            ]
        }
    ],
    "audio": [
        {
            "action_name": "PlaySoundAction",
            "action_type": "SkillSystem.Actions.PlaySoundAction, Assembly-CSharp",
            "description": "播放音效（施法音效、命中音效、环境音效）",
            "parameters": [
                {"name": "soundClipPath", "type": "string", "description": "音效文件路径"},
                {"name": "volume", "type": "float", "defaultValue": "1.0"},
                {"name": "pitch", "type": "float", "defaultValue": "1.0"},
                {"name": "loop", "type": "bool", "defaultValue": "false"}
            ]
        }
    ],
    "movement": [
        {
            "action_name": "DashAction",
            "action_type": "SkillSystem.Actions.DashAction, Assembly-CSharp",
            "description": "角色冲刺/位移",
            "parameters": [
                {"name": "direction", "type": "Vector3", "defaultValue": "(0,0,1)"},
                {"name": "distance", "type": "float", "description": "位移距离"},
                {"name": "speed", "type": "float", "description": "移动速度"}
            ]
        }
    ],
    "camera": [
        {
            "action_name": "CameraShakeAction",
            "action_type": "SkillSystem.Actions.CameraShakeAction, Assembly-CSharp",
            "description": "镜头震动效果",
            "parameters": [
                {"name": "intensity", "type": "float", "defaultValue": "0.5"},
                {"name": "duration", "type": "float", "defaultValue": "0.3"}
            ]
        }
    ]
}


def get_default_actions_for_track(track_type: str) -> List[Dict[str, Any]]:
    """获取指定Track类型的默认Action模板"""
    return DEFAULT_ACTIONS_BY_TRACK_TYPE.get(track_type, DEFAULT_ACTIONS_BY_TRACK_TYPE.get("effect", []))


def validate_action_matches_track_type(action_data: Dict[str, Any], track_type: str) -> Tuple[bool, str]:
    """
    验证生成的Action类型是否与Track类型匹配
    
    Returns:
        (is_valid, error_message)
    """
    params = action_data.get("parameters", {})
    odin_type = params.get("_odin_type", "")
    action_type_name = extract_action_type_name(odin_type).lower()
    
    # Track类型与允许的Action类型映射
    allowed_actions = {
        "animation": ["animation", "playanimation", "animator"],
        "effect": ["effect", "spawn", "damage", "buff", "debuff", "heal", "shield", "projectile"],
        "audio": ["sound", "audio", "playsound", "playaudio"],
        "movement": ["move", "dash", "teleport", "knockback", "pull"],
        "camera": ["camera", "shake", "zoom", "focus"],
    }
    
    # 获取该Track类型允许的Action关键词
    allowed_keywords = allowed_actions.get(track_type, [])
    
    # 如果是other类型，允许所有Action
    if track_type == "other" or not allowed_keywords:
        return True, ""
    
    # 检查Action类型是否包含允许的关键词
    for keyword in allowed_keywords:
        if keyword in action_type_name:
            return True, ""
    
    return False, f"Action类型 '{action_type_name}' 与Track类型 '{track_type}' 不匹配，期望包含: {allowed_keywords}"


# ==================== State 定义 ====================

class SingleActionProgressiveState(TypedDict):
    """
    单Action级渐进式生成State
    """
    # === 输入 ===
    requirement: str
    similar_skills: List[Dict[str, Any]]

    # === 阶段1: 骨架生成（复用） ===
    skill_skeleton: Dict[str, Any]
    skeleton_validation_errors: List[str]
    skeleton_retry_count: int
    max_skeleton_retries: int
    track_plan: List[Dict[str, Any]]

    # === 阶段2: Track级状态 ===
    current_track_index: int
    current_track_action_plan: List[Dict[str, Any]]  # 当前Track的Action计划列表

    # === 阶段3: 单Action级状态 ===
    current_action_index: int  # 当前Action索引
    current_action_data: Dict[str, Any]  # 当前生成的Action
    current_action_errors: List[str]  # 当前Action验证错误
    action_retry_count: int  # 当前Action重试次数
    max_action_retries: int  # 单个Action最大重试次数（默认2）

    # === Track内累积 ===
    accumulated_track_actions: List[Dict[str, Any]]  # 当前Track已完成的Actions

    # === 阶段4: Track组装 ===
    generated_tracks: List[Dict[str, Any]]

    # === 阶段5: 技能组装（复用） ===
    assembled_skill: Dict[str, Any]
    final_validation_errors: List[str]

    # === 兼容字段 ===
    final_result: Dict[str, Any]
    is_valid: bool

    # === 通用 ===
    messages: Annotated[List[AnyMessage], add_messages]
    thread_id: str


# ==================== 进度事件辅助函数 ====================

def _emit_action_progress(
    event_type: ProgressEventType,
    message: str,
    state: Optional[Dict[str, Any]] = None,
    **kwargs
):
    """发送单Action级进度事件"""
    writer = _get_writer_safe()
    if writer is None:
        logger.debug(f"[{event_type.value}] {message}")
        return

    extra_data = {}
    if state:
        track_plan = state.get("track_plan", [])
        current_track_idx = state.get("current_track_index", 0)
        action_plan = state.get("current_track_action_plan", [])
        current_action_idx = state.get("current_action_index", 0)

        extra_data["track_index"] = current_track_idx
        extra_data["total_tracks"] = len(track_plan)
        extra_data["action_index"] = current_action_idx
        extra_data["total_actions"] = len(action_plan)

        # 计算进度: 骨架10% + tracks 80% + 组装10%
        if track_plan:
            skeleton_progress = 0.1
            total_tracks = len(track_plan)
            completed_tracks = current_track_idx

            # 当前track内的action进度
            if action_plan:
                current_track_action_progress = current_action_idx / len(action_plan)
            else:
                current_track_action_progress = 0

            track_progress = (completed_tracks + current_track_action_progress) / total_tracks
            track_progress *= 0.8

            extra_data["progress"] = skeleton_progress + track_progress

        if current_track_idx < len(track_plan):
            extra_data["track_name"] = track_plan[current_track_idx].get("trackName", "")

    extra_data.update(kwargs)
    emit_progress(writer, event_type, message, **extra_data)


# ==================== Action计划生成 ====================

def generate_action_plan_for_track(
    track_plan_item: Dict[str, Any],
    total_duration: int
) -> List[Dict[str, Any]]:
    """
    为Track生成单Action级别的计划

    根据Track的purpose和estimatedActions，生成每个Action的计划
    """
    track_name = track_plan_item.get("trackName", "Unknown Track")
    purpose = track_plan_item.get("purpose", "")
    estimated_actions = track_plan_item.get("estimatedActions", 3)

    # 解析purpose，尝试拆分为多个功能点
    action_purposes = _parse_purpose_to_action_purposes(purpose, estimated_actions)

    # 计算每个Action的建议帧位置
    frame_per_action = total_duration // max(1, len(action_purposes))

    action_plan = []
    for i, action_purpose in enumerate(action_purposes):
        frame_hint = i * frame_per_action
        duration_hint = min(DEFAULT_ACTION_DURATION, frame_per_action)

        action_plan.append({
            "action_index": i,
            "suggested_type": None,  # 由RAG检索决定
            "frame_hint": frame_hint,
            "duration_hint": duration_hint,
            "purpose": action_purpose,
        })

    logger.info(f"📋 为 Track '{track_name}' 生成 {len(action_plan)} 个Action计划")
    return action_plan


def _parse_purpose_to_action_purposes(purpose: str, estimated_count: int) -> List[str]:
    """
    将Track的purpose拆分为多个Action的purpose

    策略：
    1. 尝试按标点符号分割
    2. 如果分割结果不足，补充通用描述
    """
    import re

    # 按中英文标点分割
    segments = re.split(r'[,，、;；和]', purpose)
    segments = [s.strip() for s in segments if s.strip()]

    # 如果分割结果不足，补充
    if len(segments) < estimated_count:
        # 复制最后一个或添加通用描述
        while len(segments) < estimated_count:
            if segments:
                segments.append(f"{segments[-1]}（续）")
            else:
                segments.append(f"执行Track功能 #{len(segments)+1}")

    # 如果分割结果过多，截断
    if len(segments) > estimated_count:
        segments = segments[:estimated_count]

    return segments


# ==================== 上下文格式化 ====================

def format_completed_actions_for_context(
    actions: List[Dict[str, Any]],
    max_count: int = MAX_CONTEXT_ACTIONS
) -> str:
    """
    格式化已完成的Actions为简洁的上下文摘要

    只保留最近N个Action的关键信息，避免上下文过长
    """
    if not actions:
        return "无（这是第一个Action）"

    # 只取最近的N个
    recent_actions = actions[-max_count:]

    lines = []
    for i, action in enumerate(recent_actions):
        frame = action.get("frame", 0)
        duration = action.get("duration", 0)
        params = action.get("parameters", {})
        odin_type = params.get("_odin_type", "")
        action_type = extract_action_type_name(odin_type)

        lines.append(f"  {i+1}. 帧{frame}-{frame+duration}: {action_type}")

    if len(actions) > max_count:
        lines.insert(0, f"  （共{len(actions)}个，显示最近{max_count}个）")

    return "\n".join(lines)


# ==================== 阶段2: Track Action计划节点 ====================

def plan_track_actions_node(state: SingleActionProgressiveState) -> Dict[str, Any]:
    """
    Track Action计划节点

    职责：为当前Track生成单Action级别的计划
    """
    skeleton = state.get("skill_skeleton", {})
    track_plan = state.get("track_plan", [])
    current_track_idx = state.get("current_track_index", 0)

    if current_track_idx >= len(track_plan):
        logger.error(f"current_track_index ({current_track_idx}) out of range")
        return {
            "current_track_action_plan": [],
            "current_action_index": 0,
            "accumulated_track_actions": [],
            "action_retry_count": 0,
            "messages": [AIMessage(content="Track index error")]
        }

    current_track = track_plan[current_track_idx]
    track_name = current_track.get("trackName", "Unknown Track")
    total_duration = skeleton.get("totalDuration", 150)

    logger.info(f"Planning actions for Track [{current_track_idx + 1}/{len(track_plan)}]: {track_name}")

    # 发送进度事件
    _emit_action_progress(
        ProgressEventType.TRACK_STARTED,
        f"Planning Track: {track_name}",
        state,
        data={"track_name": track_name}
    )

    # 生成Action计划
    action_plan = generate_action_plan_for_track(current_track, total_duration)

    messages = []
    plan_summary = "\n".join([
        f"  {p['action_index']+1}. {p['purpose'][:30]}... (帧{p['frame_hint']})"
        for p in action_plan
    ])
    messages.append(AIMessage(
        content=f"Track '{track_name}' Action计划:\n{plan_summary}"
    ))

    return {
        "current_track_action_plan": action_plan,
        "current_action_index": 0,
        "accumulated_track_actions": [],
        "action_retry_count": 0,
        "messages": messages
    }


# ==================== 阶段3: 单Action生成节点 ====================

def single_action_generator_node(state: SingleActionProgressiveState, writer: StreamWriter) -> Dict[str, Any]:
    """
    单Action生成节点

    职责：生成当前计划中的单个Action
    """
    from ..prompts.prompt_manager import get_prompt_manager

    skeleton = state["skill_skeleton"]
    track_plan = state["track_plan"]
    current_track_idx = state["current_track_index"]
    action_plan = state["current_track_action_plan"]
    current_action_idx = state["current_action_index"]
    accumulated_actions = state.get("accumulated_track_actions", [])

    if current_action_idx >= len(action_plan):
        logger.error(f"current_action_index ({current_action_idx}) out of range")
        return {
            "current_action_data": {},
            "current_action_errors": ["Action index error"],
            "messages": [AIMessage(content="Action index error")]
        }

    current_track = track_plan[current_track_idx]
    current_action_plan = action_plan[current_action_idx]

    track_name = current_track.get("trackName", "Unknown Track")
    track_purpose = current_track.get("purpose", "")
    action_purpose = current_action_plan.get("purpose", "")
    frame_hint = current_action_plan.get("frame_hint", 0)
    duration_hint = current_action_plan.get("duration_hint", DEFAULT_ACTION_DURATION)

    logger.info(
        f"Generating Action [{current_action_idx + 1}/{len(action_plan)}] "
        f"for Track '{track_name}': {action_purpose[:30]}..."
    )

    # 发送进度事件
    _emit_action_progress(
        ProgressEventType.LLM_CALLING,
        f"Generating Action {current_action_idx + 1}/{len(action_plan)}",
        state,
        data={"action_purpose": action_purpose[:50]}
    )

    messages = []
    messages.append(AIMessage(
        content=f"Generating Action [{current_action_idx + 1}/{len(action_plan)}]: {action_purpose}"
    ))

    # RAG检索相关Actions
    track_type = infer_track_type(track_name)
    relevant_actions = search_actions_by_track_type(
        track_type=track_type,
        purpose=action_purpose,
        top_k=3
    )
    
    # 🔥 RAG检索容错：如果检索结果为空或不相关，使用默认模板
    if not relevant_actions:
        logger.warning(f"⚠️ RAG检索无结果，使用 {track_type} 类型默认Action模板")
        relevant_actions = get_default_actions_for_track(track_type)
        messages.append(AIMessage(
            content=f"⚠️ 未检索到相关Action，使用 {track_type} 类型默认模板"
        ))
    
    action_schemas_text = format_action_schemas_for_prompt(relevant_actions)
    
    # 🔥 增强：添加Track类型约束提示
    track_type_hint = f"\n\n🚨 重要约束：当前是 {track_type.upper()} Track，必须生成与该类型匹配的Action！"
    if track_type == "effect":
        track_type_hint += "\n- 应使用: SpawnEffectAction, DamageAction, ApplyBuffAction 等"
        track_type_hint += "\n- 禁止使用: AnimationAction, PlayAnimationAction（这些属于Animation Track）"
    elif track_type == "audio":
        track_type_hint += "\n- 应使用: PlaySoundAction, PlayAudioAction 等"
        track_type_hint += "\n- 禁止使用: AnimationAction, DamageAction（这些不属于Audio Track）"
    elif track_type == "animation":
        track_type_hint += "\n- 应使用: AnimationAction 等"
    
    action_schemas_text = (action_schemas_text or "") + track_type_hint

    # 格式化已完成Actions的上下文（精简版）
    completed_summary = format_completed_actions_for_context(accumulated_actions)

    # 获取Prompt
    prompt_mgr = get_prompt_manager()
    prompt = prompt_mgr.get_prompt("single_action_generation")

    llm_start_time = time.time()

    try:
        llm = get_llm(streaming=True)
        chain = prompt | llm

        response = chain.invoke({
            "skill_name": skeleton.get("skillName", "Unknown"),
            "total_duration": skeleton.get("totalDuration", 150),
            "track_name": track_name,
            "track_purpose": track_purpose,
            "action_index": current_action_idx + 1,
            "total_actions": len(action_plan),
            "action_purpose": action_purpose,
            "frame_hint": frame_hint,
            "duration_hint": duration_hint,
            "completed_actions_summary": completed_summary,
            "relevant_actions": action_schemas_text or "No specific Action reference"
        })

        llm_elapsed = time.time() - llm_start_time
        logger.info(f"LLM response time: {llm_elapsed:.2f}s")

        # 解析响应
        full_content = _prepare_payload_text(response)
        json_content = extract_json_from_markdown(full_content)
        result_dict = json.loads(json_content)

        # 验证输出格式
        validated = SingleActionOutput.model_validate(result_dict)
        action_data = validated.action.model_dump()

        logger.info(f"Action generated successfully: frame={action_data.get('frame')}")

        # 发送完成事件
        _emit_action_progress(
            ProgressEventType.LLM_COMPLETED,
            f"Action {current_action_idx + 1} generated",
            state
        )

        messages.append(AIMessage(
            content=f"Action generated: frame {action_data.get('frame')}-{action_data.get('frame', 0)+action_data.get('duration', 0)}"
        ))

        return {
            "current_action_data": action_data,
            "current_action_errors": [],
            "messages": messages
        }

    except ValidationError as e:
        logger.error(f"Action validation failed: {e}")
        error_msg = str(e)[:200]
        messages.append(AIMessage(content=f"Action validation failed: {error_msg}"))

        return {
            "current_action_data": {},
            "current_action_errors": [f"Validation error: {error_msg}"],
            "messages": messages
        }

    except Exception as e:
        logger.error(f"Action generation failed: {e}", exc_info=True)
        messages.append(AIMessage(content=f"Action generation failed: {str(e)}"))

        return {
            "current_action_data": {},
            "current_action_errors": [f"Generation error: {str(e)}"],
            "messages": messages
        }


# ==================== 单Action验证节点 ====================

def single_action_validator_node(state: SingleActionProgressiveState) -> Dict[str, Any]:
    """
    单Action验证节点

    验证当前生成的Action是否合法，包括：
    1. 基本字段验证（frame, duration, parameters）
    2. 🔥 Action类型与Track类型匹配验证
    """
    action_data = state.get("current_action_data", {})
    total_duration = state["skill_skeleton"].get("totalDuration", 150)
    
    # 🔥 获取当前Track信息用于类型匹配验证
    track_plan = state.get("track_plan", [])
    current_track_idx = state.get("current_track_index", 0)
    current_track = track_plan[current_track_idx] if current_track_idx < len(track_plan) else {}
    track_name = current_track.get("trackName", "Unknown Track")
    track_type = infer_track_type(track_name)

    logger.info(f"Validating action for {track_type} track...")

    errors = []

    if not action_data:
        errors.append("Action data is empty")
        return {"current_action_errors": errors, "messages": [AIMessage(content="Action is empty")]}

    # 验证frame
    frame = action_data.get("frame")
    if not isinstance(frame, int) or frame < 0:
        errors.append(f"Invalid frame: {frame}")

    # 验证duration
    duration = action_data.get("duration")
    if not isinstance(duration, int) or duration < 1:
        errors.append(f"Invalid duration: {duration}")

    # 验证时间范围
    if isinstance(frame, int) and isinstance(duration, int):
        if frame + duration > total_duration:
            errors.append(f"Action end frame ({frame + duration}) exceeds total duration ({total_duration})")

    # 验证parameters
    params = action_data.get("parameters")
    if not params or not isinstance(params, dict):
        errors.append("Missing parameters")
    elif "_odin_type" not in params:
        errors.append("Missing _odin_type in parameters")
    else:
        # 🔥 验证Action类型与Track类型是否匹配
        is_type_match, type_error = validate_action_matches_track_type(action_data, track_type)
        if not is_type_match:
            errors.append(type_error)
            logger.warning(f"⚠️ Action类型不匹配: {type_error}")

    messages = []
    if errors:
        logger.warning(f"Action validation found {len(errors)} errors")
        messages.append(AIMessage(content=f"Validation errors: {'; '.join(errors)}"))
    else:
        logger.info("Action validation passed")
        messages.append(AIMessage(content="Action validation passed"))

    return {"current_action_errors": errors, "messages": messages}


# ==================== 单Action修复节点 ====================

def single_action_fixer_node(state: SingleActionProgressiveState) -> Dict[str, Any]:
    """
    单Action修复节点
    
    增强：传递Track类型信息，帮助修复Action类型不匹配问题
    """
    from ..prompts.prompt_manager import get_prompt_manager

    action_data = state.get("current_action_data", {})
    errors = state.get("current_action_errors", [])
    action_plan = state["current_track_action_plan"]
    current_action_idx = state["current_action_index"]
    total_duration = state["skill_skeleton"].get("totalDuration", 150)
    
    # 🔥 获取Track类型信息
    track_plan = state.get("track_plan", [])
    current_track_idx = state.get("current_track_index", 0)
    current_track = track_plan[current_track_idx] if current_track_idx < len(track_plan) else {}
    track_name = current_track.get("trackName", "Unknown Track")
    track_type = infer_track_type(track_name)
    track_purpose = current_track.get("purpose", "")

    current_plan = action_plan[current_action_idx] if current_action_idx < len(action_plan) else {}
    frame_hint = current_plan.get("frame_hint", 0)
    action_purpose = current_plan.get("purpose", "")

    logger.info(f"Fixing action with {len(errors)} errors for {track_type} track")

    # 🔥 增强错误信息，包含Track类型约束
    errors_text = "\n".join([f"- {e}" for e in errors])
    errors_text += f"\n\n当前Track: {track_name} (类型: {track_type})"
    errors_text += f"\nTrack用途: {track_purpose}"
    errors_text += f"\nAction功能: {action_purpose}"
    
    # 添加正确的Action类型提示
    if track_type == "effect":
        errors_text += "\n\n🔥 正确的Action类型应为: SpawnEffectAction, DamageAction, ApplyBuffAction"
    elif track_type == "audio":
        errors_text += "\n\n🔥 正确的Action类型应为: PlaySoundAction, PlayAudioAction"
    elif track_type == "animation":
        errors_text += "\n\n🔥 正确的Action类型应为: AnimationAction"

    prompt_mgr = get_prompt_manager()
    prompt = prompt_mgr.get_prompt("single_action_fix")

    llm = get_llm(temperature=0.3)

    try:
        chain = prompt | llm
        response = chain.invoke({
            "errors": errors_text,
            "action_json": json.dumps(action_data, ensure_ascii=False, indent=2),
            "total_duration": total_duration,
            "frame_hint": frame_hint
        })

        full_content = _prepare_payload_text(response)
        json_content = extract_json_from_markdown(full_content)
        result_dict = json.loads(json_content)

        validated = SingleActionOutput.model_validate(result_dict)
        fixed_action = validated.action.model_dump()

        logger.info("Action fixed successfully")

        return {
            "current_action_data": fixed_action,
            "action_retry_count": state.get("action_retry_count", 0) + 1,
            "messages": [AIMessage(content="Action fixed, re-validating...")]
        }

    except Exception as e:
        logger.error(f"Action fix failed: {e}")
        return {
            "action_retry_count": state.get("action_retry_count", 0) + 1,
            "messages": [AIMessage(content=f"Fix failed: {str(e)}")]
        }


# ==================== 单Action保存节点 ====================

def single_action_saver_node(state: SingleActionProgressiveState) -> Dict[str, Any]:
    """
    单Action保存节点

    保存验证通过的Action，移动到下一个
    """
    action_data = state.get("current_action_data", {})
    accumulated = list(state.get("accumulated_track_actions", []))
    current_action_idx = state.get("current_action_index", 0)
    action_plan = state.get("current_track_action_plan", [])

    # 跳过空Action
    if not action_data:
        logger.warning(f"Skipping empty action [{current_action_idx + 1}/{len(action_plan)}]")
        return {
            "accumulated_track_actions": accumulated,
            "current_action_index": current_action_idx + 1,
            "action_retry_count": 0,
            "messages": [AIMessage(content=f"Skipped empty action {current_action_idx + 1}")]
        }

    # 保存Action
    accumulated.append(action_data)

    action_type = extract_action_type_name(action_data.get("parameters", {}).get("_odin_type", ""))
    progress = f"[{current_action_idx + 1}/{len(action_plan)}]"

    logger.info(f"Saved action {progress}: {action_type}")

    # 发送进度事件
    _emit_action_progress(
        ProgressEventType.BATCH_COMPLETED,  # 复用batch完成事件
        f"Action {progress} saved: {action_type}",
        state,
        data={"action_type": action_type, "total_saved": len(accumulated)}
    )

    return {
        "accumulated_track_actions": accumulated,
        "current_action_index": current_action_idx + 1,
        "action_retry_count": 0,
        "messages": [AIMessage(content=f"Saved action {progress}: {action_type}")]
    }


# ==================== Track组装节点 ====================

def track_assembler_node_single(state: SingleActionProgressiveState) -> Dict[str, Any]:
    """
    Track组装节点（单Action版本）

    将accumulated_track_actions组装为完整Track
    """
    skeleton = state["skill_skeleton"]
    track_plan = state["track_plan"]
    current_track_idx = state["current_track_index"]
    accumulated_actions = state.get("accumulated_track_actions", [])
    generated_tracks = list(state.get("generated_tracks", []))

    current_track = track_plan[current_track_idx]
    track_name = current_track.get("trackName", "Unknown Track")
    total_duration = skeleton.get("totalDuration", 150)

    logger.info(f"Assembling Track '{track_name}': {len(accumulated_actions)} actions")

    # 组装Track
    track_data = {
        "trackName": track_name,
        "enabled": True,
        "actions": accumulated_actions
    }

    # 验证Track
    errors = validate_track(track_data, total_duration)
    if errors:
        logger.warning(f"Track validation found {len(errors)} issues")

    generated_tracks.append(track_data)
    progress = f"[{len(generated_tracks)}/{len(track_plan)}]"

    # 发送进度事件
    _emit_action_progress(
        ProgressEventType.TRACK_COMPLETED,
        f"Track '{track_name}' assembled {progress}",
        state,
        data={"track_name": track_name, "action_count": len(accumulated_actions)}
    )

    return {
        "generated_tracks": generated_tracks,
        "current_track_index": current_track_idx + 1,
        "accumulated_track_actions": [],
        "messages": [AIMessage(content=f"Track '{track_name}' assembled {progress}")]
    }


# ==================== 条件判断函数 ====================

def should_fix_action(state: SingleActionProgressiveState) -> Literal["save", "fix", "skip"]:
    """判断Action是否需要修复"""
    errors = state.get("current_action_errors", [])
    retry_count = state.get("action_retry_count", 0)
    max_retries = state.get("max_action_retries", 2)

    if not errors:
        return "save"
    if retry_count < max_retries:
        return "fix"
    return "skip"


def should_continue_actions(state: SingleActionProgressiveState) -> Literal["continue", "assemble_track"]:
    """判断是否继续生成下一个Action"""
    current_action_idx = state.get("current_action_index", 0)
    action_plan = state.get("current_track_action_plan", [])

    if current_action_idx < len(action_plan):
        return "continue"
    return "assemble_track"


def should_continue_tracks_single(state: SingleActionProgressiveState) -> Literal["continue", "assemble_skill"]:
    """判断是否继续生成下一个Track"""
    current_track_idx = state.get("current_track_index", 0)
    track_plan = state.get("track_plan", [])

    if current_track_idx < len(track_plan):
        return "continue"
    return "assemble_skill"

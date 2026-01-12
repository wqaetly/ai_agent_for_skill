"""
批次上下文管理模块
"""

from typing import Any, Dict, List, Optional, Tuple

from ...schemas import BatchContextState, BatchPhase
from ..constants import SEMANTIC_KEYWORD_MAP


def extract_key_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """提取 Action 参数中的关键参数（用于摘要）"""
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
        elif isinstance(value, (int, float)) and value != 0:
            result[key] = value

    return dict(list(result.items())[:5])


def merge_frame_intervals(intervals: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """合并重叠的帧区间"""
    if not intervals:
        return []

    sorted_intervals = sorted(intervals, key=lambda x: x[0])
    merged = [sorted_intervals[0]]
    
    for start, end in sorted_intervals[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))

    return merged


def parse_purpose_to_action_types(purpose: str) -> List[str]:
    """从 purpose 文本解析建议的 Action 类型"""
    suggested = []
    purpose_lower = purpose.lower()

    for keyword, action_types in SEMANTIC_KEYWORD_MAP.items():
        if keyword in purpose_lower:
            for action_type in action_types:
                if action_type not in suggested:
                    suggested.append(action_type)

    return suggested


def create_initial_context(
    track_plan_item: Dict[str, Any],
    skeleton: Dict[str, Any],
    batch_plan: List[Dict[str, Any]]
) -> BatchContextState:
    """创建初始批次上下文"""
    purpose = track_plan_item.get("purpose", "")
    track_name = track_plan_item.get("trackName", "Unknown Track")

    suggested_types = parse_purpose_to_action_types(purpose)

    must_follow = []
    if "animation" in track_name.lower():
        must_follow.append("Animation actions should come before others")
    elif "effect" in track_name.lower():
        must_follow.append("Effect and damage actions should follow animation")

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
    """批次生成完成后更新上下文"""
    from ..validators import extract_action_type_name

    new_context: BatchContextState = dict(context)

    # Update completed actions
    completed = list(context.get("completed_actions", []))
    for action in batch_actions:
        params = action.get("parameters", {})
        odin_type = params.get("_odin_type", "")
        action_type = extract_action_type_name(odin_type)
        key_params = extract_key_params(params)

        completed.append({
            "frame": action.get("frame", 0),
            "duration": action.get("duration", 0),
            "action_type": action_type,
            "key_params": key_params,
        })
    new_context["completed_actions"] = completed

    # Update used action types
    used_types = list(context.get("used_action_types", []))
    for action in batch_actions:
        action_type = extract_action_type_name(
            action.get("parameters", {}).get("_odin_type", "")
        )
        if action_type and action_type not in used_types:
            used_types.append(action_type)
    new_context["used_action_types"] = used_types

    # Update occupied frames
    occupied = list(context.get("occupied_frames", []))
    for action in batch_actions:
        frame = action.get("frame", 0)
        duration = action.get("duration", 0)
        occupied.append((frame, frame + duration))
    new_context["occupied_frames"] = merge_frame_intervals(occupied)

    # Update batch info
    new_context["batch_id"] = next_batch_idx

    # Update phase
    if next_batch_idx < len(batch_plan):
        total = len(batch_plan)
        if next_batch_idx < total * 0.3:
            new_context["phase"] = BatchPhase.SETUP.value
        elif next_batch_idx < total * 0.7:
            new_context["phase"] = BatchPhase.MAIN.value
        else:
            new_context["phase"] = BatchPhase.CLEANUP.value

        new_context["current_goal"] = batch_plan[next_batch_idx].get("context", "")

    # Update prerequisites
    prerequisites_met = list(context.get("prerequisites_met", []))
    if "AnimationAction" in used_types:
        prerequisites_met.append("animation_played")
    if "SpawnEffectAction" in used_types:
        prerequisites_met.append("effect_spawned")
    new_context["prerequisites_met"] = list(set(prerequisites_met))

    return new_context


def format_context_for_prompt(context: BatchContextState) -> str:
    """将上下文格式化为 prompt 文本"""
    lines = []

    if context.get("design_intent"):
        lines.append(f"**Track Design Intent**: {context['design_intent']}")

    if context.get("current_goal"):
        lines.append(f"**Current Batch Goal**: {context['current_goal']}")

    phase = context.get("phase", "main")
    phase_desc = {
        "setup": "Setup phase (animation windup, preparation effects)",
        "main": "Main phase (core damage, primary effects)",
        "cleanup": "Cleanup phase (recovery, dissipation effects)"
    }
    lines.append(f"**Current Phase**: {phase_desc.get(phase, phase)}")

    completed = context.get("completed_actions", [])
    if completed:
        lines.append("**Generated Actions**:")
        for action in completed[-8:]:
            lines.append(
                f"  - Frame {action['frame']}-{action['frame']+action['duration']}: "
                f"{action['action_type']}"
            )
    else:
        lines.append("**Generated Actions**: None (first batch)")

    occupied = context.get("occupied_frames", [])
    if occupied:
        intervals = ", ".join([f"{s}-{e}" for s, e in occupied[-5:]])
        lines.append(f"**Occupied Frames**: {intervals}")

    if context.get("must_follow"):
        lines.append(f"**Must Follow**: {'; '.join(context['must_follow'])}")

    if context.get("suggested_types"):
        lines.append(f"**Suggested Action Types**: {', '.join(context['suggested_types'][:5])}")

    if context.get("avoid_patterns"):
        lines.append(f"**Avoid**: {'; '.join(context['avoid_patterns'][:3])}")

    return "\n".join(lines)

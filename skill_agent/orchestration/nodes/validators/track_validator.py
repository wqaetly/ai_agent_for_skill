"""
Track 验证模块
"""

from typing import Any, Dict, List, Tuple

from ..constants import TRACK_TYPE_RULES


def validate_track(track_data: Dict[str, Any], total_duration: int) -> List[str]:
    """
    验证单个 Track 的合法性

    Args:
        track_data: Track 数据
        total_duration: 技能总时长

    Returns:
        错误列表
    """
    errors = []

    track_name = track_data.get("trackName", "")
    if not track_name:
        errors.append("trackName cannot be empty")

    actions = track_data.get("actions", [])
    if not actions:
        errors.append(f"Track '{track_name}' has no actions")
        return errors

    for idx, action in enumerate(actions):
        frame = action.get("frame", -1)
        duration = action.get("duration", 0)
        params = action.get("parameters", {})

        if frame < 0:
            errors.append(f"Track '{track_name}' action[{idx}].frame ({frame}) must be >= 0")

        if duration < 1:
            errors.append(f"Track '{track_name}' action[{idx}].duration ({duration}) must be >= 1")

        if frame + duration > total_duration:
            errors.append(
                f"Track '{track_name}' action[{idx}] exceeds totalDuration "
                f"({frame}+{duration} > {total_duration})"
            )

        if "_odin_type" not in params:
            errors.append(f"Track '{track_name}' action[{idx}].parameters missing _odin_type")

    return errors


def validate_track_type_compliance(
    actions: List[Dict[str, Any]],
    track_type: str
) -> Tuple[List[str], List[str]]:
    """
    验证 Track 内 actions 是否符合 Track 类型要求

    Args:
        actions: Track 内的所有 actions
        track_type: Track 类型

    Returns:
        (errors, warnings) 元组
    """
    from .action_validator import extract_action_type_name

    errors = []
    warnings = []

    if track_type not in TRACK_TYPE_RULES:
        return errors, warnings

    rules = TRACK_TYPE_RULES[track_type]
    primary_actions = rules.get("primary_actions", [])
    forbidden_actions = rules.get("forbidden_actions", [])
    typical_count = rules.get("typical_count", (1, 20))

    action_types = []
    for action in actions:
        action_type = extract_action_type_name(
            action.get("parameters", {}).get("_odin_type", "")
        )
        action_types.append(action_type)

    for action_type in action_types:
        if action_type in forbidden_actions:
            errors.append(f"Track type '{track_type}' forbids '{action_type}'")

    min_count, max_count = typical_count
    actual_count = len(actions)
    if actual_count < min_count:
        warnings.append(f"Track '{track_type}' action count ({actual_count}) below recommended ({min_count})")
    elif actual_count > max_count:
        warnings.append(f"Track '{track_type}' action count ({actual_count}) exceeds recommended ({max_count})")

    has_primary = any(at in primary_actions for at in action_types)
    if not has_primary and action_types:
        warnings.append(f"Track '{track_type}' missing primary action types: {', '.join(primary_actions[:2])}")

    return errors, warnings

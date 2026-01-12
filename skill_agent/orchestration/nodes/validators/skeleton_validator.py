"""
骨架验证模块
"""

from typing import Any, Dict, List


def validate_skeleton(skeleton: Dict[str, Any]) -> List[str]:
    """
    验证技能骨架的合法性

    验证规则：
    1. skillName、skillId 非空
    2. totalDuration >= 30（至少1秒@30fps）
    3. trackPlan 非空数组
    4. 每个 trackPlan 项包含 trackName 和 purpose

    Args:
        skeleton: 骨架数据（dict 格式）

    Returns:
        错误列表，空表示验证通过
    """
    errors = []

    if not skeleton.get("skillName"):
        errors.append("skillName cannot be empty")

    if not skeleton.get("skillId"):
        errors.append("skillId cannot be empty")

    total_duration = skeleton.get("totalDuration", 0)
    if not isinstance(total_duration, int) or total_duration < 30:
        errors.append(f"totalDuration ({total_duration}) must be >= 30")

    track_plan = skeleton.get("trackPlan", [])
    if not track_plan or not isinstance(track_plan, list):
        errors.append("trackPlan cannot be empty")
        return errors

    track_names_seen = set()
    for idx, track_item in enumerate(track_plan):
        if not isinstance(track_item, dict):
            errors.append(f"trackPlan[{idx}] must be an object")
            continue

        track_name = track_item.get("trackName")
        purpose = track_item.get("purpose")

        if not track_name:
            errors.append(f"trackPlan[{idx}].trackName cannot be empty")
        else:
            if track_name in track_names_seen:
                errors.append(f"trackPlan[{idx}].trackName '{track_name}' is duplicated")
            track_names_seen.add(track_name)

        if not purpose:
            errors.append(f"trackPlan[{idx}].purpose cannot be empty")

        estimated_actions = track_item.get("estimatedActions", 1)
        if not isinstance(estimated_actions, int) or estimated_actions < 1 or estimated_actions > 20:
            errors.append(f"trackPlan[{idx}].estimatedActions ({estimated_actions}) must be 1-20")

    return errors

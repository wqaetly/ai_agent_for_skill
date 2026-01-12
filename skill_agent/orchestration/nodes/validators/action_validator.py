"""
Action 验证模块
"""

from typing import Any, Dict, List, Optional, Tuple

from ..constants import SEMANTIC_RULES, TRACK_TYPE_RULES, PHASE_RULES
from ...schemas import BatchContextState


def extract_action_type_name(odin_type: str) -> str:
    """
    从 _odin_type 字符串提取简化的 Action 类型名

    Args:
        odin_type: 如 "6|SkillSystem.Actions.DamageAction, Assembly-CSharp"

    Returns:
        简化名称如 "DamageAction"
    """
    if not odin_type:
        return "Unknown"

    if "|" in odin_type:
        odin_type = odin_type.split("|", 1)[1]

    if "." in odin_type:
        parts = odin_type.split(".")
        for i, part in enumerate(parts):
            if part == "Actions" and i + 1 < len(parts):
                class_name = parts[i + 1].split(",")[0].strip()
                return class_name

    return odin_type.split(".")[-1].split(",")[0].strip()


def validate_action_matches_track_type(
    action_data: Dict[str, Any],
    track_type: str
) -> Tuple[bool, str]:
    """
    验证生成的 Action 类型是否与 Track 类型匹配

    Returns:
        (is_valid, error_message)
    """
    params = action_data.get("parameters", {})
    odin_type = params.get("_odin_type", "")
    action_type_name = extract_action_type_name(odin_type).lower()

    allowed_actions = {
        "animation": ["animation", "playanimation", "animator"],
        "effect": ["effect", "spawn", "damage", "buff", "debuff", "heal", "shield", "projectile"],
        "audio": ["sound", "audio", "playsound", "playaudio"],
        "movement": ["move", "dash", "teleport", "knockback", "pull"],
        "camera": ["camera", "shake", "zoom", "focus"],
    }

    allowed_keywords = allowed_actions.get(track_type, [])

    if track_type == "other" or not allowed_keywords:
        return True, ""

    for keyword in allowed_keywords:
        if keyword in action_type_name:
            return True, ""

    return False, f"Action '{action_type_name}' does not match track type '{track_type}'"


def validate_semantic_rules(
    actions: List[Dict[str, Any]],
    context: BatchContextState,
    track_type: Optional[str] = None
) -> List[str]:
    """
    验证 actions 是否符合语义规则

    Args:
        actions: 当前批次的 actions
        context: 批次上下文
        track_type: Track 类型

    Returns:
        违规信息列表
    """
    violations = []
    used_types = list(context.get("used_action_types", []))
    current_phase = context.get("phase", "main")

    batch_types = []
    for action in actions:
        action_type = extract_action_type_name(
            action.get("parameters", {}).get("_odin_type", "")
        )
        batch_types.append(action_type)

    all_types = used_types + batch_types

    # 基础语义规则验证
    for rule in SEMANTIC_RULES:
        condition = rule["condition"]
        if condition not in batch_types:
            continue

        for required in rule.get("requires_before", []):
            if required not in all_types:
                severity = rule.get("severity", "warning")
                if severity == "error":
                    violations.append(f"[ERROR] {condition} requires {required} before it")
                elif severity == "warning":
                    violations.append(f"[WARNING] Suggest adding {required} before {condition}")

        for suggested in rule.get("suggests_with", []):
            if suggested not in batch_types and suggested not in used_types:
                violations.append(f"[SUGGEST] {condition} usually pairs with {suggested}")

    # Track 类型特定规则
    if track_type and track_type in TRACK_TYPE_RULES:
        track_rules = TRACK_TYPE_RULES[track_type]
        forbidden = track_rules.get("forbidden_actions", [])
        
        for action_type in batch_types:
            if action_type in forbidden:
                violations.append(f"[WARNING] {action_type} should not be in {track_type} track")

        primary = track_rules.get("primary_actions", [])
        has_primary = any(at in primary for at in batch_types)
        if not has_primary and batch_types:
            violations.append(f"[SUGGEST] {track_type} track should use: {', '.join(primary[:3])}")

    # 阶段特定规则
    if current_phase == "setup":
        if "AnimationAction" not in batch_types and "AnimationAction" not in used_types:
            if any(at in batch_types for at in ["DamageAction", "BuffAction"]):
                violations.append("[SUGGEST] Setup phase should play animation before damage/buff")

    elif current_phase == "cleanup":
        cleanup_unfriendly = ["DamageAction", "BuffAction", "ProjectileAction"]
        for action_type in batch_types:
            if action_type in cleanup_unfriendly:
                violations.append(f"[SUGGEST] {action_type} is not suitable for cleanup phase")

    # 时间轴冲突检测
    occupied_frames = context.get("occupied_frames", [])
    for action in actions:
        frame = action.get("frame", 0)
        duration = action.get("duration", 0)
        action_end = frame + duration

        for start, end in occupied_frames:
            overlap_start = max(frame, start)
            overlap_end = min(action_end, end)
            overlap = overlap_end - overlap_start

            if overlap > duration * 0.5:
                action_type = extract_action_type_name(
                    action.get("parameters", {}).get("_odin_type", "")
                )
                violations.append(
                    f"[SUGGEST] {action_type}(frame {frame}-{action_end}) overlaps significantly with existing action"
                )
                break

    return violations

"""
Track 验证模块
"""

import logging
from typing import Any, Dict, List, Tuple, Set

from ..constants import TRACK_TYPE_RULES

logger = logging.getLogger(__name__)

# 缓存可用的 Action 类型
_available_action_types: Set[str] = set()


def get_available_action_types(force_refresh: bool = False) -> Set[str]:
    """
    获取所有可用的 Action 类型名称
    
    Returns:
        可用的 Action 类型名称集合
    """
    global _available_action_types
    
    if _available_action_types and not force_refresh:
        return _available_action_types
    
    try:
        from core.action_indexer import ActionIndexer
        import os
        
        # 获取 Actions 目录路径
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        actions_dir = os.path.join(base_dir, "Data", "Actions")
        
        config = {"actions_directory": actions_dir}
        indexer = ActionIndexer(config)
        actions = indexer.get_all_actions()
        
        _available_action_types = {action.get('typeName', '') for action in actions if action.get('typeName')}
        logger.info(f"Loaded {len(_available_action_types)} available action types")
        
    except Exception as e:
        logger.error(f"Failed to load available action types: {e}")
        _available_action_types = set()
    
    return _available_action_types


def validate_action_type_exists(action_type_name: str) -> Tuple[bool, str]:
    """
    验证 Action 类型是否存在于项目中
    
    Args:
        action_type_name: Action 类型名称（如 "DamageAction"）
    
    Returns:
        (exists, error_message)
    """
    available_types = get_available_action_types()
    
    if not available_types:
        # 如果无法加载可用类型，跳过验证
        return True, ""
    
    if action_type_name in available_types:
        return True, ""
    
    # 尝试模糊匹配（可能是完整类型名）
    for available in available_types:
        if action_type_name.endswith(available) or available.endswith(action_type_name):
            return True, ""
    
    return False, f"Action type '{action_type_name}' does not exist in project. Available types: {', '.join(sorted(available_types)[:10])}..."


def validate_track_action_types(track_data: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """
    验证 Track 中所有 Action 类型是否存在
    
    Args:
        track_data: Track 数据
    
    Returns:
        (missing_types, error_messages)
    """
    from .action_validator import extract_action_type_name
    
    missing_types = []
    error_messages = []
    
    actions = track_data.get("actions", [])
    track_name = track_data.get("trackName", "Unknown")
    
    for idx, action in enumerate(actions):
        odin_type = action.get("parameters", {}).get("_odin_type", "")
        action_type_name = extract_action_type_name(odin_type)
        
        if not action_type_name or action_type_name == "Unknown":
            continue
        
        exists, error_msg = validate_action_type_exists(action_type_name)
        if not exists:
            missing_types.append(action_type_name)
            error_messages.append(f"Track '{track_name}' action[{idx}]: {error_msg}")
    
    return missing_types, error_messages


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

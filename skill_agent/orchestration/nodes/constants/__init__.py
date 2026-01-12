"""
常量模块
提供默认 Action 模板、语义规则、Track 类型等配置数据
"""

from .default_actions import (
    DEFAULT_ACTIONS_BY_TRACK_TYPE,
    get_default_actions_for_track_type,
)
from .semantic_rules import (
    SEMANTIC_RULES,
    TRACK_TYPE_RULES,
    PHASE_RULES,
    SEMANTIC_KEYWORD_MAP,
)
from .track_types import (
    TRACK_TYPE_KEYWORDS,
    infer_track_type,
)

__all__ = [
    "DEFAULT_ACTIONS_BY_TRACK_TYPE",
    "get_default_actions_for_track_type",
    "SEMANTIC_RULES",
    "TRACK_TYPE_RULES",
    "PHASE_RULES",
    "SEMANTIC_KEYWORD_MAP",
    "TRACK_TYPE_KEYWORDS",
    "infer_track_type",
]

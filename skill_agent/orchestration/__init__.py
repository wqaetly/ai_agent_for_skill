"""
skill_agent Orchestration Layer
LangGraph 编排层，提供链式调用和循环优化能�?
模块�?- graphs/：LangGraph 图定义（skill_generation, validation_loop 等）
- nodes/：Graph 节点实现（generator, validator, fixer 等）
- prompts/：Prompt 模板管理
- tools/：RAG Core 工具封装
"""

__version__ = "1.0.0"

# 导出核心�?from .graphs.skill_generation import (
    get_skill_generation_graph,
    generate_skill,
    generate_skill_sync,
)

from .graphs.other_graphs import (
    get_skill_search_graph,
    get_skill_detail_graph,
    get_skill_validation_graph,
    get_parameter_inference_graph,
    get_action_search_graph,
)

# 导出工具
from .tools.rag_tools import RAG_TOOLS

# 导出 Prompt 管理�?from .prompts.prompt_manager import get_prompt_manager

__all__ = [
    # 图实例获取函�?    "get_skill_generation_graph",
    "get_skill_search_graph",
    "get_skill_detail_graph",
    "get_skill_validation_graph",
    "get_parameter_inference_graph",
    "get_action_search_graph",
    # 便捷接口
    "generate_skill",
    "generate_skill_sync",
    # 工具和管理器
    "RAG_TOOLS",
    "get_prompt_manager",
]

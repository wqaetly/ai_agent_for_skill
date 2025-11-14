"""
LangGraph CLI 入口点
为 langgraph dev 提供编译后的 graph 实例
"""

from orchestration import (
    get_skill_generation_graph,
    get_skill_search_graph,
    get_skill_detail_graph,
    get_skill_validation_graph,
    get_parameter_inference_graph,
)

# 导出编译后的 graph 实例
skill_generation = get_skill_generation_graph()
skill_search = get_skill_search_graph()
skill_detail = get_skill_detail_graph()
skill_validation = get_skill_validation_graph()
parameter_inference = get_parameter_inference_graph()

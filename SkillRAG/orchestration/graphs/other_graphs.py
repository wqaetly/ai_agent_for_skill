"""
其他 LangGraph 图实现
包括：技能搜索、详情查询、验证修复、参数推理
"""

from typing import Dict, Any, List, TypedDict
from langgraph.graph import StateGraph, END
from ..tools.rag_tools import (
    search_skills_semantic,
    get_skill_detail,
    get_parameter_suggestions,
)


# ==================== 技能搜索图 ====================

class SkillSearchState(TypedDict):
    """技能搜索状态"""
    query: str
    top_k: int
    filters: Dict[str, Any]
    results: List[Dict[str, Any]]


def search_node(state: SkillSearchState) -> Dict[str, Any]:
    """搜索节点"""
    query = state["query"]
    top_k = state.get("top_k", 5)
    filters = state.get("filters")

    results = search_skills_semantic.invoke({
        "query": query,
        "top_k": top_k,
        "filters": filters
    })

    return {"results": results}


def build_skill_search_graph():
    """构建技能搜索图（单节点）"""
    workflow = StateGraph(SkillSearchState)
    workflow.add_node("search", search_node)
    workflow.set_entry_point("search")
    workflow.add_edge("search", END)
    return workflow.compile()


_skill_search_graph = None


def get_skill_search_graph():
    """获取技能搜索图单例"""
    global _skill_search_graph
    if _skill_search_graph is None:
        _skill_search_graph = build_skill_search_graph()
    return _skill_search_graph


# ==================== 技能详情图 ====================

class SkillDetailState(TypedDict):
    """技能详情状态"""
    skill_id: str
    result: Dict[str, Any]


def detail_node(state: SkillDetailState) -> Dict[str, Any]:
    """详情查询节点"""
    skill_id = state["skill_id"]
    result = get_skill_detail.invoke({"skill_id": skill_id})
    return {"result": result}


def build_skill_detail_graph():
    """构建技能详情图（单节点）"""
    workflow = StateGraph(SkillDetailState)
    workflow.add_node("detail", detail_node)
    workflow.set_entry_point("detail")
    workflow.add_edge("detail", END)
    return workflow.compile()


_skill_detail_graph = None


def get_skill_detail_graph():
    """获取技能详情图单例"""
    global _skill_detail_graph
    if _skill_detail_graph is None:
        _skill_detail_graph = build_skill_detail_graph()
    return _skill_detail_graph


# ==================== 技能验证图 ====================

class SkillValidationState(TypedDict):
    """技能验证状态"""
    skill_json: str  # 待验证的 JSON
    validation_errors: List[str]
    fixed_json: str
    retry_count: int
    max_retries: int
    final_result: Dict[str, Any]


def validation_only_node(state: SkillValidationState) -> Dict[str, Any]:
    """纯验证节点（复用 skill_nodes 的逻辑）"""
    from ..nodes.skill_nodes import validator_node

    # 构造兼容的 state
    temp_state = {"generated_json": state["skill_json"]}
    result = validator_node(temp_state)

    return {
        "validation_errors": result["validation_errors"]
    }


def fix_only_node(state: SkillValidationState) -> Dict[str, Any]:
    """纯修复节点"""
    from ..nodes.skill_nodes import fixer_node

    temp_state = {
        "generated_json": state["skill_json"],
        "validation_errors": state["validation_errors"],
        "retry_count": state["retry_count"]
    }

    result = fixer_node(temp_state)

    return {
        "fixed_json": result["generated_json"],
        "skill_json": result["generated_json"],  # 更新 skill_json
        "retry_count": result["retry_count"]
    }


def should_continue_validation(state: SkillValidationState) -> str:
    """判断验证是否继续"""
    errors = state.get("validation_errors", [])
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)

    if not errors:
        return "end"

    if retry_count >= max_retries:
        return "end"

    return "fix"


def build_skill_validation_graph():
    """构建技能验证图（验证 → 修复循环）"""
    workflow = StateGraph(SkillValidationState)

    workflow.add_node("validate", validation_only_node)
    workflow.add_node("fix", fix_only_node)

    workflow.set_entry_point("validate")

    workflow.add_conditional_edges(
        "validate",
        should_continue_validation,
        {
            "fix": "fix",
            "end": END
        }
    )

    workflow.add_edge("fix", "validate")  # 修复后重新验证

    return workflow.compile()


_skill_validation_graph = None


def get_skill_validation_graph():
    """获取技能验证图单例"""
    global _skill_validation_graph
    if _skill_validation_graph is None:
        _skill_validation_graph = build_skill_validation_graph()
    return _skill_validation_graph


# ==================== 参数推理图 ====================

class ParameterInferenceState(TypedDict):
    """参数推理状态"""
    skill_name: str
    skill_type: str
    action_list: List[str]
    result: Dict[str, Any]


def parameter_inference_node(state: ParameterInferenceState) -> Dict[str, Any]:
    """参数推理节点"""
    skill_name = state["skill_name"]
    skill_type = state["skill_type"]
    action_list = state["action_list"]

    result = get_parameter_suggestions.invoke({
        "skill_name": skill_name,
        "skill_type": skill_type,
        "action_list": action_list
    })

    return {"result": result}


def build_parameter_inference_graph():
    """构建参数推理图（单节点）"""
    workflow = StateGraph(ParameterInferenceState)
    workflow.add_node("infer", parameter_inference_node)
    workflow.set_entry_point("infer")
    workflow.add_edge("infer", END)
    return workflow.compile()


_parameter_inference_graph = None


def get_parameter_inference_graph():
    """获取参数推理图单例"""
    global _parameter_inference_graph
    if _parameter_inference_graph is None:
        _parameter_inference_graph = build_parameter_inference_graph()
    return _parameter_inference_graph

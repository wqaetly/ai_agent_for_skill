"""
RAG Core 工具封装
将 RAG Core 功能封装为 LangChain Tools，供 LangGraph 调用
"""

from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from pydantic import BaseModel, Field

# 导入 RAG Core（延迟导入，避免循环依赖）
_rag_engine_instance = None


def get_rag_engine():
    """获取 RAG Engine 单例"""
    global _rag_engine_instance

    if _rag_engine_instance is None:
        from core import RAGEngine
        from core.config import get_config

        config = get_config()
        _rag_engine_instance = RAGEngine(config.to_dict())

    return _rag_engine_instance


# ==================== Pydantic 输入 Schema ====================

class SearchSkillsInput(BaseModel):
    """语义搜索技能输入"""
    query: str = Field(description="搜索查询（自然语言）")
    top_k: int = Field(default=5, description="返回结果数量")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="过滤条件")


class GetSkillDetailInput(BaseModel):
    """获取技能详情输入"""
    skill_id: str = Field(description="技能 ID")


# ==================== LangChain Tools ====================

@tool(args_schema=SearchSkillsInput)
def search_skills_semantic(query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    语义搜索技能配置

    根据自然语言描述搜索相似的技能配置。

    Args:
        query: 搜索查询（如"治疗技能"、"范围伤害"）
        top_k: 返回结果数量
        filters: 过滤条件（可选，如 {"skillType": "Attack"}）

    Returns:
        技能配置列表，每个包含：skill_id, skill_name, similarity_score, skill_data
    """
    rag = get_rag_engine()
    results = rag.search(query, top_k=top_k, filters=filters)
    return results


@tool(args_schema=GetSkillDetailInput)
def get_skill_detail(skill_id: str) -> Dict[str, Any]:
    """
    获取技能详细配置

    根据技能 ID 获取完整的技能配置 JSON。

    Args:
        skill_id: 技能 ID

    Returns:
        完整的技能配置字典
    """
    rag = get_rag_engine()
    skill_data = rag.get_skill_by_id(skill_id)

    if skill_data is None:
        return {"error": f"技能 ID '{skill_id}' 不存在"}

    return skill_data


@tool
def search_actions(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    搜索 Action 脚本

    根据描述搜索相似的 Action 脚本（如 DamageAction、HealAction）。

    Args:
        query: 搜索查询（如"造成伤害"、"治疗队友"）
        top_k: 返回结果数量

    Returns:
        Action 列表，每个包含：action_name, action_type, parameters
    """
    rag = get_rag_engine()

    # 调用 Action 搜索功能
    if hasattr(rag, 'action_indexer'):
        results = rag.action_indexer.search(query, top_k=top_k)
        return results
    else:
        return {"error": "Action 索引器未初始化"}


@tool
def get_parameter_suggestions(skill_name: str, skill_type: str, action_list: List[str]) -> Dict[str, Any]:
    """
    获取参数建议

    根据技能名称和类型，推荐合理的参数值范围。

    Args:
        skill_name: 技能名称
        skill_type: 技能类型（Attack/Heal/Buff/Debuff）
        action_list: 包含的 Action 列表

    Returns:
        参数建议字典（包含推荐值和范围）
    """
    # 基于技能类型返回参数范围
    parameter_ranges = {
        "Attack": {
            "damage": {"min": 10, "max": 500, "suggested": 100},
            "cooldown": {"min": 1.0, "max": 60.0, "suggested": 5.0},
            "range": {"min": 1.0, "max": 20.0, "suggested": 5.0},
        },
        "Heal": {
            "healing": {"min": 20, "max": 300, "suggested": 80},
            "cooldown": {"min": 2.0, "max": 30.0, "suggested": 8.0},
            "range": {"min": 1.0, "max": 15.0, "suggested": 5.0},
        },
        "Buff": {
            "duration": {"min": 1.0, "max": 60.0, "suggested": 10.0},
            "buff_value": {"min": 0.1, "max": 2.0, "suggested": 0.5},
            "cooldown": {"min": 5.0, "max": 120.0, "suggested": 30.0},
        },
        "Debuff": {
            "duration": {"min": 1.0, "max": 30.0, "suggested": 5.0},
            "debuff_value": {"min": 0.1, "max": 1.0, "suggested": 0.3},
            "cooldown": {"min": 3.0, "max": 60.0, "suggested": 15.0},
        }
    }

    return parameter_ranges.get(skill_type, {})


# ==================== 工具集合 ====================

RAG_TOOLS = [
    search_skills_semantic,
    get_skill_detail,
    search_actions,
    get_parameter_suggestions,
]

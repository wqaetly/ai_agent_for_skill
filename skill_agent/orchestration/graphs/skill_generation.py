"""
技能生成图（循环优化链）
实现：检索 → 生成 → 验证 → 修复 → 重试 的完整循环
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
import os
import logging
from ..nodes.skill_nodes import (
    SkillGenerationState,
    retriever_node,
    generator_node,
    validator_node,
    fixer_node,
    finalize_node,
    should_continue,
)

logger = logging.getLogger(__name__)


def build_skill_generation_graph():
    """
    构建技能生成 LangGraph

    流程：
    1. retrieve: 检索相似技能
    2. generate: 生成 JSON
    3. validate: 验证 JSON
    4. 判断：
       - 如果通过 → finalize（结束）
       - 如果失败且未达重试上限 → fix（修复）→ generate（重新生成）
       - 如果失败且达到上限 → finalize（强制结束）

    Returns:
        编译后的 LangGraph
    """
    # 创建 StateGraph
    workflow = StateGraph(SkillGenerationState)

    # 添加节点
    workflow.add_node("retrieve", retriever_node)
    workflow.add_node("generate", generator_node)
    workflow.add_node("validate", validator_node)
    workflow.add_node("fix", fixer_node)
    workflow.add_node("finalize", finalize_node)

    # 设置入口点
    workflow.set_entry_point("retrieve")

    # 添加边
    workflow.add_edge("retrieve", "generate")  # 检索 → 生成
    workflow.add_edge("generate", "validate")  # 生成 → 验证

    # 条件分支：验证后的路由
    workflow.add_conditional_edges(
        "validate",
        should_continue,
        {
            "fix": "fix",          # 验证失败 → 修复
            "finalize": "finalize" # 验证通过 → 结束
        }
    )

    # 修复后重新生成
    workflow.add_edge("fix", "generate")

    # 最终化后结束
    workflow.add_edge("finalize", END)

    # 🔥 P0改进：添加持久化支持
    # 创建checkpoints目录
    checkpoint_dir = os.path.join(os.path.dirname(__file__), "..", "..", "Data", "checkpoints")
    os.makedirs(checkpoint_dir, exist_ok=True)

    checkpoint_db = os.path.join(checkpoint_dir, "skill_generation.db")
    logger.info(f"💾 使用checkpoint数据库: {checkpoint_db}")

    # 初始化SqliteSaver
    checkpointer = SqliteSaver.from_conn_string(checkpoint_db)

    # 🔥 编译图（添加checkpointer和recursion_limit）
    return workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=[],  # 可以在特定节点前暂停，支持human-in-the-loop
        interrupt_after=[],   # 可以在特定节点后暂停
        debug=False           # 生产环境设为False
    )


# 全局图实例（单例）
_skill_generation_graph = None


def get_skill_generation_graph():
    """获取技能生成图的单例实例"""
    global _skill_generation_graph

    if _skill_generation_graph is None:
        _skill_generation_graph = build_skill_generation_graph()

    return _skill_generation_graph


# ==================== 便捷调用接口 ====================

async def generate_skill(requirement: str, max_retries: int = 3) -> dict:
    """
    生成技能配置（异步）

    Args:
        requirement: 需求描述
        max_retries: 最大重试次数

    Returns:
        包含 final_result、messages、retry_count 的字典
    """
    graph = get_skill_generation_graph()

    initial_state = {
        "requirement": requirement,
        "similar_skills": [],
        "generated_json": "",
        "validation_errors": [],
        "retry_count": 0,
        "max_retries": max_retries,
        "final_result": {},
        "messages": [],
    }

    # 🔥 P0改进：添加thread_id和recursion_limit配置
    config = {
        "configurable": {"thread_id": f"skill_gen_{hash(requirement) % 10000}"},
        "recursion_limit": 50  # 防止无限循环
    }

    result = await graph.ainvoke(initial_state, config)
    return result


def generate_skill_sync(requirement: str, max_retries: int = 3) -> dict:
    """
    生成技能配置（同步）

    Args:
        requirement: 需求描述
        max_retries: 最大重试次数

    Returns:
        包含 final_result、messages、retry_count 的字典
    """
    graph = get_skill_generation_graph()

    initial_state = {
        "requirement": requirement,
        "similar_skills": [],
        "generated_json": "",
        "validation_errors": [],
        "retry_count": 0,
        "max_retries": max_retries,
        "final_result": {},
        "messages": [],
    }

    # 🔥 P0改进：添加thread_id和recursion_limit配置
    config = {
        "configurable": {"thread_id": f"skill_gen_{hash(requirement) % 10000}"},
        "recursion_limit": 50  # 防止无限循环
    }

    result = graph.invoke(initial_state, config)
    return result


# ==================== 可视化 ====================

def visualize_graph():
    """
    生成 Mermaid 图表（用于文档）

    Returns:
        Mermaid 格式的图表字符串
    """
    graph = get_skill_generation_graph()
    return graph.get_graph().draw_mermaid()

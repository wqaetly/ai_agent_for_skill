"""
Agentic RAG 图
基于 LangGraph 官方教程实现的智能检索增强生成系统

流程:
1. generate_query_or_respond: LLM 决定是否需要检索
2. retrieve: 执行技能检索 (ToolNode)
3. grade_documents: 评估文档相关性
4. rewrite_question: 重写问题 (如果文档不相关)
5. generate_answer: 生成最终答案
"""

import os
import logging
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition

from .utils import get_checkpointer
from ..nodes.agentic_rag_nodes import (
    get_skill_retriever_tool,
    generate_query_or_respond,
    grade_documents,
    rewrite_question,
    generate_answer,
)

logger = logging.getLogger(__name__)


def build_agentic_rag_graph():
    """
    构建 Agentic RAG LangGraph
    
    流程:
    START → generate_query_or_respond
        ├─ (有 tool_calls) → retrieve → grade_documents
        │                                   ├─ (相关) → generate_answer → END
        │                                   └─ (不相关) → rewrite_question → generate_query_or_respond
        └─ (无 tool_calls) → END (直接响应)
    
    Returns:
        编译后的 LangGraph
    """
    # 获取检索工具
    retriever_tool = get_skill_retriever_tool()
    
    # 创建 StateGraph (使用 MessagesState)
    workflow = StateGraph(MessagesState)
    
    # 添加节点
    workflow.add_node("generate_query_or_respond", generate_query_or_respond)
    workflow.add_node("retrieve", ToolNode([retriever_tool]))
    workflow.add_node("rewrite_question", rewrite_question)
    workflow.add_node("generate_answer", generate_answer)
    
    # 设置入口点
    workflow.add_edge(START, "generate_query_or_respond")
    
    # 条件边: 决定是否检索
    workflow.add_conditional_edges(
        "generate_query_or_respond",
        tools_condition,  # LangGraph 内置的工具条件判断
        {
            "tools": "retrieve",  # 有 tool_calls → 检索
            END: END,             # 无 tool_calls → 直接结束
        },
    )
    
    # 条件边: 评估文档相关性
    workflow.add_conditional_edges(
        "retrieve",
        grade_documents,  # 返回 "generate_answer" 或 "rewrite_question"
    )
    
    # 普通边
    workflow.add_edge("generate_answer", END)
    workflow.add_edge("rewrite_question", "generate_query_or_respond")
    
    # 获取 checkpointer
    checkpoint_db = os.path.join(
        os.path.dirname(__file__), "..", "..", "Data", "checkpoints", "agentic_rag.db"
    )
    checkpointer = get_checkpointer(checkpoint_db)
    
    # 编译图
    return workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=[],
        interrupt_after=[],
        debug=False
    )


# 全局图实例（单例）
_agentic_rag_graph = None


def get_agentic_rag_graph():
    """获取 Agentic RAG 图的单例实例"""
    global _agentic_rag_graph
    
    if _agentic_rag_graph is None:
        _agentic_rag_graph = build_agentic_rag_graph()
    
    return _agentic_rag_graph


# ==================== 便捷调用接口 ====================

async def agentic_rag_query(question: str, thread_id: str = None) -> dict:
    """
    Agentic RAG 查询（异步）
    
    Args:
        question: 用户问题
        thread_id: 会话线程ID（可选）
        
    Returns:
        包含 messages 的结果字典
    """
    import hashlib
    
    graph = get_agentic_rag_graph()
    
    initial_state = {
        "messages": [{"role": "user", "content": question}]
    }
    
    if thread_id is None:
        thread_id = f"rag_{hashlib.md5(question.encode()).hexdigest()[:8]}"
    
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 10  # 防止无限循环
    }
    
    result = await graph.ainvoke(initial_state, config)
    return result


def agentic_rag_query_sync(question: str, thread_id: str = None) -> dict:
    """
    Agentic RAG 查询（同步）
    
    Args:
        question: 用户问题
        thread_id: 会话线程ID（可选）
        
    Returns:
        包含 messages 的结果字典
    """
    import hashlib
    
    graph = get_agentic_rag_graph()
    
    initial_state = {
        "messages": [{"role": "user", "content": question}]
    }
    
    if thread_id is None:
        thread_id = f"rag_{hashlib.md5(question.encode()).hexdigest()[:8]}"
    
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 10
    }
    
    result = graph.invoke(initial_state, config)
    return result


def agentic_rag_stream(question: str, thread_id: str = None):
    """
    Agentic RAG 流式查询
    
    Args:
        question: 用户问题
        thread_id: 会话线程ID（可选）
        
    Yields:
        每个节点的更新
    """
    import hashlib
    
    graph = get_agentic_rag_graph()
    
    initial_state = {
        "messages": [{"role": "user", "content": question}]
    }
    
    if thread_id is None:
        thread_id = f"rag_{hashlib.md5(question.encode()).hexdigest()[:8]}"
    
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 10
    }
    
    for chunk in graph.stream(initial_state, config):
        for node, update in chunk.items():
            yield {
                "node": node,
                "messages": update.get("messages", [])
            }


# ==================== 可视化 ====================

def visualize_graph():
    """
    生成 Mermaid 图表
    
    Returns:
        Mermaid 格式的图表字符串
    """
    graph = get_agentic_rag_graph()
    return graph.get_graph().draw_mermaid()


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    print("=== Agentic RAG Graph ===")
    print(visualize_graph())
    
    print("\n=== Testing Query ===")
    result = agentic_rag_query_sync("有哪些火焰伤害技能？")
    
    for msg in result["messages"]:
        print(f"\n{msg.__class__.__name__}: {msg.content[:200]}...")

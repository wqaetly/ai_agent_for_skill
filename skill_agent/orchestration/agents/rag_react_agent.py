"""
RAG ReAct Agent - 使用 LangGraph 预构建的 create_react_agent

让 LLM 动态决定是否需要检索参考技能和 Action 定义，
而不是硬编码的检索逻辑。

优势：
1. LLM 根据需求复杂度决定是否检索
2. 可以多轮检索，逐步细化
3. 支持交互式问答
"""

import logging
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
import os

logger = logging.getLogger(__name__)

# RAG Agent 系统提示
RAG_AGENT_SYSTEM_PROMPT = """你是一个 Unity 技能配置助手，负责帮助用户理解和生成技能配置。

你可以使用以下工具来检索参考信息：
1. search_skills_semantic - 搜索相似的技能配置作为参考
2. search_actions - 搜索可用的 Action 类型和参数定义
3. get_skill_detail - 获取特定技能的完整配置
4. get_parameter_suggestions - 获取参数建议

工作流程：
1. 分析用户需求，判断是否需要检索参考
2. 如果需求简单明确（如"火球术"），可以直接生成
3. 如果需求复杂或不确定，先检索相似技能和相关 Action
4. 根据检索结果，提供技能配置建议

注意：
- 不要过度检索，只在必要时使用工具
- 检索结果用于参考，不要直接复制
- 始终确保生成的配置符合 Odin 序列化格式
"""


def get_rag_llm():
    """获取 RAG Agent 使用的 LLM"""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY not set")
    
    return ChatOpenAI(
        model="deepseek-chat",  # 使用 chat 模型而非 reasoner（更快）
        temperature=0.3,
        api_key=api_key,
        base_url="https://api.deepseek.com/v1",
        timeout=60,
    )


def create_rag_react_agent():
    """
    创建 RAG ReAct Agent
    
    使用 LangGraph 预构建的 create_react_agent，
    让 LLM 动态决定是否需要检索。
    """
    from langgraph.prebuilt import create_react_agent
    from ..tools.rag_tools import RAG_TOOLS
    
    llm = get_rag_llm()
    
    agent = create_react_agent(
        model=llm,
        tools=RAG_TOOLS,
        prompt=RAG_AGENT_SYSTEM_PROMPT,
    )
    
    logger.info("RAG ReAct Agent created")
    return agent


# 全局 Agent 实例
_rag_agent = None


def get_rag_agent():
    """获取 RAG Agent 单例"""
    global _rag_agent
    if _rag_agent is None:
        _rag_agent = create_rag_react_agent()
    return _rag_agent


async def analyze_requirement_with_rag(requirement: str) -> Dict[str, Any]:
    """
    使用 RAG Agent 分析需求并检索相关信息
    
    Args:
        requirement: 用户需求描述
    
    Returns:
        包含 similar_skills, action_schemas, analysis 的字典
    """
    agent = get_rag_agent()
    
    prompt = f"""请分析以下技能需求，并决定是否需要检索参考信息：

需求：{requirement}

请执行以下步骤：
1. 判断需求复杂度
2. 如果需要参考，使用工具检索相似技能和相关 Action
3. 总结检索结果，提供配置建议

最后，请以 JSON 格式输出你的分析结果：
{{
    "complexity": "simple|medium|complex",
    "needs_reference": true/false,
    "similar_skills_summary": "相似技能摘要",
    "recommended_actions": ["Action1", "Action2"],
    "suggestions": "配置建议"
}}
"""
    
    result = await agent.ainvoke({
        "messages": [HumanMessage(content=prompt)]
    })
    
    # 提取最后一条消息作为分析结果
    last_message = result["messages"][-1]
    
    return {
        "analysis": last_message.content,
        "messages": result["messages"],
    }


def analyze_requirement_with_rag_sync(requirement: str) -> Dict[str, Any]:
    """同步版本的需求分析"""
    agent = get_rag_agent()
    
    prompt = f"""请分析以下技能需求，并决定是否需要检索参考信息：

需求：{requirement}

请执行以下步骤：
1. 判断需求复杂度
2. 如果需要参考，使用工具检索相似技能和相关 Action
3. 总结检索结果，提供配置建议
"""
    
    result = agent.invoke({
        "messages": [HumanMessage(content=prompt)]
    })
    
    last_message = result["messages"][-1]
    
    return {
        "analysis": last_message.content,
        "messages": result["messages"],
    }


# 导出
__all__ = [
    "create_rag_react_agent",
    "get_rag_agent",
    "analyze_requirement_with_rag",
    "analyze_requirement_with_rag_sync",
]

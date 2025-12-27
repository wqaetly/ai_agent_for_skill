"""
Agentic RAG 节点实现
基于 LangGraph 官方 Agentic RAG 教程，整合现有 RAG Core
"""

import logging
from typing import Any, Dict, List, Literal
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import MessagesState

from .skill_nodes import get_llm

logger = logging.getLogger(__name__)


# ==================== Pydantic Schema ====================

class GradeDocuments(BaseModel):
    """文档相关性评分 Schema"""
    binary_score: str = Field(
        description="相关性评分: 'yes' 表示相关, 'no' 表示不相关"
    )


# ==================== Prompts ====================

GRADE_PROMPT = """你是一个评估检索文档与用户问题相关性的评分员。

检索到的文档内容:
{context}

用户问题: {question}

如果文档包含与用户问题相关的关键词或语义内容，则评为相关。
请给出二元评分 'yes' 或 'no' 来表示文档是否与问题相关。"""

REWRITE_PROMPT = """分析以下问题，理解其潜在的语义意图。

原始问题:
-------
{question}
-------

请重新表述一个更清晰、更具体的问题，以便更好地检索相关信息:"""

GENERATE_PROMPT = """你是一个技能配置问答助手。
使用以下检索到的上下文来回答问题。
如果你不知道答案，就说不知道。
回答要简洁，最多三句话。

问题: {question}

上下文: {context}"""


# ==================== Retriever Tool ====================

def get_skill_retriever_tool():
    """获取技能检索工具"""
    from langchain_core.tools import tool
    from ..tools.rag_tools import get_rag_engine
    
    @tool
    def retrieve_skills(query: str) -> str:
        """搜索并返回与查询相关的技能配置信息。
        
        Args:
            query: 搜索查询（自然语言描述）
            
        Returns:
            检索到的技能信息
        """
        rag = get_rag_engine()
        results = rag.search_skills(query, top_k=3, return_details=True)
        
        if not results:
            return "未找到相关技能配置。"
        
        formatted_results = []
        for skill in results:
            skill_info = f"""
技能名称: {skill.get('skill_name', 'Unknown')}
技能ID: {skill.get('skill_id', 'N/A')}
相似度: {skill.get('similarity', 0):.2%}
Action数量: {skill.get('num_actions', 0)}
总时长: {skill.get('total_duration', 0)} 帧
"""
            if skill.get('search_text_preview'):
                skill_info += f"描述预览: {skill.get('search_text_preview', '')[:200]}..."
            formatted_results.append(skill_info)
        
        return "\n---\n".join(formatted_results)
    
    return retrieve_skills


# ==================== 节点函数 ====================

def generate_query_or_respond(state: MessagesState) -> Dict[str, Any]:
    """
    生成查询或直接响应节点
    
    LLM 决定是否需要调用检索工具，或者直接回答用户
    """
    retriever_tool = get_skill_retriever_tool()
    
    # 使用 deepseek-chat 而非 reasoner（更快，适合简单决策）
    llm = get_llm(model="deepseek-chat", temperature=0, streaming=False)
    llm_with_tools = llm.bind_tools([retriever_tool])
    
    response = llm_with_tools.invoke(state["messages"])
    
    logger.info(f"generate_query_or_respond: tool_calls={bool(response.tool_calls)}")
    
    return {"messages": [response]}


def grade_documents(state: MessagesState) -> Literal["generate_answer", "rewrite_question"]:
    """
    评估检索文档的相关性（条件边）
    
    Returns:
        "generate_answer" - 文档相关，生成答案
        "rewrite_question" - 文档不相关，重写问题
    """
    messages = state["messages"]
    
    # 获取原始问题（第一条消息）
    question = messages[0].content
    
    # 获取检索结果（最后一条 tool message）
    context = messages[-1].content
    
    # 使用 structured output 进行评分
    llm = get_llm(model="deepseek-chat", temperature=0, streaming=False)
    grader = llm.with_structured_output(GradeDocuments)
    
    prompt = GRADE_PROMPT.format(question=question, context=context)
    response = grader.invoke([{"role": "user", "content": prompt}])
    
    score = response.binary_score.lower()
    logger.info(f"grade_documents: score={score}")
    
    if score == "yes":
        return "generate_answer"
    else:
        return "rewrite_question"


def rewrite_question(state: MessagesState) -> Dict[str, Any]:
    """
    重写问题节点
    
    当检索结果不相关时，重新表述问题以获得更好的检索结果
    """
    messages = state["messages"]
    question = messages[0].content
    
    llm = get_llm(model="deepseek-chat", temperature=0.3, streaming=False)
    
    prompt = REWRITE_PROMPT.format(question=question)
    response = llm.invoke([{"role": "user", "content": prompt}])
    
    rewritten = response.content
    logger.info(f"rewrite_question: '{question[:50]}...' -> '{rewritten[:50]}...'")
    
    return {"messages": [HumanMessage(content=rewritten)]}


def generate_answer(state: MessagesState) -> Dict[str, Any]:
    """
    生成答案节点
    
    基于检索到的上下文生成最终答案
    """
    messages = state["messages"]
    
    # 获取原始问题
    question = messages[0].content
    
    # 获取检索上下文（最后一条 tool message）
    context = messages[-1].content
    
    llm = get_llm(model="deepseek-chat", temperature=0.7, streaming=True)
    
    prompt = GENERATE_PROMPT.format(question=question, context=context)
    response = llm.invoke([{"role": "user", "content": prompt}])
    
    logger.info(f"generate_answer: response length={len(response.content)}")
    
    return {"messages": [response]}

"""
LangGraph HTTP 服务器
为 agent-chat-ui 提供兼容的 HTTP API 接口
支持技能分析、生成、搜索等功能
"""

import os
import sys
import logging
import asyncio
from typing import Dict, Any, List, Optional, AsyncIterator
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestration import (
    get_skill_generation_graph,
    get_skill_search_graph,
    get_skill_detail_graph,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== 数据模型 ====================

class Message(BaseModel):
    """消息模型（兼容 LangGraph 标准）"""
    role: str = Field(..., description="消息角色: human, ai, system")
    content: str = Field(..., description="消息内容")
    id: Optional[str] = Field(None, description="消息ID")
    name: Optional[str] = Field(None, description="发送者名称")


class ThreadState(BaseModel):
    """线程状态模型"""
    messages: List[Message] = Field(default_factory=list, description="对话历史")
    requirement: Optional[str] = Field(None, description="用户需求")
    similar_skills: List[Dict[str, Any]] = Field(default_factory=list)
    generated_json: Optional[str] = Field(None)
    validation_errors: List[str] = Field(default_factory=list)
    retry_count: int = Field(0)
    max_retries: int = Field(3)
    final_result: Optional[Dict[str, Any]] = Field(None)


class StreamInput(BaseModel):
    """流式输入模型"""
    input: Dict[str, Any] = Field(..., description="输入数据")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    stream_mode: str = Field("values", description="流式模式")


class RunsStreamRequest(BaseModel):
    """运行流请求（兼容 LangGraph API）"""
    input: Dict[str, Any]
    config: Optional[Dict[str, Any]] = None
    stream_mode: Optional[List[str]] = ["values"]
    assistant_id: Optional[str] = None


# ==================== 应用生命周期 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚀 LangGraph Server starting...")
    
    # 预加载图
    try:
        get_skill_generation_graph()
        get_skill_search_graph()
        get_skill_detail_graph()
        logger.info("✅ All graphs loaded successfully")
    except Exception as e:
        logger.error(f"❌ Failed to load graphs: {e}")
    
    yield
    
    logger.info("🛑 LangGraph Server shutting down...")


# ==================== FastAPI 应用 ====================

app = FastAPI(
    title="SkillRAG LangGraph Server",
    description="技能分析与生成的 LangGraph 服务器",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 辅助函数 ====================

def convert_to_langgraph_messages(messages: List[Message]) -> List[Dict[str, Any]]:
    """将消息转换为 LangGraph 格式"""
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    
    result = []
    for msg in messages:
        if msg.role == "human":
            result.append(HumanMessage(content=msg.content))
        elif msg.role == "ai":
            result.append(AIMessage(content=msg.content))
        elif msg.role == "system":
            result.append(SystemMessage(content=msg.content))
    return result


def convert_from_langgraph_messages(messages: List[Any]) -> List[Dict[str, str]]:
    """将 LangGraph 消息转换为标准格式"""
    result = []
    for msg in messages:
        msg_type = msg.__class__.__name__.lower()
        role = "human" if "human" in msg_type else "ai" if "ai" in msg_type else "system"
        result.append({
            "role": role,
            "content": msg.content,
            "id": getattr(msg, "id", None)
        })
    return result


async def stream_graph_updates(
    graph,
    initial_state: Dict[str, Any]
) -> AsyncIterator[str]:
    """
    流式输出图的更新
    
    Args:
        graph: LangGraph 图实例
        initial_state: 初始状态
        
    Yields:
        SSE 格式的事件数据
    """
    try:
        # 使用 astream 进行流式处理
        async for event in graph.astream(initial_state):
            # 格式化为 SSE 事件
            event_data = {
                "event": "values",
                "data": event
            }
            
            # 转换消息格式
            if "messages" in event:
                event_data["data"]["messages"] = convert_from_langgraph_messages(
                    event["messages"]
                )
            
            # 发送事件
            yield f"data: {str(event_data)}\n\n"
            
            # 添加小延迟以确保流式传输
            await asyncio.sleep(0.01)
        
        # 发送结束事件
        yield f"data: {str({'event': 'end'})}\n\n"
        
    except Exception as e:
        logger.error(f"Stream error: {e}", exc_info=True)
        error_event = {
            "event": "error",
            "data": {"error": str(e)}
        }
        yield f"data: {str(error_event)}\n\n"


# ==================== API 端点 ====================

@app.get("/")
async def root():
    """根端点"""
    return {
        "service": "SkillRAG LangGraph Server",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "threads": "/threads/{thread_id}/runs/stream",
            "assistants": "/assistants",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/assistants")
async def list_assistants():
    """列出可用的助手（图）"""
    return {
        "assistants": [
            {
                "assistant_id": "skill-generation",
                "name": "技能生成助手",
                "description": "根据需求描述生成技能配置JSON",
                "graph_id": "skill_generation"
            },
            {
                "assistant_id": "skill-search",
                "name": "技能搜索助手",
                "description": "语义搜索技能库",
                "graph_id": "skill_search"
            },
            {
                "assistant_id": "skill-detail",
                "name": "技能详情助手",
                "description": "查询技能详细信息",
                "graph_id": "skill_detail"
            }
        ]
    }


@app.post("/threads/{thread_id}/runs/stream")
async def create_run_stream(
    thread_id: str,
    request: RunsStreamRequest
):
    """
    创建流式运行（兼容 agent-chat-ui）
    
    这是 agent-chat-ui 调用的主要端点
    """
    try:
        logger.info(f"Stream request for thread {thread_id}: {request.input}")
        
        # 获取助手ID（默认使用技能生成）
        assistant_id = request.assistant_id or request.config.get("configurable", {}).get("assistant_id", "skill-generation")
        
        # 根据助手ID选择图
        if assistant_id == "skill-generation":
            graph = get_skill_generation_graph()
        elif assistant_id == "skill-search":
            graph = get_skill_search_graph()
        elif assistant_id == "skill-detail":
            graph = get_skill_detail_graph()
        else:
            raise HTTPException(status_code=404, detail=f"Assistant '{assistant_id}' not found")
        
        # 准备初始状态
        input_data = request.input
        
        # 从 messages 中提取最新的用户消息作为需求
        messages = input_data.get("messages", [])
        if messages:
            last_message = messages[-1]
            requirement = last_message.get("content", "")
        else:
            requirement = input_data.get("requirement", "")
        
        # 构建初始状态
        initial_state = {
            "requirement": requirement,
            "similar_skills": [],
            "generated_json": "",
            "validation_errors": [],
            "retry_count": 0,
            "max_retries": 3,
            "final_result": {},
            "messages": convert_to_langgraph_messages([Message(**msg) for msg in messages]) if messages else [],
        }
        
        # 返回流式响应
        return StreamingResponse(
            stream_graph_updates(graph, initial_state),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        logger.error(f"Error in stream endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/threads/{thread_id}/runs")
async def create_run(
    thread_id: str,
    request: RunsStreamRequest
):
    """
    创建非流式运行
    """
    try:
        logger.info(f"Run request for thread {thread_id}: {request.input}")
        
        # 获取助手ID
        assistant_id = request.assistant_id or request.config.get("configurable", {}).get("assistant_id", "skill-generation")
        
        # 根据助手ID选择图
        if assistant_id == "skill-generation":
            graph = get_skill_generation_graph()
        elif assistant_id == "skill-search":
            graph = get_skill_search_graph()
        elif assistant_id == "skill-detail":
            graph = get_skill_detail_graph()
        else:
            raise HTTPException(status_code=404, detail=f"Assistant '{assistant_id}' not found")
        
        # 准备初始状态
        input_data = request.input
        messages = input_data.get("messages", [])
        
        if messages:
            last_message = messages[-1]
            requirement = last_message.get("content", "")
        else:
            requirement = input_data.get("requirement", "")
        
        initial_state = {
            "requirement": requirement,
            "similar_skills": [],
            "generated_json": "",
            "validation_errors": [],
            "retry_count": 0,
            "max_retries": 3,
            "final_result": {},
            "messages": convert_to_langgraph_messages([Message(**msg) for msg in messages]) if messages else [],
        }
        
        # 执行图
        result = await graph.ainvoke(initial_state)
        
        # 转换消息格式
        result["messages"] = convert_from_langgraph_messages(result.get("messages", []))
        
        return {
            "thread_id": thread_id,
            "run_id": f"run_{datetime.now().timestamp()}",
            "status": "completed",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Error in run endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/threads/{thread_id}")
async def get_thread(thread_id: str):
    """获取线程信息"""
    return {
        "thread_id": thread_id,
        "created_at": datetime.now().isoformat(),
        "metadata": {}
    }


# ==================== 主函数 ====================

def main():
    """启动服务器"""
    host = os.getenv("LANGGRAPH_HOST", "0.0.0.0")
    port = int(os.getenv("LANGGRAPH_PORT", "2024"))
    
    logger.info(f"Starting LangGraph server on {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()

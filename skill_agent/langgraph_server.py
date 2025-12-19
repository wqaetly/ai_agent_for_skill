"""
LangGraph HTTP 服务器
为 agent-chat-ui 提供兼容的 HTTP API 接口
支持技能分析、生成、搜索等功能
"""

import os
import sys
import logging
import asyncio
import json
from typing import Dict, Any, List, Optional, AsyncIterator
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestration import (
    get_skill_generation_graph,
    get_progressive_skill_generation_graph,
    get_skill_search_graph,
    get_skill_detail_graph,
)
from config import retry, server, rag, timeout, cors

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 🔥 P0改进：状态持久化已迁移到 LangGraph Checkpoint
# 不再需要全局内存存储，所有状态由 SqliteSaver 自动管理
# 每个图在 compile() 时已配置 checkpointer，状态会自动持久化到 SQLite


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
    max_retries: int = Field(default=retry.MAX_RETRIES, description="最大重试次数")
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
        get_progressive_skill_generation_graph()  # 渐进式生成图
        get_skill_search_graph()
        get_skill_detail_graph()
        logger.info("✅ All graphs loaded successfully (including progressive generation)")
    except Exception as e:
        logger.error(f"❌ Failed to load graphs: {e}")

    # 自动初始化 RAG 索引
    try:
        from orchestration.tools.rag_tools import get_rag_engine

        logger.info("🔍 Checking RAG index status...")
        engine = get_rag_engine()

        # 获取索引统计信息
        try:
            skill_count = engine.vector_store.count()
            logger.info(f"Skill index count: {skill_count}")
        except Exception as e:
            logger.warning(f"Failed to get skill count: {e}")
            skill_count = 0

        try:
            action_count = engine.action_vector_store.count()
            logger.info(f"Action index count: {action_count}")
        except Exception as e:
            logger.warning(f"Failed to get action count: {e}")
            action_count = 0

        # 如果索引为空，自动重建
        if skill_count == 0 or action_count == 0:
            logger.info("📦 Empty index detected, initializing...")

            # 重建技能索引
            if skill_count == 0:
                logger.info("  → Indexing skills...")
                skill_result = engine.index_skills(force_rebuild=False)
                logger.info(f"  ✅ Skills indexed: {skill_result.get('count', 0)} items in {skill_result.get('elapsed_time', 0):.2f}s")

            # 重建 Action 索引
            if action_count == 0:
                logger.info("  → Indexing actions...")
                action_result = engine.index_actions(force_rebuild=False)
                logger.info(f"  ✅ Actions indexed: {action_result.get('count', 0)} items in {action_result.get('elapsed_time', 0):.2f}s")

            logger.info("🎉 RAG index initialization complete")
        else:
            logger.info(f"✅ RAG index ready (Skills: {skill_count}, Actions: {action_count})")

    except Exception as e:
        import traceback
        logger.error(f"❌ Failed to initialize RAG index: {e}")
        logger.error(traceback.format_exc())
        logger.warning("⚠️  RAG功能可能无法正常工作，请手动调用 POST /rag/index/rebuild")

    yield

    logger.info("🛑 LangGraph Server shutting down...")


# ==================== FastAPI 应用 ====================

app = FastAPI(
    title="SkillRAG LangGraph Server",
    description="技能分析与生成的 LangGraph 服务器",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 配置（使用配置模块，支持环境变量覆盖）
# 生产环境设置: ALLOWED_ORIGINS=https://your-domain.com
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors.origins_list,
    allow_credentials=cors.ALLOW_CREDENTIALS,
    allow_methods=cors.methods_list,
    allow_headers=cors.headers_list,
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


def normalize_langgraph_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    将 LangGraph Cloud 消息格式转换为内部格式

    处理以下情况：
    - role 可能在 "type" 或 "role" 字段
    - content 可能是字符串或列表

    Args:
        messages: LangGraph Cloud 格式的消息列表

    Returns:
        标准化后的消息列表
    """
    normalized = []
    for msg in messages:
        # 提取 role (type 字段优先)
        role = msg.get("type", msg.get("role", "human"))

        # 提取 content (可能是字符串或列表)
        content = msg.get("content", "")
        if isinstance(content, list):
            # 如果是列表，提取第一个 text 内容
            content = content[0].get("text", "") if content else ""

        normalized.append({
            "id": msg.get("id"),
            "role": role,
            "content": content,
            "name": msg.get("name")
        })

    return normalized


def build_initial_state(
    assistant_id: str,
    requirement: str,
    thread_id: str,
    normalized_messages: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    根据 assistant_id 构建初始状态

    Args:
        assistant_id: 助手类型 ("progressive-skill-generation" 或其他)
        requirement: 用户需求描述
        thread_id: 线程ID
        normalized_messages: 标准化后的消息列表

    Returns:
        对应类型的初始状态字典
    """
    # 转换消息为 LangGraph 格式
    langgraph_messages = convert_to_langgraph_messages([
        Message(
            role=msg["role"],
            content=msg["content"],
            id=msg.get("id"),
            name=msg.get("name")
        )
        for msg in normalized_messages
    ]) if normalized_messages else []

    # 公共字段
    base_state = {
        "requirement": requirement,
        "similar_skills": [],
        "thread_id": thread_id,
        "messages": langgraph_messages,
    }

    if assistant_id == "progressive-skill-generation":
        # 渐进式生成使用 ProgressiveSkillGenerationState
        return {
            **base_state,
            # 阶段1输出
            "skill_skeleton": {},
            "skeleton_validation_errors": [],
            # 阶段2状态
            "track_plan": [],
            "current_track_index": 0,
            "current_track_data": {},
            "generated_tracks": [],
            "current_track_errors": [],
            "track_retry_count": 0,
            "max_track_retries": retry.MAX_TRACK_RETRIES,
            # 阶段3输出
            "assembled_skill": {},
            "final_validation_errors": [],
        }
    else:
        # 标准技能生成使用 SkillGenerationState
        return {
            **base_state,
            "generated_json": "",
            "validation_errors": [],
            "retry_count": 0,
            "max_retries": retry.MAX_RETRIES,
            "final_result": {},
        }


def convert_from_langgraph_messages(messages: List[Any]) -> List[Dict[str, str]]:
    """将 LangGraph 消息转换为标准格式"""
    result = []
    for msg in messages:
        msg_type = msg.__class__.__name__.lower()
        message_type = "human" if "human" in msg_type else "ai" if "ai" in msg_type else "system"
        result.append({
            "type": message_type,  # 前端期望 type 字段，不是 role
            "content": msg.content,
            "id": getattr(msg, "id", None)
        })
    return result


def serialize_event_data(data: Any) -> Any:
    """
    递归序列化事件数据，处理 LangChain 消息对象

    Args:
        data: 待序列化的数据

    Returns:
        可 JSON 序列化的数据
    """
    from langchain_core.messages import BaseMessage

    if isinstance(data, BaseMessage):
        # 转换 LangChain 消息为字典
        msg_type = data.__class__.__name__.lower()
        message_type = "human" if "human" in msg_type else "ai" if "ai" in msg_type else "system"

        # 提取 thinking 标记
        is_thinking = False
        if hasattr(data, 'additional_kwargs') and isinstance(data.additional_kwargs, dict):
            is_thinking = data.additional_kwargs.get("thinking", False)

        result = {
            "type": message_type,  # 前端期望 type 字段，不是 role
            "content": data.content,
            "id": getattr(data, "id", None)
        }

        # 如果是思考消息，添加 thinking 字段
        if is_thinking:
            result["thinking"] = True

        return result
    elif isinstance(data, dict):
        # 递归处理字典
        return {k: serialize_event_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        # 递归处理列表
        return [serialize_event_data(item) for item in data]
    else:
        # 其他类型直接返回
        return data


async def stream_graph_updates(
    graph,
    initial_state: Dict[str, Any],
    thread_id: str
) -> AsyncIterator[str]:
    """
    流式输出图的更新

    Args:
        graph: LangGraph 图实例
        initial_state: 初始状态
        thread_id: 线程ID

    Yields:
        SSE 格式的事件数据
    """
    try:
        logger.info(f"Starting stream for thread {thread_id}, initial_state: {initial_state.get('requirement', 'N/A')}")
        event_count = 0

        # 使用 astream 进行流式处理
        # 维护一个累积的 state
        accumulated_state = {}

        try:
            # 🔥 传递 thread_id 到 config
            config = {"configurable": {"thread_id": thread_id}}

            # 🔥 使用多个 stream_mode：
            # - "values": 图状态更新
            # - "messages": LLM token 级别流式输出（LangGraph Studio 需要）
            # - "custom": 自定义事件
            async for stream_mode, event in graph.astream(
                initial_state,
                config=config,
                stream_mode=["values", "messages", "custom"]
            ):
                event_count += 1
                
                # 🔥 处理 messages 模式（LLM token 流）
                if stream_mode == "messages":
                    # messages 模式返回 (message_chunk, metadata) 元组
                    try:
                        message_chunk, metadata = event
                        # 获取 token 内容
                        content = ""
                        if hasattr(message_chunk, 'content'):
                            content = message_chunk.content
                        elif isinstance(message_chunk, dict):
                            content = message_chunk.get('content', '')
                        
                        if content:
                            # 🔥 SDK 期望 messages 事件数据是 [message_dict, metadata] 数组格式
                            # 参见: @langchain/langgraph-sdk/dist/ui/manager.js:
                            #   const [serialized, metadata] = data;
                            message_dict = {
                                "content": content,
                                "type": "ai",
                                "id": getattr(message_chunk, 'id', None) if hasattr(message_chunk, 'id') else None,
                            }
                            metadata_dict = {
                                "langgraph_node": metadata.get("langgraph_node", "unknown") if isinstance(metadata, dict) else "unknown"
                            }
                            # 发送 [message, metadata] 数组格式
                            messages_event = [message_dict, metadata_dict]
                            event_json = json.dumps(messages_event, ensure_ascii=False)
                            yield f"event: messages\ndata: {event_json}\n\n"
                    except Exception as e:
                        logger.debug(f"Messages event processing: {e}")
                    continue

                # 🔥 处理 custom 模式（自定义事件）
                if stream_mode == "custom":
                    logger.info(f"📨 Received custom event: {event}")
                    try:
                        event_json = json.dumps(event, ensure_ascii=False)
                        logger.info(f"📤 Forwarding custom event with data: {event_json[:200]}...")
                        yield f"event: custom\ndata: {event_json}\n\n"
                    except Exception as e:
                        logger.error(f"❌ Custom event encoding error: {e}", exc_info=True)
                    continue

                # 处理 values 事件（图状态更新）
                logger.debug(f"Raw values event: {event}")

                # 序列化事件数据
                try:
                    serialized_event = serialize_event_data(event)
                    logger.info(f"✅ Event serialized successfully")
                except Exception as e:
                    logger.error(f"❌ Serialization error: {e}", exc_info=True)
                    continue

                # 从节点输出中提取 messages 到顶层
                # LangGraph 输出格式：{node_name: {messages: [...], ...}}
                # 前端期望格式：{messages: [...], node_name: {...}}
                flattened_state = {}
                for node_name, node_output in serialized_event.items():
                    if isinstance(node_output, dict) and 'messages' in node_output:
                        # 将 messages 提升到顶层
                        flattened_state['messages'] = node_output['messages']
                        # 保留节点输出（不包含 messages）
                        flattened_state[node_name] = {k: v for k, v in node_output.items() if k != 'messages'}
                    else:
                        # 保留其他字段
                        flattened_state[node_name] = node_output

                # 累积消息（追加而非覆盖）
                if 'messages' in flattened_state:
                    if 'messages' not in accumulated_state:
                        accumulated_state['messages'] = []

                    # 记录新增的消息内容
                    new_messages = flattened_state['messages']
                    logger.info(f"📨 Event contains {len(new_messages)} messages")
                    for i, msg in enumerate(new_messages):
                        content = msg.get('content', '')
                        content_preview = content[:200] if len(content) > 200 else content
                        # 🔍 检查 thinking 字段
                        thinking_flag = msg.get('thinking', False)
                        msg_id = msg.get('id', 'N/A')
                        logger.info(f"  Message {i+1}: type={msg.get('type', 'unknown')}, id={msg_id}, thinking={thinking_flag}, content={content_preview}...")

                    # 追加到累积状态
                    accumulated_state['messages'].extend(new_messages)
                    # 移除 flattened_state 中的 messages，避免重复 update
                    flattened_state = {k: v for k, v in flattened_state.items() if k != 'messages'}

                # 更新其他状态字段
                accumulated_state.update(flattened_state)

                # 发送标准 SSE 事件（发送累积状态）
                try:
                    event_json = json.dumps(accumulated_state, ensure_ascii=False)
                    logger.info(f"📤 Sending SSE values event (size: {len(event_json)} bytes)")
                    logger.info(f"📋 Event data keys: {list(accumulated_state.keys())}")
                    # 标准 SSE 格式：event: <type>\ndata: <json>\n\n
                    yield f"event: values\ndata: {event_json}\n\n"
                except Exception as e:
                    logger.error(f"❌ JSON encoding error: {e}", exc_info=True)
                    continue

                # 添加小延迟以确保流式传输（减少到 1ms 降低累积延迟）
                await asyncio.sleep(0.001)
        except Exception as e:
            logger.error(f"❌ Stream iteration error: {e}", exc_info=True)
            raise

        # 🔥 P0改进：状态已由 LangGraph Checkpoint 自动持久化，无需手动保存
        # LangGraph 在每次节点执行后自动调用 checkpointer.put()
        logger.info(f"✅ Stream completed for thread {thread_id}, state auto-persisted by checkpoint")

        # 发送结束事件（保留最终状态）
        logger.info(f"Stream completed with {event_count} events, sending end signal")
        final_state_json = json.dumps(accumulated_state, ensure_ascii=False)
        yield f"event: end\ndata: {final_state_json}\n\n"
        logger.info("End signal sent successfully")

    except Exception as e:
        logger.error(f"Stream error: {e}", exc_info=True)
        error_data = {"error": str(e)}
        yield f"event: error\ndata: {json.dumps(error_data, ensure_ascii=False)}\n\n"


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
            "health": "/health",
            "thread_state": "/threads/{thread_id}/state",
            "thread_resume": "/threads/{thread_id}/resume",
            "thread_history": "/threads/{thread_id}/history",
            "rag": {
                "search": "/rag/search",
                "recommend_actions": "/rag/recommend-actions",
                "recommend_parameters": "/rag/recommend-parameters",
                "rebuild_index": "/rag/index/rebuild",
                "stats": "/rag/index/stats",
                "clear_cache": "/rag/cache",
                "health": "/rag/health"
            }
        }
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/info")
async def server_info():
    """
    服务器信息端点（兼容 LangGraph Cloud/Studio）

    前端使用此端点检查服务可用性
    """
    return {
        "version": "1.0.0",
        "name": "SkillRAG LangGraph Server",
        "description": "技能分析与生成的 LangGraph 服务器",
        "status": "ready",
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
                "description": "根据需求描述生成技能配置JSON（一次性生成）",
                "graph_id": "skill_generation"
            },
            {
                "assistant_id": "progressive-skill-generation",
                "name": "渐进式技能生成助手",
                "description": "三阶段渐进式生成技能：骨架→Track→组装（推荐用于复杂技能）",
                "graph_id": "progressive_skill_generation",
                "recommended": True
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
        elif assistant_id == "progressive-skill-generation":
            graph = get_progressive_skill_generation_graph()
        elif assistant_id == "skill-search":
            graph = get_skill_search_graph()
        elif assistant_id == "skill-detail":
            graph = get_skill_detail_graph()
        else:
            raise HTTPException(status_code=404, detail=f"Assistant '{assistant_id}' not found")

        # 准备初始状态
        input_data = request.input
        messages = input_data.get("messages", [])

        # 使用抽取的辅助函数转换消息格式
        normalized_messages = normalize_langgraph_messages(messages)

        # 提取最新消息作为需求
        if normalized_messages:
            requirement = normalized_messages[-1].get("content", "")
        else:
            requirement = input_data.get("requirement", "")

        # 使用抽取的辅助函数构建初始状态
        initial_state = build_initial_state(
            assistant_id=assistant_id,
            requirement=requirement,
            thread_id=thread_id,
            normalized_messages=normalized_messages
        )

        # 返回流式响应
        return StreamingResponse(
            stream_graph_updates(graph, initial_state, thread_id),
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
        elif assistant_id == "progressive-skill-generation":
            graph = get_progressive_skill_generation_graph()
        elif assistant_id == "skill-search":
            graph = get_skill_search_graph()
        elif assistant_id == "skill-detail":
            graph = get_skill_detail_graph()
        else:
            raise HTTPException(status_code=404, detail=f"Assistant '{assistant_id}' not found")
        
        # 准备初始状态
        input_data = request.input
        messages = input_data.get("messages", [])

        # 使用抽取的辅助函数转换消息格式
        normalized_messages = normalize_langgraph_messages(messages)

        # 提取最新消息作为需求
        if normalized_messages:
            requirement = normalized_messages[-1].get("content", "")
        else:
            requirement = input_data.get("requirement", "")

        # 使用抽取的辅助函数构建初始状态
        initial_state = build_initial_state(
            assistant_id=assistant_id,
            requirement=requirement,
            thread_id=thread_id,
            normalized_messages=normalized_messages
        )

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


@app.post("/threads")
async def create_thread():
    """
    创建新线程（兼容 LangGraph Cloud API）

    前端使用此端点创建新的对话线程
    """
    thread_id = f"thread_{datetime.now().timestamp()}"
    return {
        "thread_id": thread_id,
        "created_at": datetime.now().isoformat(),
        "metadata": {},
        "status": "idle"
    }


@app.get("/threads/{thread_id}")
async def get_thread(thread_id: str):
    """获取线程信息"""
    return {
        "thread_id": thread_id,
        "created_at": datetime.now().isoformat(),
        "metadata": {}
    }


@app.get("/threads/{thread_id}/state")
async def get_thread_state(thread_id: str, assistant_id: str = "skill-generation"):
    """
    获取线程状态（兼容 LangGraph SDK）

    前端在 stream 完成后会调用此端点获取最终状态
    🔥 P0改进：从 LangGraph Checkpoint 读取持久化状态
    """
    try:
        # 根据 assistant_id 选择对应的图
        if assistant_id == "skill-generation":
            graph = get_skill_generation_graph()
        elif assistant_id == "progressive-skill-generation":
            graph = get_progressive_skill_generation_graph()
        elif assistant_id == "skill-search":
            graph = get_skill_search_graph()
        elif assistant_id == "skill-detail":
            graph = get_skill_detail_graph()
        else:
            logger.warning(f"Unknown assistant_id: {assistant_id}, using skill-generation")
            graph = get_skill_generation_graph()

        # 🔥 从 checkpoint 读取状态
        config = {"configurable": {"thread_id": thread_id}}
        state_snapshot = graph.get_state(config)

        if state_snapshot is None or not state_snapshot.values:
            # 如果没有找到，返回空状态
            logger.warning(f"No checkpoint state found for thread {thread_id}")
            return {
                "values": {},
                "next": [],
                "config": config,
                "metadata": {},
                "created_at": datetime.now().isoformat(),
                "parent_config": None
            }

        # 返回 LangGraph 兼容的状态格式
        return {
            "values": state_snapshot.values,  # 从 checkpoint 读取的状态
            "next": state_snapshot.next,       # 下一步节点
            "config": config,
            "metadata": state_snapshot.metadata or {},
            "created_at": state_snapshot.created_at.isoformat() if hasattr(state_snapshot, 'created_at') else datetime.now().isoformat(),
            "parent_config": state_snapshot.parent_config
        }
    except Exception as e:
        logger.error(f"Get thread state error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/threads/search")
async def search_threads(request: Request):
    """
    搜索线程（兼容 LangGraph SDK）

    前端使用 client.threads.search() 时调用此端点
    🔥 P0改进：从 Checkpoint 查询持久化的线程列表
    """
    try:
        body = await request.json() if request.headers.get("content-type") == "application/json" else {}

        # 🔥 TODO: 实现从 SqliteSaver 查询线程列表
        # SqliteSaver 提供了 list() 方法，但需要遍历所有图的 checkpoint
        # 暂时返回空列表，未来可以通过查询 SQLite 数据库实现
        logger.info("Thread search requested, returning empty list (TODO: implement checkpoint query)")
        return []

    except Exception as e:
        logger.error(f"Search threads error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/threads/{thread_id}/history")
async def get_thread_history(thread_id: str, request: Request, assistant_id: str = "skill-generation"):
    """
    获取线程历史消息（兼容 LangGraph SDK）

    返回指定线程的完整对话历史
    LangGraph SDK 期望返回一个数组格式的历史记录
    🔥 P0改进：从 Checkpoint 读取历史状态快照
    """
    try:
        # 根据 assistant_id 选择对应的图
        if assistant_id == "skill-generation":
            graph = get_skill_generation_graph()
        elif assistant_id == "progressive-skill-generation":
            graph = get_progressive_skill_generation_graph()
        elif assistant_id == "skill-search":
            graph = get_skill_search_graph()
        elif assistant_id == "skill-detail":
            graph = get_skill_detail_graph()
        else:
            graph = get_skill_generation_graph()

        # 🔥 从 checkpoint 读取历史状态
        config = {"configurable": {"thread_id": thread_id}}

        # 使用 get_state_history() 获取所有历史快照
        history = []
        try:
            state_history = graph.get_state_history(config)
            for state_snapshot in state_history:
                history.append({
                    "values": state_snapshot.values,
                    "next": state_snapshot.next,
                    "config": state_snapshot.config,
                    "metadata": state_snapshot.metadata or {},
                    "parent_config": state_snapshot.parent_config,
                    "created_at": state_snapshot.created_at.isoformat() if hasattr(state_snapshot, 'created_at') else None
                })
        except Exception as e:
            logger.warning(f"Failed to get history for thread {thread_id}: {e}")

        return history

    except Exception as e:
        logger.error(f"Get thread history error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/threads/{thread_id}/resume")
async def resume_thread(thread_id: str, assistant_id: str = "skill-generation"):
    """
    恢复线程会话（新增功能）

    返回指定线程的最新状态和对话历史,用于服务重启后恢复对话
    🔥 P0新功能：利用 Checkpoint 实现会话恢复
    """
    try:
        # 根据 assistant_id 选择对应的图
        if assistant_id == "skill-generation":
            graph = get_skill_generation_graph()
        elif assistant_id == "progressive-skill-generation":
            graph = get_progressive_skill_generation_graph()
        elif assistant_id == "skill-search":
            graph = get_skill_search_graph()
        elif assistant_id == "skill-detail":
            graph = get_skill_detail_graph()
        else:
            logger.warning(f"Unknown assistant_id: {assistant_id}, using skill-generation")
            graph = get_skill_generation_graph()

        # 从 checkpoint 读取最新状态
        config = {"configurable": {"thread_id": thread_id}}
        state_snapshot = graph.get_state(config)

        if state_snapshot is None or not state_snapshot.values:
            logger.warning(f"No checkpoint found for thread {thread_id}")
            raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found or has no state")

        # 提取对话历史（从 messages 字段）
        messages = state_snapshot.values.get("messages", [])
        converted_messages = convert_from_langgraph_messages(messages) if messages else []

        # 构建恢复响应
        return {
            "thread_id": thread_id,
            "assistant_id": assistant_id,
            "status": "resumed",
            "messages": converted_messages,
            "state_summary": {
                "requirement": state_snapshot.values.get("requirement", ""),
                "retry_count": state_snapshot.values.get("retry_count", 0),
                "is_valid": state_snapshot.values.get("is_valid", None),
                "has_result": bool(state_snapshot.values.get("final_result")),
            },
            "next_nodes": state_snapshot.next,
            "created_at": state_snapshot.created_at.isoformat() if hasattr(state_snapshot, 'created_at') else datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume thread error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== RAG 专用端点 ====================

class RAGSearchRequest(BaseModel):
    """RAG搜索请求"""
    query: str = Field(..., description="搜索查询文本")
    top_k: int = Field(default=rag.DEFAULT_TOP_K, description="返回结果数量")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")


class RAGActionRecommendRequest(BaseModel):
    """Action推荐请求"""
    context: str = Field(..., description="上下文描述")
    top_k: int = Field(default=rag.RECOMMEND_TOP_K, description="推荐数量")


class RAGParameterRecommendRequest(BaseModel):
    """参数推荐请求"""
    action_type: str = Field(..., description="Action类型名称")
    skill_context: Optional[str] = Field(None, description="技能上下文")
    parameter_name: Optional[str] = Field(None, description="参数名称")


@app.post("/rag/search")
async def rag_search(request: RAGSearchRequest):
    """
    技能语义搜索

    根据自然语言查询搜索相似的技能配置
    """
    try:
        from orchestration.tools.rag_tools import get_rag_engine

        logger.info(f"RAG search: query='{request.query}', top_k={request.top_k}")

        engine = get_rag_engine()
        results = engine.search_skills(
            query=request.query,
            top_k=request.top_k,
            filters=request.filters,
            return_details=True
        )

        return {
            "success": True,
            "query": request.query,
            "results": results,
            "count": len(results)
        }

    except Exception as e:
        logger.error(f"RAG search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rag/recommend-actions")
async def rag_recommend_actions(request: RAGActionRecommendRequest):
    """
    Action类型智能推荐

    根据上下文描述推荐合适的Action类型
    """
    try:
        from orchestration.tools.rag_tools import get_rag_engine

        logger.info(f"Action recommendation: context='{request.context}'")

        engine = get_rag_engine()
        recommendations = engine.recommend_actions(
            context=request.context,
            top_k=request.top_k
        )

        return {
            "success": True,
            "context": request.context,
            "recommendations": recommendations,
            "count": len(recommendations)
        }

    except Exception as e:
        logger.error(f"Action recommendation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rag/recommend-parameters")
async def rag_recommend_parameters(request: RAGParameterRecommendRequest):
    """
    参数智能推荐（原Unity Inspector功能）

    为指定Action类型推荐合适的参数配置
    """
    try:
        from orchestration.tools.rag_tools import get_rag_engine

        logger.info(f"Parameter recommendation: action_type='{request.action_type}'")

        engine = get_rag_engine()

        # 搜索包含该Action类型的技能
        action_search_results = engine.search_actions(
            query=request.action_type,
            top_k=rag.PARAMETER_TOP_K
        )

        # 提取参数示例
        parameter_examples = []
        for result in action_search_results:
            if 'action_data' in result:
                action_data = result['action_data']
                if 'parameters' in action_data:
                    parameter_examples.append({
                        "action_type": result.get('actionType', request.action_type),
                        "parameters": action_data['parameters'],
                        "source_skill": result.get('skill_name', 'Unknown'),
                        "similarity": result.get('similarity', 0.0)
                    })

        return {
            "success": True,
            "action_type": request.action_type,
            "parameter_examples": parameter_examples,
            "count": len(parameter_examples)
        }

    except Exception as e:
        logger.error(f"Parameter recommendation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rag/index/rebuild")
async def rag_rebuild_index():
    """
    重建RAG索引

    重新索引所有技能配置文件
    """
    try:
        from orchestration.tools.rag_tools import get_rag_engine

        logger.info("Rebuilding RAG index...")

        engine = get_rag_engine()

        # 重建技能索引
        skill_result = engine.index_skills(force_rebuild=True)

        # 重建Action索引
        action_result = engine.index_actions(force_rebuild=True)

        # 重建结构化索引
        structured_result = engine.rebuild_structured_index(force=True)

        return {
            "success": True,
            "skill_index": skill_result,
            "action_index": action_result,
            "structured_index": structured_result,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Index rebuild error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rag/index/stats")
async def rag_index_stats():
    """
    获取RAG索引统计信息
    """
    try:
        from orchestration.tools.rag_tools import get_rag_engine
        import os

        engine = get_rag_engine()
        stats = engine.get_statistics()

        # 提取关键统计数据
        vector_stats = stats.get('vector_store', {})
        action_stats = stats.get('action_stats', {})

        # 计算索引大小（估算）
        persist_dir = vector_stats.get('persist_directory', '')
        index_size_mb = 0.0
        if persist_dir and os.path.exists(persist_dir):
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(persist_dir):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
            index_size_mb = total_size / (1024 * 1024)  # 转换为 MB

        # 返回前端期望的格式
        return {
            "total_skills": vector_stats.get('total_documents', 0),
            "total_actions": action_stats.get('total_actions', 0),
            "total_parameters": int(action_stats.get('avg_params_per_action', 0) * action_stats.get('total_actions', 0)),
            "index_size_mb": round(index_size_mb, 2)
        }

    except Exception as e:
        logger.error(f"Stats retrieval error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/rag/cache")
async def rag_clear_cache():
    """
    清空RAG查询缓存
    """
    try:
        from orchestration.tools.rag_tools import get_rag_engine

        engine = get_rag_engine()

        # 清空查询缓存
        if hasattr(engine, '_query_cache') and engine._query_cache is not None:
            cache_size = len(engine._query_cache)
            engine._query_cache.clear()
            logger.info(f"Cleared {cache_size} cached queries")
        else:
            cache_size = 0
            logger.info("Query cache is disabled or empty")

        return {
            "success": True,
            "cleared_entries": cache_size,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Cache clear error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rag/health")
async def rag_health_check():
    """
    RAG服务健康检查

    与 webui/src/app/rag/page.tsx HealthStatus 接口对接
    """
    try:
        from orchestration.tools.rag_tools import get_rag_engine

        engine = get_rag_engine()
        stats = engine.get_statistics()

        # 提取嵌套统计数据
        vector_stats = stats.get('vector_store', {})
        action_stats = stats.get('action_stats', {})

        return {
            "status": "healthy",
            "skill_count": vector_stats.get('total_documents', 0),
            "action_count": action_stats.get('total_actions', 0),
            "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    except Exception as e:
        logger.warning(f"RAG health check failed: {e}")
        return {
            "status": "unhealthy",
            "skill_count": 0,
            "action_count": 0,
            "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }


# ==================== 主函数 ====================

def kill_process_on_port(port: int) -> bool:
    """
    杀掉占用指定端口的进程

    Args:
        port: 端口号

    Returns:
        是否成功杀掉进程
    """
    try:
        import subprocess
        import re

        # 在Windows上查找占用端口的进程
        if sys.platform == "win32":
            # 使用 netstat 查找端口
            result = subprocess.run(
                ['netstat', '-ano'],
                capture_output=True,
                text=True,
                timeout=5
            )

            # 解析输出，查找监听该端口的进程
            for line in result.stdout.splitlines():
                if f':{port}' in line and 'LISTENING' in line:
                    # 提取PID（最后一列）
                    parts = line.split()
                    if parts:
                        pid = parts[-1]
                        logger.info(f"🔍 Found process {pid} using port {port}")

                        # 杀掉进程
                        kill_result = subprocess.run(
                            ['taskkill', '/F', '/PID', pid],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )

                        if kill_result.returncode == 0:
                            logger.info(f"✅ Successfully killed process {pid}")
                            return True
                        else:
                            logger.warning(f"⚠️  Failed to kill process {pid}: {kill_result.stderr}")

            return False
        else:
            # Linux/Mac 使用 lsof
            result = subprocess.run(
                ['lsof', '-ti', f':{port}'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.stdout.strip():
                pid = result.stdout.strip()
                logger.info(f"🔍 Found process {pid} using port {port}")

                subprocess.run(['kill', '-9', pid], timeout=5)
                logger.info(f"✅ Successfully killed process {pid}")
                return True

            return False

    except Exception as e:
        logger.error(f"❌ Error killing process on port {port}: {e}")
        return False


def main():
    """启动服务器"""
    # 使用配置模块（支持环境变量覆盖）
    host = server.LANGGRAPH_HOST
    port = server.LANGGRAPH_PORT

    logger.info(f"Starting LangGraph server on {host}:{port}")

    # 检查端口是否被占用
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()

    if result == 0:
        logger.warning(f"⚠️  Port {port} is already in use!")
        logger.info(f"🔄 Attempting to kill existing process...")

        if kill_process_on_port(port):
            logger.info(f"✅ Port {port} is now free, starting server...")
            # 等待端口完全释放
            import time
            time.sleep(timeout.PORT_RELEASE_WAIT)
        else:
            logger.error(f"❌ Failed to free port {port}")
            logger.warning(f"    To manually find the process: netstat -ano | findstr :{port}")
            logger.warning(f"    To manually kill it: taskkill /F /PID <PID>")
            sys.exit(1)

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()

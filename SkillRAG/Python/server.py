"""
FastAPI服务器
提供RESTful API接口供Unity编辑器调用
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager

import yaml
import uvicorn
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from rag_engine import RAGEngine

# 配置日志
def setup_logging(config: dict):
    """配置日志系统"""
    log_config = config.get('logging', {})
    log_level = log_config.get('level', 'INFO')
    log_file = log_config.get('file', '../Data/rag_server.log')

    # 确保日志目录存在
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # 配置logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

# 加载配置
config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

setup_logging(config)
logger = logging.getLogger(__name__)

# 全局RAG引擎实例
rag_engine: Optional[RAGEngine] = None
file_observer: Optional[Observer] = None


# 文件监听器
class SkillFileHandler(FileSystemEventHandler):
    """技能文件变化监听器"""

    def __init__(self, rag_engine: RAGEngine):
        self.rag_engine = rag_engine
        self.logger = logging.getLogger(__name__)

    def on_modified(self, event):
        """文件修改时触发"""
        if event.is_directory:
            return

        if event.src_path.endswith('.json'):
            self.logger.info(f"Detected skill file change: {event.src_path}")
            # 更新索引
            self.rag_engine.update_skill(event.src_path)

    def on_created(self, event):
        """新文件创建时触发"""
        if event.is_directory:
            return

        if event.src_path.endswith('.json'):
            self.logger.info(f"Detected new skill file: {event.src_path}")
            # 更新索引
            self.rag_engine.update_skill(event.src_path)


# 应用生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动和关闭时的处理"""
    global rag_engine, file_observer

    # 启动时初始化
    logger.info("=" * 60)
    logger.info("Starting SkillRAG Server")
    logger.info("=" * 60)

    # 初始化RAG引擎
    logger.info("Initializing RAG Engine...")
    rag_engine = RAGEngine(config)

    # 自动索引技能
    logger.info("Indexing skills...")
    index_result = rag_engine.index_skills(force_rebuild=False)
    logger.info(f"Skill index result: {index_result}")

    # 自动索引Actions
    logger.info("Indexing actions...")
    action_index_result = rag_engine.index_actions(force_rebuild=False)
    logger.info(f"Action index result: {action_index_result}")

    # 启动文件监听
    watch_enabled = config.get('skill_indexer', {}).get('watch_enabled', True)
    if watch_enabled:
        skills_dir = config.get('skill_indexer', {}).get('skills_directory')
        if skills_dir and os.path.exists(skills_dir):
            event_handler = SkillFileHandler(rag_engine)
            file_observer = Observer()
            file_observer.schedule(event_handler, skills_dir, recursive=False)
            file_observer.start()
            logger.info(f"File watcher started for: {skills_dir}")

    logger.info("SkillRAG Server is ready!")
    logger.info(f"Access API docs at: http://{config['server']['host']}:{config['server']['port']}/docs")

    yield  # 服务器运行期间

    # 关闭时清理
    logger.info("Shutting down SkillRAG Server...")
    if file_observer:
        file_observer.stop()
        file_observer.join()
        logger.info("File watcher stopped")


# 创建FastAPI应用
app = FastAPI(
    title="SkillRAG API",
    description="Unity技能系统RAG服务，提供技能搜索和智能推荐功能",
    version="1.0.0",
    lifespan=lifespan
)

# 添加CORS中间件（允许Unity编辑器跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ Pydantic模型 ============

class SearchRequest(BaseModel):
    """搜索请求"""
    query: str = Field(..., description="搜索查询文本")
    top_k: Optional[int] = Field(None, description="返回结果数量")
    filters: Optional[Dict[str, Any]] = Field(None, description="元数据过滤条件")
    return_details: bool = Field(False, description="是否返回详细信息")


class SearchResponse(BaseModel):
    """搜索响应"""
    results: List[Dict[str, Any]] = Field(..., description="搜索结果列表")
    query: str = Field(..., description="原始查询")
    count: int = Field(..., description="结果数量")
    timestamp: str = Field(..., description="查询时间戳")


class RecommendRequest(BaseModel):
    """Action推荐请求"""
    context: str = Field(..., description="上下文描述")
    top_k: int = Field(3, description="推荐数量")


class RecommendResponse(BaseModel):
    """Action推荐响应"""
    recommendations: List[Dict[str, Any]] = Field(..., description="推荐的Action列表")
    context: str = Field(..., description="原始上下文")
    count: int = Field(..., description="推荐数量")


class IndexRequest(BaseModel):
    """索引请求"""
    force_rebuild: bool = Field(False, description="是否强制重建索引")


class IndexResponse(BaseModel):
    """索引响应"""
    status: str = Field(..., description="索引状态")
    count: int = Field(..., description="索引的技能数量")
    elapsed_time: Optional[float] = Field(None, description="耗时（秒）")
    message: Optional[str] = Field(None, description="额外信息")


# ============ API路由 ============

@app.get("/", tags=["System"])
async def root():
    """根路径，返回服务信息"""
    return {
        "service": "SkillRAG API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health", tags=["System"])
async def health_check():
    """健康检查"""
    if rag_engine is None:
        raise HTTPException(status_code=503, detail="RAG Engine not initialized")

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/search", response_model=SearchResponse, tags=["RAG"])
async def search_skills(request: SearchRequest):
    """
    搜索技能

    根据查询文本搜索相似的技能，支持中英文语义搜索。
    """
    if rag_engine is None:
        raise HTTPException(status_code=503, detail="RAG Engine not initialized")

    try:
        results = rag_engine.search_skills(
            query=request.query,
            top_k=request.top_k,
            filters=request.filters,
            return_details=request.return_details
        )

        return SearchResponse(
            results=results,
            query=request.query,
            count=len(results),
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search", response_model=SearchResponse, tags=["RAG"])
async def search_skills_get(
    q: str = Query(..., description="搜索查询文本"),
    top_k: Optional[int] = Query(None, description="返回结果数量"),
    details: bool = Query(False, description="是否返回详细信息")
):
    """
    搜索技能（GET方法）

    简化版搜索接口，适用于快速查询。
    """
    request = SearchRequest(
        query=q,
        top_k=top_k,
        return_details=details
    )
    return await search_skills(request)


@app.get("/skill/{skill_id}", tags=["Skills"])
async def get_skill_by_id(skill_id: str):
    """
    根据skill_id获取技能详细信息

    返回技能的完整数据，包括所有tracks和actions。
    """
    if rag_engine is None:
        raise HTTPException(status_code=503, detail="RAG Engine not initialized")

    try:
        skill_data = rag_engine.get_skill_by_id(skill_id)

        if skill_data is None:
            raise HTTPException(status_code=404, detail=f"Skill not found: {skill_id}")

        return {
            "skill": skill_data,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting skill {skill_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/recommend", response_model=RecommendResponse, tags=["RAG"])
async def recommend_actions(request: RecommendRequest):
    """
    推荐Action

    根据上下文描述推荐合适的Action类型及参数示例。
    """
    if rag_engine is None:
        raise HTTPException(status_code=503, detail="RAG Engine not initialized")

    try:
        recommendations = rag_engine.recommend_actions(
            context=request.context,
            top_k=request.top_k
        )

        return RecommendResponse(
            recommendations=recommendations,
            context=request.context,
            count=len(recommendations)
        )

    except Exception as e:
        logger.error(f"Recommendation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/index", response_model=IndexResponse, tags=["Management"])
async def index_skills(request: IndexRequest = Body(default=IndexRequest())):
    """
    索引技能

    扫描技能目录并重建索引。可选择强制重建或仅更新变化的文件。
    """
    if rag_engine is None:
        raise HTTPException(status_code=503, detail="RAG Engine not initialized")

    try:
        result = rag_engine.index_skills(force_rebuild=request.force_rebuild)

        return IndexResponse(
            status=result.get('status', 'unknown'),
            count=result.get('count', 0),
            elapsed_time=result.get('elapsed_time'),
            message=result.get('message')
        )

    except Exception as e:
        logger.error(f"Indexing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats", tags=["Management"])
async def get_statistics():
    """
    获取统计信息

    返回RAG引擎的运行统计，包括查询次数、缓存命中率等。
    """
    if rag_engine is None:
        raise HTTPException(status_code=503, detail="RAG Engine not initialized")

    try:
        stats = rag_engine.get_statistics()
        return {
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clear-cache", tags=["Management"])
async def clear_cache():
    """
    清空缓存

    清空查询缓存和嵌入缓存，强制重新计算。
    """
    if rag_engine is None:
        raise HTTPException(status_code=503, detail="RAG Engine not initialized")

    try:
        rag_engine.embedding_generator.clear_cache()
        if rag_engine._query_cache is not None:
            rag_engine._query_cache.clear()

        return {
            "status": "success",
            "message": "All caches cleared",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error clearing cache: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rebuild_index", tags=["Management"])
async def rebuild_all_indexes():
    """
    重建所有索引

    同时重建技能索引和Action索引。
    用于Unity描述管理器一键发布流程。
    """
    if rag_engine is None:
        raise HTTPException(status_code=503, detail="RAG Engine not initialized")

    try:
        logger.info("Starting rebuild of all indexes...")

        # 重建技能索引
        logger.info("Rebuilding skill index...")
        skill_result = rag_engine.index_skills(force_rebuild=True)
        skill_count = skill_result.get('count', 0)

        # 重建Action索引
        logger.info("Rebuilding action index...")
        action_result = rag_engine.index_actions(force_rebuild=True)
        action_count = action_result.get('count', 0)

        logger.info(f"Rebuild complete: {action_count} actions, {skill_count} skills")

        return {
            "status": "ok",
            "message": f"Rebuilt {action_count} actions and {skill_count} skills",
            "action_count": action_count,
            "skill_count": skill_count,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error rebuilding indexes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============ Action相关API路由 ============

@app.post("/index_actions", response_model=IndexResponse, tags=["Action Management"])
async def index_actions(request: IndexRequest = Body(default=IndexRequest())):
    """
    索引Action脚本

    扫描Unity导出的action_definitions.json并构建向量索引。
    """
    if rag_engine is None:
        raise HTTPException(status_code=503, detail="RAG Engine not initialized")

    try:
        result = rag_engine.index_actions(force_rebuild=request.force_rebuild)

        return IndexResponse(
            status=result.get('status', 'unknown'),
            count=result.get('count', 0),
            elapsed_time=result.get('elapsed_time'),
            message=result.get('message')
        )

    except Exception as e:
        logger.error(f"Action indexing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search_actions", response_model=SearchResponse, tags=["Action RAG"])
async def search_actions_post(request: SearchRequest):
    """
    搜索Action类型

    根据查询文本搜索相似的Action类型，支持中英文语义搜索。
    例如："造成伤害" -> DamageAction, "移动角色" -> MovementAction
    """
    if rag_engine is None:
        raise HTTPException(status_code=503, detail="RAG Engine not initialized")

    try:
        results = rag_engine.search_actions(
            query=request.query,
            top_k=request.top_k,
            category_filter=request.filters.get('category') if request.filters else None,
            return_details=request.return_details
        )

        return SearchResponse(
            results=results,
            query=request.query,
            count=len(results),
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"Action search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search_actions", response_model=SearchResponse, tags=["Action RAG"])
async def search_actions_get(
    q: str = Query(..., description="搜索查询文本"),
    top_k: Optional[int] = Query(None, description="返回结果数量"),
    category: Optional[str] = Query(None, description="按分类过滤"),
    details: bool = Query(False, description="是否返回详细参数信息")
):
    """
    搜索Action类型（GET方法）

    简化版Action搜索接口，适用于快速查询。
    """
    filters = {"category": category} if category else None
    request = SearchRequest(
        query=q,
        top_k=top_k,
        filters=filters,
        return_details=details
    )
    return await search_actions_post(request)


@app.get("/action/{action_type}", tags=["Actions"])
async def get_action_by_type(action_type: str):
    """
    根据Action类型名获取详细信息

    返回Action的完整定义，包括所有参数、约束、默认值等。
    例如：/action/DamageAction
    """
    if rag_engine is None:
        raise HTTPException(status_code=503, detail="RAG Engine not initialized")

    try:
        action_data = rag_engine.get_action_by_type(action_type)

        if action_data is None:
            raise HTTPException(status_code=404, detail=f"Action not found: {action_type}")

        return {
            "action": action_data,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting action {action_type}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/actions/categories", tags=["Actions"])
async def get_action_categories():
    """
    获取所有Action分类

    返回系统中所有可用的Action分类列表。
    """
    if rag_engine is None:
        raise HTTPException(status_code=503, detail="RAG Engine not initialized")

    try:
        categories = rag_engine.get_action_categories()

        return {
            "categories": categories,
            "count": len(categories),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting action categories: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/actions/category/{category}", tags=["Actions"])
async def get_actions_by_category(category: str):
    """
    获取指定分类的所有Action

    返回属于某个分类的所有Action列表。
    例如：/actions/category/Damage
    """
    if rag_engine is None:
        raise HTTPException(status_code=503, detail="RAG Engine not initialized")

    try:
        actions = rag_engine.get_actions_by_category(category)

        return {
            "category": category,
            "actions": actions,
            "count": len(actions),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting actions for category {category}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============ 主函数 ============

def main():
    """启动服务器"""
    server_config = config.get('server', {})
    host = server_config.get('host', '127.0.0.1')
    port = server_config.get('port', 8765)
    reload = server_config.get('reload', False)

    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()

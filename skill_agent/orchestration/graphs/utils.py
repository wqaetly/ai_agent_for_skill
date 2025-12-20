"""
图构建辅助工具
提供环境检测和 checkpointer 创建功能
"""

import os
import logging
from typing import Optional
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

logger = logging.getLogger(__name__)

# PostgreSQL 连接配置
POSTGRES_URI = os.getenv(
    "POSTGRES_URI",
    "postgresql://postgres:postgres@localhost:5432/skill_agent?sslmode=disable"
)

# 全局 checkpointer 实例和连接池
_checkpointer: Optional[AsyncPostgresSaver] = None
_pool: Optional[AsyncConnectionPool] = None


def is_langgraph_api_deployment() -> bool:
    """
    检测是否在 LangGraph API 部署环境中运行

    LangGraph API 会自动管理持久化，不需要也不允许使用自定义 checkpointer

    Returns:
        True 如果在 LangGraph API 部署环境，False 如果在本地开发环境
    """
    # LangGraph API 部署环境通常会设置特定的环境变量
    # 例如：LANGGRAPH_API, LANGGRAPH_CLOUD, LANGSMITH_API_KEY（配合云环境）

    # 方法1：检查是否有 LangGraph API 特定的环境变量
    if os.getenv("LANGGRAPH_API"):
        return True

    # 方法2：检查是否在 langgraph dev 命令中运行（langgraph dev 会设置环境变量）
    if os.getenv("LANGGRAPH_DEV"):
        return True

    # 方法3：检查是否存在 graphs.py 文件（LangGraph API 要求使用 graphs.py）
    # 同时检查当前目录是否是通过 langgraph 命令启动的
    if os.path.exists("./graphs.py") and os.getenv("LANGGRAPH_HOST"):
        return True

    return False


def get_checkpointer(checkpoint_db: str = "") -> Optional[AsyncPostgresSaver]:
    """
    根据运行环境决定是否创建 checkpointer

    Args:
        checkpoint_db: 已弃用参数，保留兼容性

    Returns:
        AsyncPostgresSaver 实例（本地开发环境）或 None（部署环境）
    """
    global _checkpointer
    
    if is_langgraph_api_deployment():
        logger.info("检测到 LangGraph API 部署环境，跳过自定义 checkpointer")
        return None

    # 返回全局 checkpointer 实例（必须先调用 init_checkpointer）
    if _checkpointer is None:
        logger.warning("Checkpointer 尚未初始化，请先调用 init_checkpointer()")
    return _checkpointer


async def init_checkpointer() -> AsyncPostgresSaver:
    """
    初始化 checkpointer（需要在应用启动时调用）
    创建必要的数据库表
    """
    global _checkpointer, _pool
    
    if _checkpointer is not None:
        return _checkpointer
    
    # 创建连接池
    # 注意：setup() 使用 CREATE INDEX CONCURRENTLY，需要 autocommit 模式
    # 参考：https://github.com/langchain-ai/langgraph/issues/2887
    _pool = AsyncConnectionPool(
        conninfo=POSTGRES_URI,
        max_size=20,
        open=False,  # 延迟打开
        kwargs={"autocommit": True}  # 启用 autocommit 以支持 CREATE INDEX CONCURRENTLY
    )
    await _pool.open()
    
    # 创建 checkpointer
    _checkpointer = AsyncPostgresSaver(_pool)
    
    # 创建必要的表（现在可以正常执行 CREATE INDEX CONCURRENTLY）
    await _checkpointer.setup()
    
    logger.info("✅ PostgreSQL checkpointer 初始化完成")
    return _checkpointer


async def close_checkpointer():
    """关闭 checkpointer 连接"""
    global _checkpointer, _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
    _checkpointer = None
    logger.info("PostgreSQL checkpointer 已关闭")

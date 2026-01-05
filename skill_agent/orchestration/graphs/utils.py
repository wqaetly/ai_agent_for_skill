"""
图构建辅助工具
提供环境检测和 checkpointer 创建功能
"""

import os
import logging
from typing import Optional
from langgraph.checkpoint.memory import MemorySaver

logger = logging.getLogger(__name__)

# 全局 checkpointer 实例
_checkpointer: Optional[MemorySaver] = None


def is_langgraph_api_deployment() -> bool:
    """
    检测是否在 LangGraph API 部署环境中运行

    LangGraph API 会自动管理持久化，不需要也不允许使用自定义 checkpointer

    Returns:
        True 如果在 LangGraph API 部署环境，False 如果在本地开发环境
    """
    if os.getenv("LANGGRAPH_API"):
        return True
    if os.getenv("LANGGRAPH_DEV"):
        return True
    if os.path.exists("./graphs.py") and os.getenv("LANGGRAPH_HOST"):
        return True
    return False


def get_checkpointer(checkpoint_db: str = "") -> Optional[MemorySaver]:
    """
    根据运行环境决定是否创建 checkpointer

    Args:
        checkpoint_db: 已弃用参数，保留兼容性

    Returns:
        MemorySaver 实例（本地开发环境）或 None（部署环境）
    """
    global _checkpointer
    
    if is_langgraph_api_deployment():
        logger.info("检测到 LangGraph API 部署环境，跳过自定义 checkpointer")
        return None

    if _checkpointer is None:
        logger.warning("Checkpointer 尚未初始化，请先调用 init_checkpointer()")
    return _checkpointer


async def init_checkpointer() -> MemorySaver:
    """
    初始化 checkpointer（需要在应用启动时调用）
    使用内存存储，无需外部数据库
    """
    global _checkpointer
    
    if _checkpointer is not None:
        return _checkpointer
    
    _checkpointer = MemorySaver()
    logger.info("✅ MemorySaver checkpointer 初始化完成")
    return _checkpointer


async def close_checkpointer():
    """关闭 checkpointer（内存存储无需特殊清理）"""
    global _checkpointer
    _checkpointer = None
    logger.info("Checkpointer 已关闭")

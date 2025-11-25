"""
图构建辅助工具
提供环境检测和 checkpointer 创建功能
"""

import os
import sqlite3
import logging
from typing import Optional
from langgraph.checkpoint.sqlite import SqliteSaver

logger = logging.getLogger(__name__)


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


def get_checkpointer(checkpoint_db: str) -> Optional[SqliteSaver]:
    """
    根据运行环境决定是否创建 checkpointer

    Args:
        checkpoint_db: SQLite 数据库文件路径

    Returns:
        SqliteSaver 实例（本地开发环境）或 None（部署环境）
    """
    if is_langgraph_api_deployment():
        logger.info("检测到 LangGraph API 部署环境，跳过自定义 checkpointer")
        return None

    # 本地开发环境：创建并返回 SqliteSaver
    os.makedirs(os.path.dirname(checkpoint_db), exist_ok=True)
    conn = sqlite3.connect(checkpoint_db, check_same_thread=False)
    checkpointer = SqliteSaver(conn)
    checkpointer.setup()
    logger.info(f"本地开发环境：使用 checkpoint 数据库 {checkpoint_db}")
    return checkpointer

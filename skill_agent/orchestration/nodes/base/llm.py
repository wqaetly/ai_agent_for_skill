"""
LLM 初始化模块
提供 LangChain ChatOpenAI 和 OpenAI SDK 客户端的统一初始化
"""

import logging
import os
from typing import Optional

from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


def get_llm(
    model: str = None,
    temperature: float = None,
    streaming: bool = None
) -> ChatOpenAI:
    """
    获取 LLM 实例（使用 LangChain ChatOpenAI 兼容 DeepSeek）

    Args:
        model: 模型名称（默认从配置读取）
        temperature: 温度参数（默认从配置读取）
        streaming: 是否启用流式输出（默认从配置读取）

    Returns:
        ChatOpenAI 实例
    """
    from ...config import get_skill_gen_config
    
    config = get_skill_gen_config().llm

    model = model or config.model
    temperature = temperature if temperature is not None else config.temperature
    streaming = streaming if streaming is not None else config.streaming

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY not set")

    logger.info(f"Init LLM: model={model}, timeout={config.timeout}s, streaming={streaming}")

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=api_key,
        base_url="https://api.deepseek.com/v1",
        timeout=config.timeout,
        max_retries=config.max_retries,
        streaming=streaming,
        http_client=None,
    )


def get_openai_client():
    """
    获取 OpenAI SDK 客户端（用于直接调用 DeepSeek API 以支持 reasoning_content 流式输出）

    Returns:
        OpenAI 客户端实例
    """
    from openai import OpenAI
    import httpx
    from ...config import get_skill_gen_config

    config = get_skill_gen_config().llm

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY not set")

    logger.info(f"Init OpenAI SDK: timeout={config.timeout}s, max_retries={config.max_retries}")

    return OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
        timeout=httpx.Timeout(config.timeout, connect=30.0),
        max_retries=config.max_retries
    )

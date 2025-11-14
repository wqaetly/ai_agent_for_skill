"""
JSON 工具模块
提供从 Markdown 格式文本中提取 JSON 的功能
"""

import re
import json
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def extract_json_from_markdown(text: str) -> Optional[str]:
    """
    从 Markdown 格式的文本中提取 JSON 代码块

    Args:
        text: 可能包含 Markdown 代码块的文本

    Returns:
        提取的 JSON 字符串，如果未找到则返回原文本
    """
    # 匹配 ```json ... ``` 代码块
    pattern = r'```json\s*\n(.*?)\n```'
    matches = re.findall(pattern, text, re.DOTALL)

    if matches:
        logger.debug(f"从 ```json 代码块中提取到 {len(matches)} 个 JSON")
        # 返回第一个匹配的 JSON 内容
        return matches[0].strip()

    # 如果没有找到 json 代码块，尝试匹配 ``` ... ``` (无语言标记)
    pattern = r'```\s*\n(.*?)\n```'
    matches = re.findall(pattern, text, re.DOTALL)

    if matches:
        logger.debug(f"从 ``` 代码块中找到 {len(matches)} 个候选块，尝试验证 JSON")
        # 检查是否是有效 JSON
        for match in matches:
            content = match.strip()
            try:
                json.loads(content)
                logger.debug("找到有效的 JSON 代码块")
                return content
            except json.JSONDecodeError:
                continue

    # 如果都没找到，返回原文本
    logger.debug("未找到 Markdown 代码块，返回原文本")
    return text.strip()

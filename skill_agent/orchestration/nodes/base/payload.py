"""
Payload 转换模块
提供 payload 规范化和类型转换功能
"""

import json
from typing import Any


def prepare_payload_text(payload: Any) -> str:
    """
    将异构的 payload（AIMessage/BaseModel/str/dict）规范化为原始文本

    支持多种输入类型：
    - str: 直接返回
    - AIMessage/有 content 属性的对象: 返回 content
    - Pydantic Model: 转换为 JSON 字符串
    - dict/list: 序列化为 JSON

    Args:
        payload: 任意类型的输入

    Returns:
        规范化后的文本字符串
    """
    if payload is None:
        return ""

    if isinstance(payload, str):
        return payload

    if hasattr(payload, "content"):
        content = payload.content
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict):
                    text_parts.append(item.get('text', ''))
                elif isinstance(item, str):
                    text_parts.append(item)
            if text_parts:
                return ''.join(text_parts)
        elif isinstance(content, dict):
            return content.get('text', content.get('content', json.dumps(content, ensure_ascii=False)))
        return str(content)

    if hasattr(payload, "model_dump_json"):
        try:
            return payload.model_dump_json()
        except Exception:
            pass

    if hasattr(payload, "model_dump"):
        try:
            return json.dumps(payload.model_dump(), ensure_ascii=False)
        except Exception:
            pass

    if isinstance(payload, (dict, list)):
        return json.dumps(payload, ensure_ascii=False)

    return str(payload)


def safe_int(value: Any, default: int = 0, min_value: int = 0) -> int:
    """
    安全地将值转换为整数

    支持：str, int, float, Decimal 等类型
    容错：无效值返回 default，负数钳制到 min_value

    Args:
        value: 待转换的值
        default: 转换失败时的默认值
        min_value: 最小值（用于钳制负数）

    Returns:
        整数值
    """
    if value is None:
        return default

    try:
        result = int(value)
    except (ValueError, TypeError):
        try:
            result = int(float(value))
        except (ValueError, TypeError):
            return default

    return max(result, min_value)

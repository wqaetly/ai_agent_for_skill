"""
JSON 工具模块
提供从 Markdown 格式文本中提取 JSON 的功能，包含多层容错机制
"""

import re
import json
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class JSONExtractionError(Exception):
    """JSON 提取失败异常"""
    
    def __init__(self, message: str, original_text: str = "", attempted_fixes: int = 0):
        self.original_text = original_text
        self.attempted_fixes = attempted_fixes
        super().__init__(message)
    
    def __str__(self):
        base_msg = super().__str__()
        preview = self.original_text[:200] + "..." if len(self.original_text) > 200 else self.original_text
        return f"{base_msg}\n原文预览: {preview}"


def _fix_common_json_errors(json_str: str) -> str:
    """
    修复 LLM 生成 JSON 中的常见格式错误

    Args:
        json_str: 可能包含格式错误的 JSON 字符串

    Returns:
        修复后的 JSON 字符串
    """
    if not json_str:
        return json_str

    # 1. 移除 BOM 和不可见字符
    json_str = json_str.strip('\ufeff\u200b\u200c\u200d')

    # 2. 修复尾随逗号 (trailing comma)
    # 匹配 }, ] 或 " 前的逗号
    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)

    # 3. 修复单引号（替换为双引号，但要小心字符串内容）
    # 只处理明显是键名的情况
    json_str = re.sub(r"'(\w+)'(\s*:)", r'"\1"\2', json_str)

    # 4. 修复未转义的换行符（在字符串值内）
    # 这个比较复杂，简单处理：替换字符串内的实际换行为 \n
    def escape_newlines_in_strings(match):
        content = match.group(1)
        # 替换实际换行为转义换行
        content = content.replace('\n', '\\n').replace('\r', '\\r')
        return f'"{content}"'

    # 匹配双引号字符串（非贪婪）
    json_str = re.sub(r'"([^"]*(?:\\"[^"]*)*)"', escape_newlines_in_strings, json_str)

    # 5. 修复注释（JSON 不支持注释）
    # 移除 // 单行注释
    json_str = re.sub(r'//[^\n]*\n', '\n', json_str)
    # 移除 /* */ 多行注释
    json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)

    return json_str


def _find_json_boundaries(text: str) -> Optional[str]:
    """
    通过括号匹配找到 JSON 对象/数组的边界

    Args:
        text: 可能包含 JSON 的文本

    Returns:
        提取的 JSON 字符串，如果未找到则返回 None
    """
    # 找到第一个 { 或 [
    start_idx = -1
    start_char = None
    for i, char in enumerate(text):
        if char == '{':
            start_idx = i
            start_char = '{'
            break
        elif char == '[':
            start_idx = i
            start_char = '['
            break

    if start_idx == -1:
        return None

    # 匹配对应的结束括号
    end_char = '}' if start_char == '{' else ']'
    depth = 0
    in_string = False
    escape_next = False

    for i in range(start_idx, len(text)):
        char = text[i]

        if escape_next:
            escape_next = False
            continue

        if char == '\\':
            escape_next = True
            continue

        if char == '"' and not escape_next:
            in_string = not in_string
            continue

        if in_string:
            continue

        if char == start_char:
            depth += 1
        elif char == end_char:
            depth -= 1
            if depth == 0:
                return text[start_idx:i + 1]

    return None


def extract_json_from_markdown(text: str, raise_on_failure: bool = False) -> str:
    """
    从 Markdown 格式的文本中提取 JSON 代码块（多层容错）

    容错策略：
    1. 优先匹配 ```json 代码块
    2. 尝试匹配无语言标记的 ``` 代码块
    3. 通过括号匹配找到 JSON 边界
    4. 修复常见 JSON 格式错误
    5. 最后返回原文本或抛出异常

    Args:
        text: 可能包含 Markdown 代码块的文本
        raise_on_failure: 如果为 True，当所有策略都失败时抛出 JSONExtractionError；
                          如果为 False（默认），返回原文本以保持向后兼容

    Returns:
        提取的 JSON 字符串

    Raises:
        JSONExtractionError: 当 raise_on_failure=True 且无法提取有效 JSON 时
    """
    if not text:
        if raise_on_failure:
            raise JSONExtractionError("输入文本为空", original_text="", attempted_fixes=0)
        return text

    text = text.strip()

    # 策略1: 匹配 ```json ... ``` 代码块
    pattern = r'```json\s*\n?(.*?)\n?```'
    matches = re.findall(pattern, text, re.DOTALL)

    if matches:
        logger.debug(f"从 ```json 代码块中提取到 {len(matches)} 个 JSON")
        extracted = matches[0].strip()
        # 尝试验证，如果失败则修复
        try:
            json.loads(extracted)
            return extracted
        except json.JSONDecodeError:
            fixed = _fix_common_json_errors(extracted)
            try:
                json.loads(fixed)
                logger.info("JSON 格式错误已自动修复")
                return fixed
            except json.JSONDecodeError:
                pass  # 继续尝试其他策略

    # 策略2: 匹配 ``` ... ``` (无语言标记)
    pattern = r'```\s*\n?(.*?)\n?```'
    matches = re.findall(pattern, text, re.DOTALL)

    if matches:
        logger.debug(f"从 ``` 代码块中找到 {len(matches)} 个候选块")
        for match in matches:
            content = match.strip()
            # 先尝试直接解析
            try:
                json.loads(content)
                logger.debug("找到有效的 JSON 代码块")
                return content
            except json.JSONDecodeError:
                # 尝试修复
                fixed = _fix_common_json_errors(content)
                try:
                    json.loads(fixed)
                    logger.info("JSON 格式错误已自动修复")
                    return fixed
                except json.JSONDecodeError:
                    continue

    # 策略3: 通过括号匹配找到 JSON 边界（处理代码块外有额外文本的情况）
    json_candidate = _find_json_boundaries(text)
    if json_candidate:
        try:
            json.loads(json_candidate)
            logger.debug("通过括号匹配找到有效 JSON")
            return json_candidate
        except json.JSONDecodeError:
            fixed = _fix_common_json_errors(json_candidate)
            try:
                json.loads(fixed)
                logger.info("通过括号匹配找到 JSON 并修复格式错误")
                return fixed
            except json.JSONDecodeError:
                pass

    # 策略4: 直接尝试解析原文本
    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        # 最后尝试修复原文本
        fixed = _fix_common_json_errors(text)
        try:
            json.loads(fixed)
            logger.info("原文本 JSON 格式错误已自动修复")
            return fixed
        except json.JSONDecodeError as e:
            pass

    # 所有策略都失败
    logger.warning("未能提取有效 JSON，所有策略均失败")
    if raise_on_failure:
        raise JSONExtractionError(
            "无法从文本中提取有效的 JSON，已尝试所有容错策略",
            original_text=text,
            attempted_fixes=4  # 4种策略
        )
    # 返回原文本以保持向后兼容（让上层处理错误）
    return text

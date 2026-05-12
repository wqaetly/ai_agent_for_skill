"""
JSON 工具模块
提供从 Markdown 格式文本中提取 JSON 的功能，包含多层容错机制

增强版：
- 支持 json5 宽松解析（处理尾随逗号、注释等）
- 更多格式修复策略（缺失逗号、浮点数转整数等）
- 针对 LLM 输出特性优化
"""

import re
import json
from typing import Optional, Tuple
import logging

# 尝试导入 json5（宽松 JSON 解析器）
try:
    import json5
    HAS_JSON5 = True
except ImportError:
    HAS_JSON5 = False

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

    # 2. 移除可能的 markdown 代码块标记（LLM 有时会在 json_mode 下仍然输出）
    json_str = re.sub(r'^```(?:json)?\s*\n?', '', json_str)
    json_str = re.sub(r'\n?```\s*$', '', json_str)

    # 3. 修复尾随逗号 (trailing comma) - LLM 最常见错误
    # 匹配 }, ] 前的逗号（可能有空白）
    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)

    # 4. 修复单引号（替换为双引号，但要小心字符串内容）
    # 只处理明显是键名的情况
    json_str = re.sub(r"'(\w+)'(\s*:)", r'"\1"\2', json_str)

    # 5. 修复未转义的换行符（在字符串值内）
    def escape_newlines_in_strings(match):
        content = match.group(1)
        # 替换实际换行为转义换行
        content = content.replace('\n', '\\n').replace('\r', '\\r')
        return f'"{content}"'

    # 匹配双引号字符串（非贪婪）
    json_str = re.sub(r'"([^"]*(?:\\"[^"]*)*)"', escape_newlines_in_strings, json_str)

    # 6. 修复注释（JSON 不支持注释）
    # 移除 // 单行注释（但要避免误伤 URL 中的 //）
    json_str = re.sub(r'(?<!:)//[^\n]*\n', '\n', json_str)
    # 移除 /* */ 多行注释
    json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)

    # 7. 修复缺失的逗号（常见于多行对象/数组）
    # 匹配 "..." 或 数字 或 } 或 ] 后面紧跟着换行和 " 的情况
    json_str = re.sub(r'(["}\]\d])\s*\n\s*(")', r'\1,\n\2', json_str)

    # 8. 修复浮点数（frame/duration 等应该是整数）
    # 将 "frame": 30.0 修复为 "frame": 30
    json_str = re.sub(r'("(?:frame|duration|totalDuration|frameRate|estimatedActions|priority)":\s*)(\d+)\.0+\b', r'\1\2', json_str)

    # 9. 移除可能的 thinking 标签（如果 LLM 在 JSON 中输出了思考过程）
    json_str = re.sub(r'<thinking>.*?</thinking>\s*', '', json_str, flags=re.DOTALL)
    json_str = re.sub(r'##\s*思考分析.*?(?=\{)', '', json_str, flags=re.DOTALL)
    json_str = re.sub(r'##\s*技能配置\s*', '', json_str)

    return json_str.strip()


def _try_parse_json(json_str: str) -> Tuple[bool, Optional[dict], Optional[str]]:
    """
    尝试解析 JSON，支持多种解析器

    Args:
        json_str: JSON 字符串

    Returns:
        (成功标志, 解析结果, 错误信息)
    """
    # 1. 首先尝试标准 json
    try:
        result = json.loads(json_str)
        return True, result, None
    except json.JSONDecodeError as e:
        std_error = str(e)

    # 2. 尝试修复后再解析
    fixed = _fix_common_json_errors(json_str)
    try:
        result = json.loads(fixed)
        logger.info("JSON 格式错误已通过修复策略解决")
        return True, result, None
    except json.JSONDecodeError:
        pass

    # 3. 使用 json5 宽松解析（如果可用）
    if HAS_JSON5:
        try:
            result = json5.loads(json_str)
            logger.info("使用 json5 宽松解析成功")
            return True, result, None
        except Exception:
            pass

        # 尝试修复后的 json5 解析
        try:
            result = json5.loads(fixed)
            logger.info("使用 json5 解析修复后的 JSON 成功")
            return True, result, None
        except Exception as e:
            pass

    return False, None, std_error


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
    从 Markdown 格式的文本中提取 JSON 代码块（多层容错 + json5 支持）

    容错策略：
    1. 优先匹配 ```json 代码块
    2. 尝试匹配无语言标记的 ``` 代码块
    3. 通过括号匹配找到 JSON 边界
    4. 修复常见 JSON 格式错误
    5. 使用 json5 宽松解析（如果可用）
    6. 最后返回原文本或抛出异常

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

    # 辅助函数：尝试用所有方法解析
    def try_parse(candidate: str) -> Optional[str]:
        success, result, _ = _try_parse_json(candidate)
        if success:
            # 返回标准化的 JSON 字符串
            return json.dumps(result, ensure_ascii=False, indent=2)
        return None

    # 策略1: 匹配 ```json ... ``` 代码块
    pattern = r'```json\s*\n?(.*?)\n?```'
    matches = re.findall(pattern, text, re.DOTALL)

    if matches:
        logger.debug(f"从 ```json 代码块中提取到 {len(matches)} 个 JSON")
        for match in matches:
            extracted = match.strip()
            result = try_parse(extracted)
            if result:
                return result

    # 策略2: 匹配 ``` ... ``` (无语言标记)
    pattern = r'```\s*\n?(.*?)\n?```'
    matches = re.findall(pattern, text, re.DOTALL)

    if matches:
        logger.debug(f"从 ``` 代码块中找到 {len(matches)} 个候选块")
        for match in matches:
            content = match.strip()
            # 跳过明显不是 JSON 的内容
            if not content.startswith(('{', '[')):
                continue
            result = try_parse(content)
            if result:
                return result

    # 策略3: 通过括号匹配找到 JSON 边界（处理代码块外有额外文本的情况）
    json_candidate = _find_json_boundaries(text)
    if json_candidate:
        result = try_parse(json_candidate)
        if result:
            logger.debug("通过括号匹配找到有效 JSON")
            return result

    # 策略4: 直接尝试解析原文本（可能就是纯 JSON）
    result = try_parse(text)
    if result:
        return result

    # 所有策略都失败
    logger.warning("未能提取有效 JSON，所有策略均失败")
    if raise_on_failure:
        raise JSONExtractionError(
            "无法从文本中提取有效的 JSON，已尝试所有容错策略",
            original_text=text,
            attempted_fixes=5 if HAS_JSON5 else 4
        )
    # 返回原文本以保持向后兼容（让上层处理错误）
    return text


def parse_json_safe(text: str) -> Tuple[bool, Optional[dict], str]:
    """
    安全解析 JSON 的便捷函数

    Args:
        text: 可能包含 JSON 的文本

    Returns:
        (成功标志, 解析结果字典, 提取的JSON字符串或错误信息)
    """
    try:
        json_str = extract_json_from_markdown(text, raise_on_failure=True)
        result = json.loads(json_str)
        return True, result, json_str
    except JSONExtractionError as e:
        return False, None, str(e)
    except json.JSONDecodeError as e:
        return False, None, f"JSON 解析错误: {e}"

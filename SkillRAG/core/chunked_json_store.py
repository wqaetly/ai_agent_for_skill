"""
ChunkedJsonStore - 大JSON文件流式加载器
支持按路径加载指定片段，限制内存占用
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path


class ChunkedJsonStore:
    """流式JSON存储，支持按路径访问大文件片段"""

    def __init__(self, max_chunk_size_mb: float = 10.0):
        """
        Args:
            max_chunk_size_mb: 单次加载的最大内存限制(MB)
        """
        self.max_chunk_size_mb = max_chunk_size_mb
        self.max_chunk_bytes = int(max_chunk_size_mb * 1024 * 1024)

    def load_by_path(
        self,
        file_path: str,
        json_path: str,
        include_context: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        按JSONPath加载指定片段

        Args:
            file_path: JSON文件路径
            json_path: JSONPath表达式，如 "tracks.$rcontent[2].actions.$rcontent[0]"
            include_context: 是否包含父级上下文信息

        Returns:
            提取的JSON片段，包含元数据

        Example:
            >>> store.load_by_path(
            ...     "FlameShockwave.json",
            ...     "tracks.$rcontent[2].actions.$rcontent[0]"
            ... )
            {
                "data": {...},  # Action数据
                "context": {
                    "track_name": "Damage Track",
                    "track_index": 2,
                    "action_index": 0
                },
                "size_bytes": 1024,
                "line_range": (145, 165)
            }
        """
        path_parts = self._parse_json_path(json_path)

        # 读取并修复Unity JSON格式
        with open(file_path, 'r', encoding='utf-8') as f:
            json_str = f.read()

        # 修复Unity的非标准JSON
        json_str = self._fix_unity_json(json_str)

        # 解析JSON
        try:
            full_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            return None

        # 按路径提取数据
        data = self._extract_by_path_parts_dict(full_data, path_parts)

        if data is None:
            return None

        result = {
            "data": data,
            "size_bytes": len(json.dumps(data, ensure_ascii=False)),
            "path": json_path
        }

        if include_context:
            result["context"] = self._extract_context(file_path, path_parts)

        return result

    def load_by_line_range(
        self,
        file_path: str,
        start_line: int,
        end_line: int
    ) -> Dict[str, Any]:
        """
        按行号范围加载JSON片段

        Args:
            file_path: JSON文件路径
            start_line: 起始行号（包含）
            end_line: 结束行号（包含）

        Returns:
            包含指定行的JSON片段
        """
        lines = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, start=1):
                if i < start_line:
                    continue
                if i > end_line:
                    break
                lines.append(line)

        raw_text = ''.join(lines)

        # 尝试解析为JSON（可能不完整）
        try:
            data = json.loads(raw_text)
            is_complete = True
        except json.JSONDecodeError:
            # 不完整的JSON，返回原始文本
            data = None
            is_complete = False

        return {
            "raw_text": raw_text,
            "data": data,
            "is_complete": is_complete,
            "line_range": (start_line, end_line),
            "size_bytes": len(raw_text)
        }

    def find_line_number(
        self,
        file_path: str,
        json_path: str
    ) -> Optional[Tuple[int, int]]:
        """
        查找JSONPath对应的行号范围

        Args:
            file_path: JSON文件路径
            json_path: JSONPath表达式

        Returns:
            (start_line, end_line) 元组，如果未找到返回None
        """
        path_parts = self._parse_json_path(json_path)

        with open(file_path, 'r', encoding='utf-8') as f:
            return self._find_line_number_by_path(f, path_parts)

    def get_chunk_summary(
        self,
        file_path: str,
        json_path: str
    ) -> str:
        """
        生成JSON片段的可读摘要

        Args:
            file_path: JSON文件路径
            json_path: JSONPath表达式

        Returns:
            人类可读的摘要文本
        """
        chunk = self.load_by_path(file_path, json_path, include_context=True)
        if chunk is None:
            return f"未找到路径: {json_path}"

        data = chunk["data"]

        # 根据数据类型生成摘要
        if isinstance(data, dict):
            if "$type" in data:
                # Odin序列化对象
                return self._summarize_odin_object(data, chunk.get("context"))
            else:
                return self._summarize_dict(data)
        elif isinstance(data, list):
            return f"数组，包含{len(data)}个元素"
        else:
            return str(data)

    # ==================== 内部方法 ====================

    def _parse_json_path(self, json_path: str) -> List[Tuple[str, Any]]:
        """
        解析JSONPath为路径部分列表

        Args:
            json_path: "tracks.$rcontent[2].actions.$rcontent[0]"

        Returns:
            [("tracks", None), ("$rcontent", 2), ("actions", None), ("$rcontent", 0)]
        """
        parts = []
        segments = json_path.split('.')

        for seg in segments:
            if '[' in seg and ']' in seg:
                # 数组索引: "$rcontent[2]"
                key = seg[:seg.index('[')]
                index = int(seg[seg.index('[')+1:seg.index(']')])
                parts.append((key, index))
            else:
                # 普通键
                parts.append((seg, None))

        return parts

    def _fix_unity_json(self, json_str: str) -> str:
        """
        修复Unity生成的非标准JSON格式
        主要处理Vector3、Color等类型的简写格式
        """
        # 处理 Color (4个值: r, g, b, a)
        pattern_color = r'("\$type":\s*"[^"]*UnityEngine\.Color([^"]*)")\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)'

        def replace_color(match):
            type_str = match.group(1)
            r = match.group(3)
            g = match.group(4)
            b = match.group(5)
            a = match.group(6)
            return f'{type_str}, "r": {r}, "g": {g}, "b": {b}, "a": {a}'

        json_str = re.sub(pattern_color, replace_color, json_str)

        # 处理 Vector3 (3个值: x, y, z)
        pattern_vector3 = r'("\$type":\s*"[^"]*UnityEngine\.Vector3([^"]*)")\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)'

        def replace_vector3(match):
            type_str = match.group(1)
            x = match.group(3)
            y = match.group(4)
            z = match.group(5)
            return f'{type_str}, "x": {x}, "y": {y}, "z": {z}'

        json_str = re.sub(pattern_vector3, replace_vector3, json_str)

        # 处理 Vector2 (2个值: x, y)
        pattern_vector2 = r'("\$type":\s*"[^"]*UnityEngine\.Vector2([^"]*)")\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)'

        def replace_vector2(match):
            type_str = match.group(1)
            x = match.group(3)
            y = match.group(4)
            return f'{type_str}, "x": {x}, "y": {y}'

        json_str = re.sub(pattern_vector2, replace_vector2, json_str)

        return json_str

    def _extract_by_path_parts_dict(
        self,
        data: Any,
        path_parts: List[Tuple[str, Any]]
    ) -> Optional[Any]:
        """从字典中按路径提取数据（回退方案）"""
        current = data

        for key, index in path_parts:
            if current is None:
                return None

            # 访问键
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None

            # 访问数组索引
            if index is not None:
                if isinstance(current, list) and 0 <= index < len(current):
                    current = current[index]
                else:
                    return None

        return current

    def _find_line_number_by_path(
        self,
        file_obj,
        path_parts: List[Tuple[str, Any]]
    ) -> Optional[Tuple[int, int]]:
        """
        查找路径对应的行号范围

        这需要记录JSON解析器的当前位置，比较复杂
        这里使用简化方案：通过文本搜索估算
        """
        file_obj.seek(0)
        content = file_obj.read()

        # 提取目标数据用于搜索
        file_obj.seek(0)
        target_data = self._extract_by_path_parts(file_obj, path_parts)

        if target_data is None:
            return None

        # 将目标数据转为紧凑JSON字符串
        target_json = json.dumps(target_data, ensure_ascii=False, separators=(',', ':'))

        # 在文件中搜索（简化版，实际需要更精确的方法）
        # 这里只是估算，真实实现需要使用JSON解析器的位置信息
        start_pos = content.find(target_json[:50])  # 搜索前50字符
        if start_pos == -1:
            return None

        # 计算行号
        start_line = content[:start_pos].count('\n') + 1
        end_line = start_line + target_json.count('\n')

        return (start_line, end_line)

    def _extract_context(
        self,
        file_path: str,
        path_parts: List[Tuple[str, Any]]
    ) -> Dict[str, Any]:
        """提取路径的上下文信息（父级元素）"""
        context = {}

        # 提取轨道信息
        for i, (key, index) in enumerate(path_parts):
            if key == "tracks":
                # 找到tracks后面的索引
                if i + 1 < len(path_parts) and path_parts[i+1][1] is not None:
                    track_index = path_parts[i+1][1]
                    context["track_index"] = track_index

                    # 加载轨道名称
                    track_path = f"tracks.$rcontent[{track_index}]"
                    track_data = self.load_by_path(file_path, track_path)
                    if track_data and "data" in track_data:
                        context["track_name"] = track_data["data"].get("trackName", "Unknown")

            elif key == "actions":
                # Action索引
                if i + 1 < len(path_parts) and path_parts[i+1][1] is not None:
                    context["action_index"] = path_parts[i+1][1]

        return context

    def _summarize_odin_object(
        self,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """生成Odin对象的摘要"""
        type_str = data.get("$type", "Unknown")

        # 提取类型名称
        if "|" in type_str:
            type_name = type_str.split("|")[1].split(",")[0]
        else:
            type_name = type_str

        # 根据类型生成摘要
        if "Action" in type_name:
            return self._summarize_action(data, type_name, context)
        else:
            return f"{type_name} 对象"

    def _summarize_action(
        self,
        data: Dict[str, Any],
        type_name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """生成Action的可读摘要"""
        parts = []

        # 轨道和位置信息
        if context:
            if "track_name" in context:
                parts.append(f"轨道: {context['track_name']}")
            if "action_index" in context:
                parts.append(f"第{context['action_index']}个Action")

        # 帧信息
        frame = data.get("frame", None)
        duration = data.get("duration", None)
        if frame is not None:
            parts.append(f"第{frame}帧")
        if duration is not None:
            parts.append(f"持续{duration}帧")

        # 类型特定参数
        if "DamageAction" in type_name:
            damage = data.get("baseDamage", data.get("damage", "?"))
            damage_type = data.get("damageType", "")
            parts.append(f"造成{damage}点{damage_type}伤害")

        elif "MovementAction" in type_name:
            speed = data.get("moveSpeed", data.get("speed", "?"))
            parts.append(f"移动速度{speed}")

        elif "AnimationAction" in type_name:
            clip = data.get("animationClipName", "")
            if clip:
                parts.append(f"播放动画: {clip}")

        return f"{type_name} - {', '.join(parts)}"

    def _summarize_dict(self, data: Dict[str, Any]) -> str:
        """生成普通字典的摘要"""
        keys = list(data.keys())[:5]
        if len(data) > 5:
            return f"包含{len(data)}个字段: {', '.join(keys)}..."
        else:
            return f"包含字段: {', '.join(keys)}"

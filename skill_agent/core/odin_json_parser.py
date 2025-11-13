"""
Odin JSON 解析器
解析 Unity Odin 序列化的 JSON 格式，转换为标准 Python 对象
"""

import json
from typing import Any, Dict, List, Optional


class OdinJsonParser:
    """Odin JSON 格式解析器"""

    def __init__(self):
        """初始化解析器"""
        # 类型缓存（用于处理类型引用）
        self.type_cache: Dict[int, str] = {}

    def parse(self, json_str: str) -> Any:
        """
        解析 Odin JSON 字符串

        Args:
            json_str: Odin JSON 字符串

        Returns:
            解析后的 Python 对象
        """
        # 先用标准 JSON 解析器加载
        raw_data = json.loads(json_str)

        # 清空类型缓存
        self.type_cache.clear()

        # 递归解析 Odin 特殊结构
        return self._resolve_odin_structure(raw_data)

    def parse_file(self, file_path: str, encoding: str = 'utf-8') -> Any:
        """
        从文件解析 Odin JSON

        Args:
            file_path: 文件路径
            encoding: 文件编码

        Returns:
            解析后的 Python 对象
        """
        with open(file_path, 'r', encoding=encoding) as f:
            return self.parse(f.read())

    def _resolve_odin_structure(self, data: Any) -> Any:
        """
        递归解析 Odin 特殊结构

        Args:
            data: 原始数据

        Returns:
            解析后的数据
        """
        if isinstance(data, dict):
            return self._resolve_dict(data)
        elif isinstance(data, list):
            return [self._resolve_odin_structure(item) for item in data]
        else:
            return data

    def _resolve_dict(self, data: Dict[str, Any]) -> Any:
        """
        解析字典类型数据

        Args:
            data: 字典数据

        Returns:
            解析后的数据
        """
        # 处理集合类型：$rcontent
        if '$rcontent' in data:
            content = data.get('$rcontent', [])
            if isinstance(content, list):
                return [self._resolve_odin_structure(item) for item in content]
            return content

        # 处理类型信息：$type
        if '$type' in data:
            type_info = data['$type']

            # 缓存类型信息（用于后续引用）
            if '$id' in data:
                type_id = data['$id']
                if isinstance(type_info, str):
                    self.type_cache[type_id] = type_info

            # 处理 Unity 特殊类型
            if isinstance(type_info, str):
                # Vector3
                if 'Vector3' in type_info:
                    return self._parse_vector3(data)

                # Vector2
                elif 'Vector2' in type_info:
                    return self._parse_vector2(data)

                # Quaternion
                elif 'Quaternion' in type_info:
                    return self._parse_quaternion(data)

                # Color
                elif 'Color' in type_info:
                    return self._parse_color(data)

                # Vector4
                elif 'Vector4' in type_info:
                    return self._parse_vector4(data)

        # 普通对象：递归处理所有字段（排除 Odin 元数据）
        result = {}
        for key, value in data.items():
            # 跳过 Odin 元数据字段
            if key.startswith('$'):
                # 保留 $type 用于类型识别（可选）
                if key == '$type' and isinstance(value, str):
                    result['_odin_type'] = value
                continue

            result[key] = self._resolve_odin_structure(value)

        return result if result else data

    def _parse_vector3(self, data: Dict[str, Any]) -> Dict[str, float]:
        """
        解析 Vector3 类型

        Args:
            data: 包含 Vector3 数据的字典

        Returns:
            标准化的 Vector3 字典 {"x": ..., "y": ..., "z": ...}
        """
        # 方案 1：标准化后的格式（带键名）
        if 'x' in data and 'y' in data and 'z' in data:
            return {
                'x': float(data['x']),
                'y': float(data['y']),
                'z': float(data['z'])
            }

        # 方案 2：裸值数组（数字键）
        if 0 in data or '0' in data:
            return {
                'x': float(data.get(0) or data.get('0', 0)),
                'y': float(data.get(1) or data.get('1', 0)),
                'z': float(data.get(2) or data.get('2', 0))
            }

        # 方案 3：从非元数据键中提取（假设有序）
        values = []
        for key, value in data.items():
            if not key.startswith('$') and isinstance(value, (int, float)):
                values.append(value)

        if len(values) >= 3:
            return {'x': float(values[0]), 'y': float(values[1]), 'z': float(values[2])}

        # 默认返回零向量
        return {'x': 0.0, 'y': 0.0, 'z': 0.0}

    def _parse_vector2(self, data: Dict[str, Any]) -> Dict[str, float]:
        """解析 Vector2 类型"""
        if 'x' in data and 'y' in data:
            return {'x': float(data['x']), 'y': float(data['y'])}

        if 0 in data or '0' in data:
            return {
                'x': float(data.get(0) or data.get('0', 0)),
                'y': float(data.get(1) or data.get('1', 0))
            }

        values = [v for k, v in data.items() if not k.startswith('$') and isinstance(v, (int, float))]
        if len(values) >= 2:
            return {'x': float(values[0]), 'y': float(values[1])}

        return {'x': 0.0, 'y': 0.0}

    def _parse_quaternion(self, data: Dict[str, Any]) -> Dict[str, float]:
        """解析 Quaternion 类型"""
        if all(k in data for k in ['x', 'y', 'z', 'w']):
            return {
                'x': float(data['x']),
                'y': float(data['y']),
                'z': float(data['z']),
                'w': float(data['w'])
            }

        if 0 in data or '0' in data:
            return {
                'x': float(data.get(0) or data.get('0', 0)),
                'y': float(data.get(1) or data.get('1', 0)),
                'z': float(data.get(2) or data.get('2', 0)),
                'w': float(data.get(3) or data.get('3', 1))
            }

        values = [v for k, v in data.items() if not k.startswith('$') and isinstance(v, (int, float))]
        if len(values) >= 4:
            return {
                'x': float(values[0]),
                'y': float(values[1]),
                'z': float(values[2]),
                'w': float(values[3])
            }

        return {'x': 0.0, 'y': 0.0, 'z': 0.0, 'w': 1.0}

    def _parse_color(self, data: Dict[str, Any]) -> Dict[str, float]:
        """解析 Color 类型"""
        if all(k in data for k in ['r', 'g', 'b', 'a']):
            return {
                'r': float(data['r']),
                'g': float(data['g']),
                'b': float(data['b']),
                'a': float(data['a'])
            }

        if 0 in data or '0' in data:
            return {
                'r': float(data.get(0) or data.get('0', 0)),
                'g': float(data.get(1) or data.get('1', 0)),
                'b': float(data.get(2) or data.get('2', 0)),
                'a': float(data.get(3) or data.get('3', 1))
            }

        values = [v for k, v in data.items() if not k.startswith('$') and isinstance(v, (int, float))]
        if len(values) >= 4:
            return {
                'r': float(values[0]),
                'g': float(values[1]),
                'b': float(values[2]),
                'a': float(values[3])
            }

        return {'r': 1.0, 'g': 1.0, 'b': 1.0, 'a': 1.0}

    def _parse_vector4(self, data: Dict[str, Any]) -> Dict[str, float]:
        """解析 Vector4 类型"""
        if all(k in data for k in ['x', 'y', 'z', 'w']):
            return {
                'x': float(data['x']),
                'y': float(data['y']),
                'z': float(data['z']),
                'w': float(data['w'])
            }

        if 0 in data or '0' in data:
            return {
                'x': float(data.get(0) or data.get('0', 0)),
                'y': float(data.get(1) or data.get('1', 0)),
                'z': float(data.get(2) or data.get('2', 0)),
                'w': float(data.get(3) or data.get('3', 0))
            }

        values = [v for k, v in data.items() if not k.startswith('$') and isinstance(v, (int, float))]
        if len(values) >= 4:
            return {
                'x': float(values[0]),
                'y': float(values[1]),
                'z': float(values[2]),
                'w': float(values[3])
            }

        return {'x': 0.0, 'y': 0.0, 'z': 0.0, 'w': 0.0}


# 便捷函数
def parse_odin_json(json_str: str) -> Any:
    """
    解析 Odin JSON 字符串（便捷函数）

    Args:
        json_str: Odin JSON 字符串

    Returns:
        解析后的 Python 对象
    """
    parser = OdinJsonParser()
    return parser.parse(json_str)


def parse_odin_json_file(file_path: str, encoding: str = 'utf-8') -> Any:
    """
    从文件解析 Odin JSON（便捷函数）

    Args:
        file_path: 文件路径
        encoding: 文件编码

    Returns:
        解析后的 Python 对象
    """
    parser = OdinJsonParser()
    return parser.parse_file(file_path, encoding)


if __name__ == '__main__':
    # 测试代码
    test_json = '''
    {
        "$id": 0,
        "$type": "SkillData",
        "skillName": "Test Skill",
        "position": {
            "$type": "UnityEngine.Vector3",
            "x": 1.5,
            "y": 2.0,
            "z": 3.5
        },
        "tracks": {
            "$rcontent": [
                {
                    "trackName": "Track 1",
                    "value": 42
                },
                {
                    "trackName": "Track 2",
                    "value": 100
                }
            ]
        }
    }
    '''

    result = parse_odin_json(test_json)
    print("Parsed result:")
    print(json.dumps(result, indent=2))

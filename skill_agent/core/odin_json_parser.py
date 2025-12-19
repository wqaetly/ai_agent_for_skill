"""
Odin JSON 解析器
解析 Unity Odin 序列化的 JSON 格式，转换为标准 Python 对象
"""

import json
import re
import threading
from typing import Any, Dict, List, Optional, Tuple

# _odin_type 格式验证正则
# 支持两种格式：
# 1. "FullTypeName, Assembly-CSharp" (无索引)
# 2. "index|FullTypeName, Assembly-CSharp" (带索引)
ODIN_TYPE_PATTERN = re.compile(
    r'^(?:(\d+)\|)?'  # 可选的索引部分
    r'([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)'  # 完整类型名
    r',\s*'  # 逗号分隔
    r'([A-Za-z_][A-Za-z0-9_\-]*)'  # 程序集名称
    r'$'
)


def validate_odin_type(odin_type: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    验证 _odin_type 格式是否正确
    
    Args:
        odin_type: _odin_type 字符串
        
    Returns:
        (is_valid, type_name, error_message)
        - is_valid: 格式是否正确
        - type_name: 提取的类型名（不含索引）
        - error_message: 错误信息（如果验证失败）
    """
    if not odin_type:
        return False, None, "_odin_type 不能为空"
    
    match = ODIN_TYPE_PATTERN.match(odin_type.strip())
    if not match:
        return False, None, f"_odin_type 格式无效: '{odin_type}'，期望格式: 'TypeName, Assembly-CSharp' 或 'index|TypeName, Assembly-CSharp'"
    
    # 提取类型名和程序集
    type_name = match.group(2)
    assembly = match.group(3)
    full_type = f"{type_name}, {assembly}"
    
    return True, full_type, None


def extract_type_name_from_odin_type(odin_type: str) -> str:
    """
    从 _odin_type 中提取纯类型名（去掉索引和程序集）
    
    Args:
        odin_type: 如 "4|SkillSystem.Actions.DamageAction, Assembly-CSharp"
        
    Returns:
        类型名，如 "DamageAction"
    """
    if not odin_type:
        return ""
    
    # 去掉索引部分
    if "|" in odin_type:
        odin_type = odin_type.split("|", 1)[1]
    
    # 去掉程序集部分
    if "," in odin_type:
        odin_type = odin_type.split(",", 1)[0]
    
    # 提取最后一个类名
    if "." in odin_type:
        return odin_type.rsplit(".", 1)[1]
    
    return odin_type


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


class OdinJsonSerializer:
    """
    Odin JSON 序列化器（线程安全）
    将 Python 对象（LLM 生成格式）转换为 Unity Odin 序列化格式
    
    注意：
    - 此类使用线程锁确保并发安全
    - 每次 serialize() 调用会重置内部状态
    - LLM 生成的 _odin_type 中的索引会被忽略，由序列化器重新分配
    """

    def __init__(self):
        """初始化序列化器"""
        self._lock = threading.Lock()
        self._id_counter = 0
        self._type_registry: Dict[str, int] = {}  # type_str -> type_index
        self._warnings: List[str] = []  # 序列化过程中的警告

    def serialize(self, skill_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将技能数据序列化为 Odin JSON 格式

        Args:
            skill_data: LLM 生成的技能数据（含 tracks 数组）

        Returns:
            Odin 序列化格式的技能数据
        """
        with self._lock:
            # 重置状态
            self._id_counter = 0
            self._type_registry.clear()
            self._warnings.clear()

            # 构建根对象
            result = {
                "$id": self._next_id(),
                "$type": self._get_type_ref("SkillSystem.Data.SkillData, Assembly-CSharp"),
                "skillName": skill_data.get("skillName", ""),
                "skillDescription": skill_data.get("skillDescription", ""),
                "totalDuration": skill_data.get("totalDuration", 0),
                "frameRate": skill_data.get("frameRate", 30),
            }

            # 序列化 tracks
            tracks = skill_data.get("tracks", [])
            result["tracks"] = self._serialize_track_list(tracks)

            # skillId 放最后（与示例一致）
            result["skillId"] = skill_data.get("skillId", "")

            return result

    def get_warnings(self) -> List[str]:
        """获取序列化过程中的警告"""
        return self._warnings.copy()

    def _next_id(self) -> int:
        """获取下一个唯一 ID"""
        current = self._id_counter
        self._id_counter += 1
        return current

    def _get_type_ref(self, type_str: str) -> str:
        """
        获取类型引用（带索引）

        首次出现返回完整类型字符串，后续引用只返回索引
        """
        if type_str not in self._type_registry:
            index = len(self._type_registry)
            self._type_registry[type_str] = index

        index = self._type_registry[type_str]
        return f"{index}|{type_str}"

    def _serialize_track_list(self, tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """序列化 Track 列表"""
        list_type = "System.Collections.Generic.List`1[[SkillSystem.Data.SkillTrack, Assembly-CSharp]], mscorlib"

        serialized_tracks = []
        for track in tracks:
            serialized_tracks.append(self._serialize_track(track))

        return {
            "$id": self._next_id(),
            "$type": self._get_type_ref(list_type),
            "$rlength": len(serialized_tracks),
            "$rcontent": serialized_tracks
        }

    def _serialize_track(self, track: Dict[str, Any]) -> Dict[str, Any]:
        """序列化单个 Track"""
        track_type = "SkillSystem.Data.SkillTrack, Assembly-CSharp"

        result = {
            "$id": self._next_id(),
            "$type": self._get_type_ref(track_type),
            "trackName": track.get("trackName", ""),
            "enabled": track.get("enabled", True),
        }

        # 序列化 actions
        actions = track.get("actions", [])
        result["actions"] = self._serialize_action_list(actions)

        return result

    def _serialize_action_list(self, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """序列化 Action 列表"""
        list_type = "System.Collections.Generic.List`1[[SkillSystem.Actions.ISkillAction, Assembly-CSharp]], mscorlib"

        serialized_actions = []
        for action in actions:
            serialized_actions.append(self._serialize_action(action))

        return {
            "$id": self._next_id(),
            "$type": self._get_type_ref(list_type),
            "$rlength": len(serialized_actions),
            "$rcontent": serialized_actions
        }

    def _serialize_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """序列化单个 Action"""
        # 从 parameters 中提取 _odin_type
        parameters = action.get("parameters", {})
        odin_type = parameters.get("_odin_type", "")

        # 验证并解析 _odin_type 格式
        is_valid, type_name, error_msg = validate_odin_type(odin_type)
        
        if not is_valid:
            # 记录警告并使用默认类型
            self._warnings.append(
                f"Action (frame={action.get('frame', '?')}) {error_msg}，使用默认类型"
            )
            type_name = "SkillSystem.Actions.BaseAction, Assembly-CSharp"

        result = {
            "$id": self._next_id(),
            "$type": self._get_type_ref(type_name),
            "frame": action.get("frame", 0),
            "duration": action.get("duration", 1),
            "enabled": action.get("enabled", True),
        }

        # 扁平化 parameters（排除 _odin_type）
        for key, value in parameters.items():
            if key == "_odin_type":
                continue
            result[key] = self._serialize_value(value)

        return result

    def _serialize_value(self, value: Any) -> Any:
        """
        序列化值（处理特殊类型如 Vector3）
        """
        if isinstance(value, dict):
            # 检查是否为 Vector3 格式
            if set(value.keys()) == {"x", "y", "z"}:
                return self._serialize_vector3(value)
            # 检查是否为 Vector2 格式
            elif set(value.keys()) == {"x", "y"}:
                return self._serialize_vector2(value)
            # 检查是否为 Color 格式
            elif set(value.keys()) == {"r", "g", "b", "a"}:
                return self._serialize_color(value)
            # 检查是否为 Quaternion/Vector4 格式
            elif set(value.keys()) == {"x", "y", "z", "w"}:
                return self._serialize_vector4(value)
            # 普通字典
            else:
                return {k: self._serialize_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._serialize_value(item) for item in value]
        else:
            return value

    def _serialize_vector3(self, vec: Dict[str, float]) -> Dict[str, Any]:
        """序列化 Vector3"""
        return {
            "$type": self._get_type_ref("UnityEngine.Vector3, UnityEngine.CoreModule"),
            0: vec.get("x", 0.0),
            1: vec.get("y", 0.0),
            2: vec.get("z", 0.0)
        }

    def _serialize_vector2(self, vec: Dict[str, float]) -> Dict[str, Any]:
        """序列化 Vector2"""
        return {
            "$type": self._get_type_ref("UnityEngine.Vector2, UnityEngine.CoreModule"),
            0: vec.get("x", 0.0),
            1: vec.get("y", 0.0)
        }

    def _serialize_vector4(self, vec: Dict[str, float]) -> Dict[str, Any]:
        """序列化 Vector4/Quaternion"""
        return {
            "$type": self._get_type_ref("UnityEngine.Vector4, UnityEngine.CoreModule"),
            0: vec.get("x", 0.0),
            1: vec.get("y", 0.0),
            2: vec.get("z", 0.0),
            3: vec.get("w", 0.0)
        }

    def _serialize_color(self, color: Dict[str, float]) -> Dict[str, Any]:
        """序列化 Color"""
        return {
            "$type": self._get_type_ref("UnityEngine.Color, UnityEngine.CoreModule"),
            0: color.get("r", 1.0),
            1: color.get("g", 1.0),
            2: color.get("b", 1.0),
            3: color.get("a", 1.0)
        }


def serialize_to_odin(skill_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    将技能数据序列化为 Odin JSON 格式（便捷函数）

    Args:
        skill_data: LLM 生成的技能数据

    Returns:
        Odin 序列化格式的技能数据
    """
    serializer = OdinJsonSerializer()
    return serializer.serialize(skill_data)


def serialize_to_odin_string(skill_data: Dict[str, Any], indent: int = 4) -> str:
    """
    将技能数据序列化为 Odin JSON 字符串（便捷函数）

    Args:
        skill_data: LLM 生成的技能数据
        indent: 缩进空格数

    Returns:
        Odin 序列化格式的 JSON 字符串
    """
    odin_data = serialize_to_odin(skill_data)
    return json.dumps(odin_data, indent=indent, ensure_ascii=False)


if __name__ == '__main__':
    # 测试解析
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

    # 测试序列化
    print("\n" + "=" * 50)
    print("Test serialization:")

    test_skill = {
        "skillName": "火球术",
        "skillId": "fireball-001",
        "skillDescription": "释放火球",
        "totalDuration": 120,
        "frameRate": 30,
        "tracks": [
            {
                "trackName": "Animation Track",
                "enabled": True,
                "actions": [
                    {
                        "frame": 0,
                        "duration": 30,
                        "enabled": True,
                        "parameters": {
                            "_odin_type": "SkillSystem.Actions.AnimationAction, Assembly-CSharp",
                            "animationClipName": "Cast",
                            "normalizedTime": 0.0
                        }
                    }
                ]
            }
        ]
    }

    odin_result = serialize_to_odin(test_skill)
    print(json.dumps(odin_result, indent=2, ensure_ascii=False))

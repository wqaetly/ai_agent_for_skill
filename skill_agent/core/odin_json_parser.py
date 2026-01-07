"""
Odin JSON 解析器
解析 Unity Odin 序列化的 JSON 格式，转换为标准 Python 对象

Odin JSON 格式特点（基于 odin_test_data.json 分析）：
1. 类型引用系统 ($type):
   - 首次出现: "$type": "索引|完整类型名, 程序集"
   - 后续引用: "$type": 索引 (仅数字)
   
2. 对象引用系统 ($id / $iref):
   - $id: 对象唯一标识
   - $iref:N: 引用已定义的对象
   
3. 集合格式:
   - 基元数组: $plength + $pcontent
   - 引用数组/List: $rlength + $rcontent
   - Dictionary: $rcontent 包含 {$k: key, $v: value} 对象
   
4. Unity类型使用裸值数组:
   - Vector3: {"$type": "2|UnityEngine.Vector3...", 1, 2, 3} (无键名)
   - Color: {"$type": "7|UnityEngine.Color...", 1, 0.5, 0.25, 1}
   
5. Nullable类型: {"$type": "39|System.Nullable`1...", 42} 或 null
"""

import json
import re
import threading
from typing import Any, Dict, List, Optional, Tuple, Union


def preprocess_odin_json(json_str: str) -> str:
    """
    预处理 Odin JSON 字符串，将非标准格式转换为标准 JSON
    
    Odin 序列化的 Unity 类型使用裸值数组格式：
    { "$type": "...", 1.5, 2.5 }
    
    需要转换为标准 JSON：
    { "$type": "...", "0": 1.5, "1": 2.5 }
    """
    result = []
    i = 0
    n = len(json_str)
    
    while i < n:
        char = json_str[i]
        
        if char == '{':
            # 进入对象，处理可能的裸值
            result.append(char)
            i += 1
            
            # 跟踪当前对象中的裸值索引
            bare_value_index = 0
            in_object = True
            depth = 1
            
            while i < n and depth > 0:
                char = json_str[i]
                
                if char == '{':
                    depth += 1
                    result.append(char)
                    i += 1
                elif char == '}':
                    depth -= 1
                    result.append(char)
                    i += 1
                elif char == '[':
                    # 处理数组
                    result.append(char)
                    i += 1
                    array_depth = 1
                    while i < n and array_depth > 0:
                        c = json_str[i]
                        if c == '[':
                            array_depth += 1
                        elif c == ']':
                            array_depth -= 1
                        result.append(c)
                        i += 1
                elif char == '"':
                    # 处理字符串
                    result.append(char)
                    i += 1
                    while i < n:
                        c = json_str[i]
                        result.append(c)
                        i += 1
                        if c == '"' and json_str[i-2:i-1] != '\\':
                            break
                        if c == '\\' and i < n:
                            result.append(json_str[i])
                            i += 1
                elif char == ',':
                    result.append(char)
                    i += 1
                    # 检查逗号后是否是裸值（数字、true、false、null）
                    # 跳过空白
                    while i < n and json_str[i] in ' \t\n\r':
                        result.append(json_str[i])
                        i += 1
                    
                    if i < n and depth == 1:
                        # 检查是否是裸值（不是以 " 或 { 或 [ 开头，也不是 }）
                        next_char = json_str[i]
                        if next_char not in '"{[}':
                            # 可能是裸值，检查是否是数字、true、false、null
                            # 向前查找到下一个逗号或 }
                            lookahead = ""
                            j = i
                            while j < n and json_str[j] not in ',}':
                                lookahead += json_str[j]
                                j += 1
                            lookahead = lookahead.strip()
                            
                            # 检查是否是裸值
                            if lookahead and not lookahead.startswith('"') and ':' not in lookahead:
                                # 这是一个裸值，添加索引键
                                result.append(f'"{bare_value_index}": ')
                                bare_value_index += 1
                elif char == ':':
                    result.append(char)
                    i += 1
                    # 冒号后面重置裸值索引（这是一个键值对）
                else:
                    result.append(char)
                    i += 1
        else:
            result.append(char)
            i += 1
    
    return ''.join(result)


def parse_odin_json_raw(json_str: str) -> Any:
    """
    解析 Odin 非标准 JSON 格式
    
    处理以下非标准格式：
    1. 裸值: { "$type": "...", 1.5, 2.5 } -> { "$type": "...", "0": 1.5, "1": 2.5 }
    2. 裸对象: { "$type": "...", {...}, {...} } -> { "$type": "...", "0": {...}, "1": {...} }
    3. $iref:N 引用
    4. 数组中的键值对: ["ranks": "2|3", 1, 2] -> [{"ranks": "2|3"}, 1, 2]
    """
    # 移除 BOM
    if json_str.startswith('\ufeff'):
        json_str = json_str[1:]
    
    # 字符级解析
    result = []
    i = 0
    n = len(json_str)
    
    # 状态栈：每个元素是 [bare_index, has_type, expect_value, context]
    # bare_index: 当前裸值索引
    # has_type: 是否包含 $type（可能需要处理裸值）
    # expect_value: 是否期待一个值（冒号后面）
    # context: 'object' 或 'array'
    stack = []
    
    while i < n:
        c = json_str[i]
        
        # 跳过空白
        if c in ' \t\n\r':
            result.append(c)
            i += 1
            continue
        
        # 字符串
        if c == '"':
            string_start = len(result)
            result.append(c)
            i += 1
            while i < n:
                c2 = json_str[i]
                result.append(c2)
                i += 1
                if c2 == '\\' and i < n:
                    result.append(json_str[i])
                    i += 1
                elif c2 == '"':
                    break
            
            # 检查是否在数组中且后面跟着冒号（数组中的键值对）
            if stack and stack[-1][3] == 'array':
                # 向前看是否有冒号
                j = i
                while j < n and json_str[j] in ' \t\n\r':
                    j += 1
                if j < n and json_str[j] == ':':
                    # 这是数组中的键值对，需要包装成对象
                    # 在字符串前插入 {
                    result.insert(string_start, '{')
                    # 继续读取冒号和值
                    result.append(':')
                    i = j + 1
                    # 跳过空白
                    while i < n and json_str[i] in ' \t\n\r':
                        result.append(json_str[i])
                        i += 1
                    # 读取值（字符串）
                    if i < n and json_str[i] == '"':
                        result.append(json_str[i])
                        i += 1
                        while i < n:
                            c3 = json_str[i]
                            result.append(c3)
                            i += 1
                            if c3 == '\\' and i < n:
                                result.append(json_str[i])
                                i += 1
                            elif c3 == '"':
                                break
                    # 添加结束 }
                    result.append('}')
                    continue
            
            # 字符串处理完毕，如果之前期待值，现在不再期待
            if stack and stack[-1][3] == 'object':
                stack[-1][2] = False
            continue
        
        # 对象开始
        if c == '{':
            # 检查是否是裸对象（在有 $type 的对象中，且不是在期待值的位置，且不在数组中）
            if stack and stack[-1][3] == 'object' and stack[-1][1] and not stack[-1][2]:
                # 这是一个裸对象，需要添加索引键
                bare_idx = stack[-1][0]
                result.append(f'"{bare_idx}": ')
                stack[-1][0] += 1
            
            result.append(c)
            i += 1
            # 向前看是否有 $type
            lookahead = json_str[i:i+300]
            # 只在第一个 } 之前查找 $type
            first_brace = lookahead.find('}')
            if first_brace > 0:
                lookahead = lookahead[:first_brace]
            has_type = '"$type"' in lookahead
            stack.append([0, has_type, False, 'object'])
            continue
        
        # 对象结束
        if c == '}':
            result.append(c)
            i += 1
            if stack:
                stack.pop()
            # 父对象不再期待值
            if stack and stack[-1][3] == 'object':
                stack[-1][2] = False
            continue
        
        # 数组开始
        if c == '[':
            result.append(c)
            i += 1
            stack.append([0, False, False, 'array'])
            continue
        
        # 数组结束
        if c == ']':
            result.append(c)
            i += 1
            if stack:
                stack.pop()
            if stack and stack[-1][3] == 'object':
                stack[-1][2] = False
            continue
        
        # 冒号 - 标记期待值
        if c == ':':
            result.append(c)
            i += 1
            if stack and stack[-1][3] == 'object':
                stack[-1][2] = True  # 期待一个值
            continue
        
        # 逗号 - 不再期待值
        if c == ',':
            result.append(c)
            i += 1
            if stack and stack[-1][3] == 'object':
                stack[-1][2] = False
            continue
        
        # 检查是否是裸值（在有 $type 的对象中，且不是在期待值的位置）
        if stack and stack[-1][3] == 'object' and stack[-1][1] and not stack[-1][2]:
            if c in '-0123456789tfn':
                # 可能是裸值
                if c == 't' and json_str[i:i+4] == 'true':
                    bare_idx = stack[-1][0]
                    result.append(f'"{bare_idx}": true')
                    stack[-1][0] += 1
                    i += 4
                    continue
                elif c == 'f' and json_str[i:i+5] == 'false':
                    bare_idx = stack[-1][0]
                    result.append(f'"{bare_idx}": false')
                    stack[-1][0] += 1
                    i += 5
                    continue
                elif c == 'n' and json_str[i:i+4] == 'null':
                    bare_idx = stack[-1][0]
                    result.append(f'"{bare_idx}": null')
                    stack[-1][0] += 1
                    i += 4
                    continue
                elif c in '-0123456789':
                    # 读取完整数字
                    num_chars = []
                    while i < n and json_str[i] in '-+0123456789.eE':
                        num_chars.append(json_str[i])
                        i += 1
                    num_str = ''.join(num_chars)
                    bare_idx = stack[-1][0]
                    result.append(f'"{bare_idx}": {num_str}')
                    stack[-1][0] += 1
                    continue
        
        # $iref:N 处理
        if c == '$' and json_str[i:i+5] == '$iref':
            ref_start = i
            while i < n and json_str[i] not in ',}\n\r\t ':
                i += 1
            ref_str = json_str[ref_start:i]
            result.append(f'"{ref_str}"')
            if stack and stack[-1][3] == 'object':
                stack[-1][2] = False
            continue
        
        # 普通值（数字、true、false、null）- 在期待值的位置或数组中
        if stack and (stack[-1][2] or stack[-1][3] == 'array'):
            if c in '-0123456789':
                # 读取完整数字
                num_chars = []
                while i < n and json_str[i] in '-+0123456789.eE':
                    num_chars.append(json_str[i])
                    i += 1
                num_str = ''.join(num_chars)
                result.append(num_str)
                if stack[-1][3] == 'object':
                    stack[-1][2] = False
                continue
            elif c == 't' and json_str[i:i+4] == 'true':
                result.append('true')
                i += 4
                if stack[-1][3] == 'object':
                    stack[-1][2] = False
                continue
            elif c == 'f' and json_str[i:i+5] == 'false':
                result.append('false')
                i += 5
                if stack[-1][3] == 'object':
                    stack[-1][2] = False
                continue
            elif c == 'n' and json_str[i:i+4] == 'null':
                result.append('null')
                i += 4
                if stack[-1][3] == 'object':
                    stack[-1][2] = False
                continue
        
        # 其他字符直接添加
        result.append(c)
        i += 1
    
    processed_json = ''.join(result)
    return json.loads(processed_json)

# _odin_type 格式验证正则
# 支持多种格式：
# 1. "FullTypeName, Assembly-CSharp" (无索引)
# 2. "index|FullTypeName, Assembly-CSharp" (带索引)
# 3. 支持泛型类型如 "System.Collections.Generic.List`1[[System.Int32, mscorlib]], mscorlib"
ODIN_TYPE_PATTERN = re.compile(
    r'^(?:(\d+)\|)?'  # 可选的索引部分
    r'(.+?)'  # 类型名（包括泛型）
    r',\s*'  # 逗号分隔
    r'([A-Za-z_][A-Za-z0-9_\-\.]*)'  # 程序集名称
    r'$'
)

# Unity 内置类型映射（用于识别需要特殊处理的类型）
UNITY_VECTOR_TYPES = {
    'UnityEngine.Vector2': 2,
    'UnityEngine.Vector3': 3,
    'UnityEngine.Vector4': 4,
    'UnityEngine.Vector2Int': 2,
    'UnityEngine.Vector3Int': 3,
    'UnityEngine.Quaternion': 4,
    'UnityEngine.Color': 4,
    'UnityEngine.Color32': 4,
    'UnityEngine.Rect': 4,
    'UnityEngine.GradientAlphaKey': 2,
    'UnityEngine.GradientColorKey': 2,  # 实际是 Color + float
    'UnityEngine.LayerMask': 1,
}


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
    
    # 处理纯数字索引引用
    if isinstance(odin_type, int) or odin_type.isdigit():
        return True, None, None  # 类型引用，需要从缓存获取
    
    match = ODIN_TYPE_PATTERN.match(odin_type.strip())
    if not match:
        return False, None, f"_odin_type 格式无效: '{odin_type}'，期望格式: 'TypeName, Assembly' 或 'index|TypeName, Assembly'"
    
    # 提取类型名和程序集
    type_name = match.group(2)
    assembly = match.group(3)
    full_type = f"{type_name}, {assembly}"
    
    return True, full_type, None


def extract_type_name_from_odin_type(odin_type: Union[str, int]) -> str:
    """
    从 _odin_type 中提取纯类型名（去掉索引和程序集）
    
    Args:
        odin_type: 如 "4|SkillSystem.Actions.DamageAction, Assembly-CSharp" 或 4
        
    Returns:
        类型名，如 "DamageAction"
    """
    if not odin_type:
        return ""
    
    if isinstance(odin_type, int):
        return ""  # 纯索引引用，需要从缓存获取
    
    # 去掉索引部分
    if "|" in odin_type:
        odin_type = odin_type.split("|", 1)[1]
    
    # 去掉程序集部分
    if "," in odin_type:
        odin_type = odin_type.split(",", 1)[0]
    
    # 处理泛型类型
    if "`" in odin_type:
        odin_type = odin_type.split("`", 1)[0]
    
    # 提取最后一个类名
    if "." in odin_type:
        return odin_type.rsplit(".", 1)[1]
    
    return odin_type


def parse_type_string(type_str: Union[str, int]) -> Tuple[Optional[int], Optional[str]]:
    """
    解析类型字符串，提取索引和完整类型名
    
    Args:
        type_str: 如 "4|UnityEngine.Vector3, UnityEngine.CoreModule" 或 4
        
    Returns:
        (index, full_type_name) - index 可能为 None
    """
    if isinstance(type_str, int):
        return type_str, None
    
    if not type_str:
        return None, None
    
    if "|" in type_str:
        parts = type_str.split("|", 1)
        try:
            index = int(parts[0])
            return index, parts[1]
        except ValueError:
            return None, type_str
    
    return None, type_str


class OdinJsonParser:
    """
    Odin JSON 格式解析器
    
    支持的格式：
    - 类型引用 ($type): 首次 "index|Type, Assembly"，后续仅 index
    - 对象引用 ($id / $iref): 对象唯一标识和引用
    - 集合: $plength/$pcontent (基元), $rlength/$rcontent (引用)
    - Dictionary: $rcontent 包含 {$k, $v} 对象
    - Unity类型: 裸值数组格式
    - Nullable: 值或 null
    """

    def __init__(self):
        """初始化解析器"""
        # 类型缓存：index -> full_type_string
        self.type_cache: Dict[int, str] = {}
        # 对象缓存：$id -> resolved_object（用于处理 $iref）
        self.object_cache: Dict[int, Any] = {}

    def parse(self, json_str: str) -> Any:
        """
        解析 Odin JSON 字符串

        Args:
            json_str: Odin JSON 字符串

        Returns:
            解析后的 Python 对象
        """
        # 使用预处理函数解析非标准 Odin JSON
        raw_data = parse_odin_json_raw(json_str)

        # 清空缓存
        self.type_cache.clear()
        self.object_cache.clear()

        # 第一遍：收集所有类型定义
        self._collect_types(raw_data)

        # 第二遍：递归解析 Odin 特殊结构
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
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            return self.parse(f.read())

    def _collect_types(self, data: Any) -> None:
        """
        收集所有类型定义到缓存
        
        Args:
            data: 原始数据
        """
        if isinstance(data, dict):
            # 收集类型定义
            if '$type' in data:
                type_info = data['$type']
                if isinstance(type_info, str) and '|' in type_info:
                    index, full_type = parse_type_string(type_info)
                    if index is not None and full_type:
                        self.type_cache[index] = full_type
            
            # 递归处理所有值
            for value in data.values():
                self._collect_types(value)
        elif isinstance(data, list):
            for item in data:
                self._collect_types(item)

    def _get_type_name(self, type_info: Union[str, int]) -> Optional[str]:
        """
        获取完整类型名
        
        Args:
            type_info: 类型信息（可能是索引或完整字符串）
            
        Returns:
            完整类型名
        """
        if isinstance(type_info, int):
            return self.type_cache.get(type_info)
        
        if isinstance(type_info, str):
            if type_info.isdigit():
                return self.type_cache.get(int(type_info))
            
            index, full_type = parse_type_string(type_info)
            return full_type or type_info
        
        return None

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
        # 处理对象引用 $iref:N
        for key, value in list(data.items()):
            if isinstance(value, str) and value.startswith('$iref:'):
                try:
                    ref_id = int(value.split(':')[1])
                    if ref_id in self.object_cache:
                        data[key] = self.object_cache[ref_id]
                except (ValueError, IndexError):
                    pass

        # 处理集合类型：$rcontent 或 $pcontent
        if '$rcontent' in data or '$pcontent' in data:
            content = data.get('$rcontent') or data.get('$pcontent', [])
            
            # 检查是否为 Dictionary（包含 $k/$v 对象）
            if isinstance(content, list) and content:
                first_item = content[0]
                if isinstance(first_item, dict) and '$k' in first_item:
                    # Dictionary 格式
                    return self._parse_dictionary(content)
                # 检查是否为二维数组（包含 "ranks" 字符串）
                if isinstance(first_item, str) and first_item.startswith('ranks'):
                    return self._parse_multidim_array(content)
            
            # 普通数组/List
            if isinstance(content, list):
                return [self._resolve_odin_structure(item) for item in content]
            return content

        # 处理类型信息：$type
        if '$type' in data:
            type_info = data['$type']
            type_name = self._get_type_name(type_info)

            # 缓存对象（用于 $iref 引用）
            if '$id' in data:
                obj_id = data['$id']
                # 先占位，防止循环引用
                self.object_cache[obj_id] = None

            # 处理 Unity 特殊类型
            if type_name:
                result = self._parse_unity_type(data, type_name)
                if result is not None:
                    # 更新对象缓存
                    if '$id' in data:
                        self.object_cache[data['$id']] = result
                    return result

            # 处理 Nullable 类型
            if type_name and 'System.Nullable' in type_name:
                return self._parse_nullable(data)

        # 普通对象：递归处理所有字段（排除 Odin 元数据）
        result = {}
        for key, value in data.items():
            # 跳过 Odin 元数据字段
            if key.startswith('$'):
                # 保留 $type 用于类型识别
                if key == '$type':
                    type_name = self._get_type_name(value)
                    if type_name:
                        result['_odin_type'] = type_name
                continue

            result[key] = self._resolve_odin_structure(value)

        # 更新对象缓存
        if '$id' in data:
            self.object_cache[data['$id']] = result

        return result if result else data

    def _parse_unity_type(self, data: Dict[str, Any], type_name: str) -> Optional[Any]:
        """
        解析 Unity 特殊类型
        
        Args:
            data: 原始数据
            type_name: 完整类型名
            
        Returns:
            解析后的数据，如果不是Unity类型则返回 None
        """
        # 提取纯类型名（不含命名空间）
        simple_type = type_name.split(',')[0].strip()
        
        # 获取裸值（非元数据字段的数值）
        raw_values = self._extract_raw_values(data)
        
        # Vector3
        if 'Vector3Int' in simple_type:
            return self._make_vector3_int(raw_values)
        elif 'Vector3' in simple_type:
            return self._make_vector3(raw_values)
        
        # Vector2
        elif 'Vector2Int' in simple_type:
            return self._make_vector2_int(raw_values)
        elif 'Vector2' in simple_type:
            return self._make_vector2(raw_values)
        
        # Vector4
        elif 'Vector4' in simple_type:
            return self._make_vector4(raw_values)
        
        # Quaternion
        elif 'Quaternion' in simple_type:
            return self._make_quaternion(raw_values)
        
        # Color / Color32
        elif 'Color32' in simple_type:
            return self._make_color32(raw_values)
        elif 'Color' in simple_type:
            return self._make_color(raw_values)
        
        # Rect / RectInt
        elif 'RectInt' in simple_type:
            return self._make_rect_int(data)
        elif 'Rect' in simple_type:
            return self._make_rect(raw_values)
        
        # Bounds / BoundsInt
        elif 'BoundsInt' in simple_type:
            return self._make_bounds_int(data)
        elif 'Bounds' in simple_type:
            return self._make_bounds(data)
        
        # LayerMask
        elif 'LayerMask' in simple_type:
            return {'value': raw_values[0] if raw_values else 0}
        
        # GradientAlphaKey
        elif 'GradientAlphaKey' in simple_type:
            return {'alpha': raw_values[0] if len(raw_values) > 0 else 1.0,
                    'time': raw_values[1] if len(raw_values) > 1 else 0.0}
        
        # GradientColorKey
        elif 'GradientColorKey' in simple_type:
            # 第一个值是嵌套的 Color，第二个是 time
            color = None
            time = 0.0
            for key, value in data.items():
                if not key.startswith('$'):
                    if isinstance(value, dict):
                        color = self._resolve_odin_structure(value)
                    elif isinstance(value, (int, float)):
                        time = float(value)
            return {'color': color or {'r': 1, 'g': 1, 'b': 1, 'a': 1}, 'time': time}
        
        return None

    def _extract_raw_values(self, data: Dict[str, Any]) -> List[float]:
        """
        从字典中提取裸值（非元数据字段的数值）
        
        Odin 序列化 Unity 类型时使用整数键：{$type: "...", 0, 1, 2}
        """
        values = []
        
        # 首先尝试整数键（0, 1, 2, 3...）
        for i in range(10):  # 最多10个分量
            if i in data:
                val = data[i]
                if isinstance(val, (int, float)):
                    values.append(float(val))
            elif str(i) in data:
                val = data[str(i)]
                if isinstance(val, (int, float)):
                    values.append(float(val))
        
        if values:
            return values
        
        # 回退：提取所有非元数据的数值
        for key, value in data.items():
            if not str(key).startswith('$') and isinstance(value, (int, float)):
                values.append(float(value))
        
        return values

    def _make_vector2(self, values: List[float]) -> Dict[str, float]:
        """创建 Vector2"""
        return {
            'x': values[0] if len(values) > 0 else 0.0,
            'y': values[1] if len(values) > 1 else 0.0
        }

    def _make_vector2_int(self, values: List[float]) -> Dict[str, int]:
        """创建 Vector2Int"""
        return {
            'x': int(values[0]) if len(values) > 0 else 0,
            'y': int(values[1]) if len(values) > 1 else 0
        }

    def _make_vector3(self, values: List[float]) -> Dict[str, float]:
        """创建 Vector3"""
        return {
            'x': values[0] if len(values) > 0 else 0.0,
            'y': values[1] if len(values) > 1 else 0.0,
            'z': values[2] if len(values) > 2 else 0.0
        }

    def _make_vector3_int(self, values: List[float]) -> Dict[str, int]:
        """创建 Vector3Int"""
        return {
            'x': int(values[0]) if len(values) > 0 else 0,
            'y': int(values[1]) if len(values) > 1 else 0,
            'z': int(values[2]) if len(values) > 2 else 0
        }

    def _make_vector4(self, values: List[float]) -> Dict[str, float]:
        """创建 Vector4"""
        return {
            'x': values[0] if len(values) > 0 else 0.0,
            'y': values[1] if len(values) > 1 else 0.0,
            'z': values[2] if len(values) > 2 else 0.0,
            'w': values[3] if len(values) > 3 else 0.0
        }

    def _make_quaternion(self, values: List[float]) -> Dict[str, float]:
        """创建 Quaternion"""
        return {
            'x': values[0] if len(values) > 0 else 0.0,
            'y': values[1] if len(values) > 1 else 0.0,
            'z': values[2] if len(values) > 2 else 0.0,
            'w': values[3] if len(values) > 3 else 1.0
        }

    def _make_color(self, values: List[float]) -> Dict[str, float]:
        """创建 Color"""
        return {
            'r': values[0] if len(values) > 0 else 1.0,
            'g': values[1] if len(values) > 1 else 1.0,
            'b': values[2] if len(values) > 2 else 1.0,
            'a': values[3] if len(values) > 3 else 1.0
        }

    def _make_color32(self, values: List[float]) -> Dict[str, int]:
        """创建 Color32"""
        return {
            'r': int(values[0]) if len(values) > 0 else 255,
            'g': int(values[1]) if len(values) > 1 else 255,
            'b': int(values[2]) if len(values) > 2 else 255,
            'a': int(values[3]) if len(values) > 3 else 255
        }

    def _make_rect(self, values: List[float]) -> Dict[str, float]:
        """创建 Rect"""
        return {
            'x': values[0] if len(values) > 0 else 0.0,
            'y': values[1] if len(values) > 1 else 0.0,
            'width': values[2] if len(values) > 2 else 0.0,
            'height': values[3] if len(values) > 3 else 0.0
        }

    def _make_rect_int(self, data: Dict[str, Any]) -> Dict[str, int]:
        """创建 RectInt（可能没有裸值）"""
        return {
            'x': int(data.get('x', 0)),
            'y': int(data.get('y', 0)),
            'width': int(data.get('width', 0)),
            'height': int(data.get('height', 0))
        }

    def _make_bounds(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建 Bounds"""
        center = {'x': 0.0, 'y': 0.0, 'z': 0.0}
        size = {'x': 0.0, 'y': 0.0, 'z': 0.0}
        
        # Bounds 包含两个嵌套的 Vector3
        nested_vectors = []
        for key, value in data.items():
            if not str(key).startswith('$') and isinstance(value, dict):
                nested_vectors.append(self._resolve_odin_structure(value))
        
        if len(nested_vectors) >= 2:
            center = nested_vectors[0]
            size = nested_vectors[1]
        elif len(nested_vectors) == 1:
            center = nested_vectors[0]
        
        return {'center': center, 'size': size}

    def _make_bounds_int(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建 BoundsInt"""
        return {
            'position': {'x': 0, 'y': 0, 'z': 0},
            'size': {'x': 0, 'y': 0, 'z': 0}
        }

    def _parse_dictionary(self, content: List[Any]) -> Dict[str, Any]:
        """
        解析 Dictionary 格式
        
        Args:
            content: $rcontent 内容，包含 {$k, $v} 对象
            
        Returns:
            Python 字典
        """
        result = {}
        for item in content:
            if isinstance(item, dict) and '$k' in item and '$v' in item:
                key = self._resolve_odin_structure(item['$k'])
                value = self._resolve_odin_structure(item['$v'])
                result[key] = value
        return result

    def _parse_multidim_array(self, content: List[Any]) -> List[List[Any]]:
        """
        解析多维数组
        
        Args:
            content: 包含 "ranks: 2|3" 和数据的列表
            
        Returns:
            多维数组
        """
        if not content:
            return []
        
        # 解析维度信息
        ranks_info = content[0]  # "ranks": "2|3"
        if isinstance(ranks_info, str) and ranks_info.startswith('ranks'):
            # 提取维度
            dims_str = ranks_info.split(':')[1].strip().strip('"')
            dims = [int(d) for d in dims_str.split('|')]
            
            # 获取数据
            data = content[1:]
            
            # 重构为多维数组
            if len(dims) == 2:
                rows, cols = dims
                result = []
                for i in range(rows):
                    row = data[i * cols:(i + 1) * cols]
                    result.append([self._resolve_odin_structure(v) for v in row])
                return result
        
        return [self._resolve_odin_structure(v) for v in content]

    def _parse_nullable(self, data: Dict[str, Any]) -> Optional[Any]:
        """
        解析 Nullable 类型
        
        Args:
            data: 包含 Nullable 数据的字典
            
        Returns:
            值或 None
        """
        # Nullable 格式: {"$type": "...", value} 或 {"$type": "...", null}
        for key, value in data.items():
            if not str(key).startswith('$'):
                return self._resolve_odin_structure(value)
        
        # 检查是否有裸值
        raw_values = self._extract_raw_values(data)
        if raw_values:
            return raw_values[0]
        
        return None


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
    
    支持的格式（基于 odin_test_data.json）：
    - 类型引用: "$type": "index|FullType, Assembly"
    - 对象ID: "$id": N
    - 集合: $rlength/$rcontent (引用类型), $plength/$pcontent (基元类型)
    - Dictionary: $rcontent 包含 {$k, $v} 对象
    - Unity类型: 裸值数组格式
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
            result["tracks"] = self._serialize_list(
                tracks, 
                "System.Collections.Generic.List`1[[SkillSystem.Data.SkillTrack, Assembly-CSharp]], mscorlib",
                self._serialize_track
            )

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
        首次出现返回完整类型字符串，后续引用返回索引
        """
        if type_str not in self._type_registry:
            index = len(self._type_registry)
            self._type_registry[type_str] = index

        index = self._type_registry[type_str]
        return f"{index}|{type_str}"

    def _get_type_index(self, type_str: str) -> int:
        """获取类型索引（仅数字）"""
        if type_str not in self._type_registry:
            index = len(self._type_registry)
            self._type_registry[type_str] = index
        return self._type_registry[type_str]

    def _serialize_list(self, items: List[Any], list_type: str, 
                        item_serializer: callable) -> Dict[str, Any]:
        """序列化列表（通用方法）"""
        serialized_items = [item_serializer(item) for item in items]
        return {
            "$id": self._next_id(),
            "$type": self._get_type_ref(list_type),
            "$rlength": len(serialized_items),
            "$rcontent": serialized_items
        }

    def _serialize_primitive_array(self, items: List[Any], array_type: str) -> Dict[str, Any]:
        """序列化基元类型数组（使用 $plength/$pcontent）"""
        return {
            "$id": self._next_id(),
            "$type": self._get_type_ref(array_type),
            "$plength": len(items),
            "$pcontent": items
        }

    def _serialize_dict(self, data: Dict[str, Any], dict_type: str) -> Dict[str, Any]:
        """序列化字典"""
        content = []
        for k, v in data.items():
            content.append({
                "$k": k,
                "$v": self._serialize_value(v)
            })
        return {
            "$id": self._next_id(),
            "$type": self._get_type_ref(dict_type),
            "$rlength": len(content),
            "$rcontent": content
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
        result["actions"] = self._serialize_list(
            actions,
            "System.Collections.Generic.List`1[[SkillSystem.Actions.ISkillAction, Assembly-CSharp]], mscorlib",
            self._serialize_action
        )

        return result

    def _serialize_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """序列化单个 Action"""
        # 从 parameters 中提取 _odin_type
        parameters = action.get("parameters", {})
        odin_type = parameters.get("_odin_type", "")

        # 验证并解析 _odin_type 格式
        is_valid, type_name, error_msg = validate_odin_type(odin_type)
        
        if not is_valid:
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
        """序列化值（处理特殊类型）"""
        if value is None:
            return None
        
        if isinstance(value, dict):
            keys = set(value.keys())
            
            # Vector3
            if keys == {"x", "y", "z"}:
                return self._serialize_vector3(value)
            # Vector2
            elif keys == {"x", "y"}:
                return self._serialize_vector2(value)
            # Color
            elif keys == {"r", "g", "b", "a"}:
                return self._serialize_color(value)
            # Quaternion/Vector4
            elif keys == {"x", "y", "z", "w"}:
                return self._serialize_quaternion(value)
            # Rect
            elif keys == {"x", "y", "width", "height"}:
                return self._serialize_rect(value)
            # Bounds
            elif keys == {"center", "size"}:
                return self._serialize_bounds(value)
            # 普通字典（可能是嵌套对象）
            else:
                return {k: self._serialize_value(v) for k, v in value.items()}
        
        elif isinstance(value, list):
            return [self._serialize_value(item) for item in value]
        
        return value

    def _serialize_vector2(self, vec: Dict[str, float]) -> Dict[str, Any]:
        """序列化 Vector2"""
        return {
            "$type": self._get_type_ref("UnityEngine.Vector2, UnityEngine.CoreModule"),
            0: vec.get("x", 0.0),
            1: vec.get("y", 0.0)
        }

    def _serialize_vector3(self, vec: Dict[str, float]) -> Dict[str, Any]:
        """序列化 Vector3"""
        return {
            "$type": self._get_type_ref("UnityEngine.Vector3, UnityEngine.CoreModule"),
            0: vec.get("x", 0.0),
            1: vec.get("y", 0.0),
            2: vec.get("z", 0.0)
        }

    def _serialize_vector4(self, vec: Dict[str, float]) -> Dict[str, Any]:
        """序列化 Vector4"""
        return {
            "$type": self._get_type_ref("UnityEngine.Vector4, UnityEngine.CoreModule"),
            0: vec.get("x", 0.0),
            1: vec.get("y", 0.0),
            2: vec.get("z", 0.0),
            3: vec.get("w", 0.0)
        }

    def _serialize_quaternion(self, quat: Dict[str, float]) -> Dict[str, Any]:
        """序列化 Quaternion"""
        return {
            "$type": self._get_type_ref("UnityEngine.Quaternion, UnityEngine.CoreModule"),
            0: quat.get("x", 0.0),
            1: quat.get("y", 0.0),
            2: quat.get("z", 0.0),
            3: quat.get("w", 1.0)
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

    def _serialize_rect(self, rect: Dict[str, float]) -> Dict[str, Any]:
        """序列化 Rect"""
        return {
            "$type": self._get_type_ref("UnityEngine.Rect, UnityEngine.CoreModule"),
            0: rect.get("x", 0.0),
            1: rect.get("y", 0.0),
            2: rect.get("width", 0.0),
            3: rect.get("height", 0.0)
        }

    def _serialize_bounds(self, bounds: Dict[str, Any]) -> Dict[str, Any]:
        """序列化 Bounds"""
        center = bounds.get("center", {"x": 0, "y": 0, "z": 0})
        size = bounds.get("size", {"x": 0, "y": 0, "z": 0})
        return {
            "$type": self._get_type_ref("UnityEngine.Bounds, UnityEngine.CoreModule"),
            0: self._serialize_vector3(center),
            1: self._serialize_vector3(size)
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
    
    注意：此函数生成的是 Odin Serializer 的非标准 JSON 格式，
    其中 Vector3/Vector2/Color 等类型使用裸数组索引（如 0, 0, 1）而非标准键值对。

    Args:
        skill_data: LLM 生成的技能数据
        indent: 缩进空格数

    Returns:
        Odin 序列化格式的 JSON 字符串（非标准JSON）
    """
    odin_data = serialize_to_odin(skill_data)
    return odin_json_encode(odin_data, indent=indent)


def odin_json_encode(obj: Any, indent: int = 4, _level: int = 0) -> str:
    """
    自定义 Odin JSON 编码器
    
    生成 Unity Odin Serializer 期望的非标准 JSON 格式：
    - Vector3/Vector2/Color 使用裸数组索引: { "$type": "...", 0, 0, 1 }
    - 而非标准 JSON 的 { "$type": "...", "0": 0, "1": 0, "2": 1 }
    
    Args:
        obj: 要编码的对象
        indent: 缩进空格数
        _level: 当前缩进层级（内部使用）
        
    Returns:
        Odin 格式的 JSON 字符串
    """
    indent_str = " " * (indent * _level)
    next_indent = " " * (indent * (_level + 1))
    
    if obj is None:
        return "null"
    elif isinstance(obj, bool):
        return "true" if obj else "false"
    elif isinstance(obj, (int, float)):
        # 处理浮点数精度
        if isinstance(obj, float):
            if obj == int(obj):
                return f"{int(obj)}.0"
            return str(obj)
        return str(obj)
    elif isinstance(obj, str):
        # 转义字符串
        escaped = obj.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
        return f'"{escaped}"'
    elif isinstance(obj, list):
        if not obj:
            return "[]"
        items = [odin_json_encode(item, indent, _level + 1) for item in obj]
        return "[\n" + next_indent + (",\n" + next_indent).join(items) + "\n" + indent_str + "]"
    elif isinstance(obj, dict):
        if not obj:
            return "{}"
        
        # 检查是否为 Unity 类型（Vector3/Vector2/Color/Vector4）
        # 这些类型使用整数键 0, 1, 2, 3
        is_unity_type = "$type" in obj and any(isinstance(k, int) for k in obj.keys())
        
        parts = []
        for key, value in obj.items():
            encoded_value = odin_json_encode(value, indent, _level + 1)
            
            if isinstance(key, int) and is_unity_type:
                # Unity 类型的整数索引：使用裸值格式 (无键名)
                parts.append(encoded_value)
            else:
                # 标准键值对
                parts.append(f'"{key}": {encoded_value}')
        
        return "{\n" + next_indent + (",\n" + next_indent).join(parts) + "\n" + indent_str + "}"
    else:
        # 其他类型尝试转为字符串
        return f'"{str(obj)}"'


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

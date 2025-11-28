"""
参数深度验证模块
对照RAG检索的Action Schema验证生成的Action参数

验证内容：
1. 参数类型匹配（int/float/string/bool/enum）
2. 枚举值合法性
3. 数值范围约束（min/max/minValue/maxValue）
4. 必需参数检查
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationSeverity(str, Enum):
    """验证问题严重程度"""
    ERROR = "error"      # 必须修复，会导致运行时错误
    WARNING = "warning"  # 建议修复，可能影响效果
    INFO = "info"        # 提示信息，不影响运行


class ParameterValidationResult:
    """参数验证结果"""

    def __init__(self):
        self.errors: List[str] = []       # 错误列表
        self.warnings: List[str] = []     # 警告列表
        self.infos: List[str] = []        # 提示列表
        self.fixed_params: Dict[str, Any] = {}  # 自动修复的参数

    @property
    def is_valid(self) -> bool:
        """是否通过验证（无错误）"""
        return len(self.errors) == 0

    @property
    def has_issues(self) -> bool:
        """是否有任何问题"""
        return len(self.errors) > 0 or len(self.warnings) > 0

    def add_error(self, message: str):
        self.errors.append(message)

    def add_warning(self, message: str):
        self.warnings.append(message)

    def add_info(self, message: str):
        self.infos.append(message)

    def merge(self, other: 'ParameterValidationResult'):
        """合并另一个验证结果"""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.infos.extend(other.infos)
        self.fixed_params.update(other.fixed_params)


# 类型映射：Action Schema类型 -> Python类型
TYPE_MAPPING = {
    "int": (int,),
    "float": (int, float),  # float也接受int
    "string": (str,),
    "bool": (bool,),
    "Vector2": (dict,),
    "Vector3": (dict,),
    "Color": (dict,),
    "Sprite": (str, type(None)),  # Sprite引用用字符串或null
    "GameObject": (str, type(None)),
    "AudioClip": (str, type(None)),
}

# 需要特殊验证的复杂类型
COMPLEX_TYPES = {"Vector2", "Vector3", "Color"}


def validate_action_parameters(
    action: Dict[str, Any],
    action_schema: Dict[str, Any],
    strict_mode: bool = False
) -> ParameterValidationResult:
    """
    验证Action参数是否符合Schema定义

    Args:
        action: 生成的Action数据，包含frame, duration, parameters等
        action_schema: RAG检索的Action Schema定义
        strict_mode: 严格模式，未知参数也报错

    Returns:
        ParameterValidationResult 验证结果
    """
    result = ParameterValidationResult()

    params = action.get("parameters", {})
    if not params:
        result.add_error("parameters字段为空或缺失")
        return result

    # 获取Schema中的参数定义
    schema_params = action_schema.get("parameters", [])
    if not schema_params:
        result.add_warning("Action Schema中无参数定义，跳过参数验证")
        return result

    # 构建参数名到Schema的映射
    schema_map: Dict[str, Dict[str, Any]] = {}
    for param_schema in schema_params:
        param_name = param_schema.get("name", "")
        if param_name:
            schema_map[param_name] = param_schema

    # 验证每个生成的参数
    for param_name, param_value in params.items():
        # 跳过_odin_type
        if param_name == "_odin_type":
            continue

        if param_name not in schema_map:
            if strict_mode:
                result.add_error(f"参数'{param_name}'不在Schema定义中")
            else:
                result.add_info(f"参数'{param_name}'不在Schema定义中（可能是扩展参数）")
            continue

        param_schema = schema_map[param_name]

        # 执行验证
        param_result = _validate_single_parameter(
            param_name, param_value, param_schema
        )
        result.merge(param_result)

    # 检查必需参数（无默认值的参数）
    for param_name, param_schema in schema_map.items():
        if param_name not in params:
            # 检查是否有默认值
            default_value = param_schema.get("defaultValue", "")
            if not default_value or default_value in ("", "null", "\"\""):
                # 某些参数虽然无默认值但可选
                is_optional = _is_optional_parameter(param_name, param_schema)
                if not is_optional:
                    result.add_warning(f"参数'{param_name}'未提供且无默认值")

    return result


def _validate_single_parameter(
    param_name: str,
    param_value: Any,
    param_schema: Dict[str, Any]
) -> ParameterValidationResult:
    """
    验证单个参数

    Args:
        param_name: 参数名
        param_value: 参数值
        param_schema: 参数Schema定义

    Returns:
        验证结果
    """
    result = ParameterValidationResult()

    param_type = param_schema.get("type", "")
    is_enum = param_schema.get("isEnum", False)
    is_array = param_schema.get("isArray", False)
    enum_values = param_schema.get("enumValues", [])
    constraints = param_schema.get("constraints", {})

    # 1. 数组类型验证
    if is_array:
        if not isinstance(param_value, list):
            result.add_error(f"参数'{param_name}'应为数组，实际类型: {type(param_value).__name__}")
            return result
        # 验证数组元素（简化版，只检查非空）
        if len(param_value) == 0:
            result.add_info(f"参数'{param_name}'是空数组")
        return result

    # 2. 枚举类型验证
    if is_enum and enum_values:
        if param_value not in enum_values:
            result.add_error(
                f"参数'{param_name}'值'{param_value}'不在允许的枚举值中: {enum_values}"
            )
        return result

    # 3. 基础类型验证
    type_result = _validate_type(param_name, param_value, param_type)
    result.merge(type_result)

    # 4. 数值约束验证
    if param_type in ("int", "float") and isinstance(param_value, (int, float)):
        constraint_result = _validate_constraints(param_name, param_value, constraints)
        result.merge(constraint_result)

    # 5. 复杂类型验证（Vector3等）
    if param_type in COMPLEX_TYPES:
        complex_result = _validate_complex_type(param_name, param_value, param_type)
        result.merge(complex_result)

    return result


def _validate_type(
    param_name: str,
    param_value: Any,
    expected_type: str
) -> ParameterValidationResult:
    """验证参数类型"""
    result = ParameterValidationResult()

    # 处理null值
    if param_value is None:
        # 某些类型允许null（如Sprite、GameObject引用）
        nullable_types = {"Sprite", "GameObject", "AudioClip", "Transform"}
        if expected_type not in nullable_types:
            result.add_warning(f"参数'{param_name}'值为null，期望类型: {expected_type}")
        return result

    # 获取期望的Python类型
    expected_python_types = TYPE_MAPPING.get(expected_type)

    if expected_python_types is None:
        # 未知类型，可能是自定义枚举或复杂类型
        if expected_type.endswith("[]"):
            # 数组类型
            if not isinstance(param_value, list):
                result.add_error(f"参数'{param_name}'应为数组类型{expected_type}")
        # 其他未知类型不做严格检查
        return result

    if not isinstance(param_value, expected_python_types):
        actual_type = type(param_value).__name__
        result.add_error(
            f"参数'{param_name}'类型错误: 期望{expected_type}，实际{actual_type}"
        )

    return result


def _validate_constraints(
    param_name: str,
    param_value: float,
    constraints: Dict[str, str]
) -> ParameterValidationResult:
    """验证数值约束"""
    result = ParameterValidationResult()

    # 解析约束值
    min_value = _parse_number(constraints.get("minValue") or constraints.get("min"))
    max_value = _parse_number(constraints.get("maxValue") or constraints.get("max"))

    if min_value is not None and param_value < min_value:
        result.add_error(
            f"参数'{param_name}'值{param_value}小于最小值{min_value}"
        )

    if max_value is not None and param_value > max_value:
        result.add_error(
            f"参数'{param_name}'值{param_value}大于最大值{max_value}"
        )

    return result


def _validate_complex_type(
    param_name: str,
    param_value: Any,
    expected_type: str
) -> ParameterValidationResult:
    """验证复杂类型（Vector3等）"""
    result = ParameterValidationResult()

    if not isinstance(param_value, dict):
        result.add_error(
            f"参数'{param_name}'应为对象格式（{expected_type}），实际: {type(param_value).__name__}"
        )
        return result

    if expected_type == "Vector2":
        required_keys = {"x", "y"}
        missing = required_keys - set(param_value.keys())
        if missing:
            result.add_error(f"参数'{param_name}'(Vector2)缺少字段: {missing}")

    elif expected_type == "Vector3":
        required_keys = {"x", "y", "z"}
        missing = required_keys - set(param_value.keys())
        if missing:
            result.add_error(f"参数'{param_name}'(Vector3)缺少字段: {missing}")

    elif expected_type == "Color":
        # Color可以是rgba或rgb
        has_rgb = all(k in param_value for k in ["r", "g", "b"])
        if not has_rgb:
            result.add_error(f"参数'{param_name}'(Color)缺少r/g/b字段")

    return result


def _parse_number(value: Optional[str]) -> Optional[float]:
    """解析字符串为数值"""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _is_optional_parameter(param_name: str, param_schema: Dict[str, Any]) -> bool:
    """判断参数是否可选"""
    # 某些常见的可选参数
    optional_patterns = [
        "icon", "sprite", "prefab", "clip", "description",
        "tooltip", "infoBox", "visual", "effect"
    ]

    param_name_lower = param_name.lower()
    for pattern in optional_patterns:
        if pattern in param_name_lower:
            return True

    # 有默认值的参数可选
    default_value = param_schema.get("defaultValue", "")
    if default_value and default_value not in ("", "null"):
        return True

    return False


def get_action_schema_by_odin_type(
    odin_type: str,
    action_schemas: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    根据_odin_type查找对应的Action Schema

    Args:
        odin_type: _odin_type字符串，如 "6|SkillSystem.Actions.DamageAction, Assembly-CSharp"
        action_schemas: RAG检索的Action Schema列表

    Returns:
        匹配的Action Schema，未找到返回None
    """
    if not odin_type:
        return None

    # 从odin_type提取类型名
    # 格式: "ID|Namespace.TypeName, AssemblyName"
    type_name = ""
    if "|" in odin_type:
        type_part = odin_type.split("|", 1)[1]
        # 提取TypeName（去掉命名空间和程序集）
        if "." in type_part:
            parts = type_part.split(".")
            for i, part in enumerate(parts):
                if "," in part:
                    type_name = part.split(",")[0].strip()
                    break
                if i == len(parts) - 1:
                    type_name = part.split(",")[0].strip()

    if not type_name:
        # 回退：尝试直接匹配
        type_name = odin_type

    # 在schema列表中查找
    for schema in action_schemas:
        schema_type_name = schema.get("typeName", "")
        if schema_type_name == type_name:
            return schema

        # 也检查fullTypeName
        full_type_name = schema.get("fullTypeName", "")
        if type_name in full_type_name:
            return schema

    return None


def validate_batch_actions_deep(
    batch_actions: List[Dict[str, Any]],
    relevant_action_schemas: List[Dict[str, Any]],
    total_duration: int
) -> Tuple[List[str], List[str]]:
    """
    深度验证批次Actions

    Args:
        batch_actions: 批次生成的actions列表
        relevant_action_schemas: RAG检索的相关Action Schema列表
        total_duration: 技能总时长

    Returns:
        (errors, warnings) 元组
    """
    all_errors: List[str] = []
    all_warnings: List[str] = []

    for idx, action in enumerate(batch_actions):
        # 基础结构验证
        frame = action.get("frame")
        duration = action.get("duration")
        params = action.get("parameters", {})

        if not isinstance(frame, int) or frame < 0:
            all_errors.append(f"action[{idx}].frame无效: {frame}")
            continue

        if not isinstance(duration, int) or duration < 1:
            all_errors.append(f"action[{idx}].duration无效: {duration}")
            continue

        if frame + duration > total_duration:
            all_errors.append(
                f"action[{idx}]结束帧({frame + duration})超出总时长({total_duration})"
            )

        # 参数深度验证
        odin_type = params.get("_odin_type", "")
        if not odin_type:
            all_errors.append(f"action[{idx}].parameters缺少_odin_type")
            continue

        # 查找对应的Schema
        action_schema = get_action_schema_by_odin_type(odin_type, relevant_action_schemas)

        if action_schema:
            # 执行参数深度验证
            validation_result = validate_action_parameters(action, action_schema)

            for error in validation_result.errors:
                all_errors.append(f"action[{idx}]: {error}")

            for warning in validation_result.warnings:
                all_warnings.append(f"action[{idx}]: {warning}")
        else:
            # 未找到Schema，只做基础验证
            all_warnings.append(
                f"action[{idx}]: 未找到'{odin_type}'的Schema定义，跳过参数深度验证"
            )

    return all_errors, all_warnings


# ==================== 导出 ====================

__all__ = [
    "ValidationSeverity",
    "ParameterValidationResult",
    "validate_action_parameters",
    "validate_batch_actions_deep",
    "get_action_schema_by_odin_type",
]

"""
条件查询语法解析器
支持结构化查询，如: "DamageAction where baseDamage > 200"
"""

import re
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class ComparisonOperator(Enum):
    """比较运算符"""
    GT = ">"          # 大于
    LT = "<"          # 小于
    GTE = ">="        # 大于等于
    LTE = "<="        # 小于等于
    EQ = "="          # 等于
    NEQ = "!="        # 不等于
    CONTAINS = "contains"     # 包含（字符串）
    BETWEEN = "between"       # 区间


@dataclass
class QueryCondition:
    """查询条件"""
    parameter: str                    # 参数名，如 "baseDamage"
    operator: ComparisonOperator      # 运算符
    value: Any                        # 比较值
    value2: Optional[Any] = None      # 第二个值（用于between）


@dataclass
class QueryExpression:
    """查询表达式"""
    action_type: Optional[str] = None      # Action类型过滤
    track_name: Optional[str] = None       # 轨道名称过滤
    conditions: List[QueryCondition] = None  # 参数条件列表

    def __post_init__(self):
        if self.conditions is None:
            self.conditions = []


class QueryParser:
    """查询语法解析器"""

    # 支持的查询语法:
    # 1. "DamageAction"  - 只指定类型
    # 2. "DamageAction where baseDamage > 200"
    # 3. "DamageAction where baseDamage > 200 and damageType = 'Magical'"
    # 4. "track='Damage Track' and baseDamage between 100 and 300"
    # 5. "animationClipName contains 'Attack'"

    OPERATOR_PATTERNS = {
        ">=": ComparisonOperator.GTE,
        "<=": ComparisonOperator.LTE,
        ">": ComparisonOperator.GT,
        "<": ComparisonOperator.LT,
        "!=": ComparisonOperator.NEQ,
        "=": ComparisonOperator.EQ,
        "contains": ComparisonOperator.CONTAINS,
        "between": ComparisonOperator.BETWEEN,
    }

    def parse(self, query: str) -> QueryExpression:
        """
        解析查询字符串

        Args:
            query: 查询字符串

        Returns:
            QueryExpression对象

        Examples:
            >>> parser.parse("DamageAction where baseDamage > 200")
            QueryExpression(
                action_type="DamageAction",
                conditions=[
                    QueryCondition(parameter="baseDamage", operator=GT, value=200)
                ]
            )
        """
        query = query.strip()

        expr = QueryExpression()

        # 分割 action_type 和 where 子句
        if " where " in query.lower():
            parts = re.split(r'\s+where\s+', query, maxsplit=1, flags=re.IGNORECASE)
            action_part = parts[0].strip()
            where_part = parts[1].strip()
        else:
            action_part = query
            where_part = ""

        # 解析action_type（可选）
        if action_part and action_part.lower() != "all":
            expr.action_type = action_part

        # 解析where子句
        if where_part:
            expr.conditions = self._parse_where_clause(where_part)

        return expr

    def _parse_where_clause(self, where_clause: str) -> List[QueryCondition]:
        """
        解析where子句

        Args:
            where_clause: "baseDamage > 200 and damageType = 'Magical'"

        Returns:
            条件列表
        """
        conditions = []

        # 按 and/or 分割（这里简化只支持and）
        condition_strs = re.split(r'\s+and\s+', where_clause, flags=re.IGNORECASE)

        for cond_str in condition_strs:
            cond = self._parse_single_condition(cond_str.strip())
            if cond:
                conditions.append(cond)

        return conditions

    def _parse_single_condition(self, condition_str: str) -> Optional[QueryCondition]:
        """
        解析单个条件

        Args:
            condition_str: "baseDamage > 200" 或 "baseDamage between 100 and 300"

        Returns:
            QueryCondition对象
        """
        # 特殊处理 between
        between_match = re.match(
            r'(\w+)\s+between\s+(.+?)\s+and\s+(.+)',
            condition_str,
            re.IGNORECASE
        )
        if between_match:
            param = between_match.group(1)
            value1 = self._parse_value(between_match.group(2).strip())
            value2 = self._parse_value(between_match.group(3).strip())
            return QueryCondition(
                parameter=param,
                operator=ComparisonOperator.BETWEEN,
                value=value1,
                value2=value2
            )

        # 处理contains
        contains_match = re.match(
            r'(\w+)\s+contains\s+(.+)',
            condition_str,
            re.IGNORECASE
        )
        if contains_match:
            param = contains_match.group(1)
            value = self._parse_value(contains_match.group(2).strip())
            return QueryCondition(
                parameter=param,
                operator=ComparisonOperator.CONTAINS,
                value=value
            )

        # 处理常规比较运算符
        for op_str, op_enum in self.OPERATOR_PATTERNS.items():
            if op_str in ["contains", "between"]:
                continue  # 已单独处理

            if op_str in condition_str:
                parts = condition_str.split(op_str, maxsplit=1)
                if len(parts) == 2:
                    param = parts[0].strip()
                    value = self._parse_value(parts[1].strip())
                    return QueryCondition(
                        parameter=param,
                        operator=op_enum,
                        value=value
                    )

        return None

    def _parse_value(self, value_str: str) -> Any:
        """
        解析值（自动类型转换）

        Args:
            value_str: "'Magical'" 或 "200" 或 "true"

        Returns:
            转换后的值
        """
        value_str = value_str.strip()

        # 字符串（单引号或双引号）
        if (value_str.startswith("'") and value_str.endswith("'")) or \
           (value_str.startswith('"') and value_str.endswith('"')):
            return value_str[1:-1]

        # 布尔值
        if value_str.lower() == "true":
            return True
        if value_str.lower() == "false":
            return False

        # 数字
        try:
            if "." in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            pass

        # 默认返回字符串
        return value_str


class QueryEvaluator:
    """查询条件评估器"""

    def evaluate(
        self,
        expression: QueryExpression,
        action_data: Dict[str, Any],
        track_name: Optional[str] = None
    ) -> bool:
        """
        评估Action是否满足查询条件

        Args:
            expression: 查询表达式
            action_data: Action数据（包含参数）
            track_name: 轨道名称（可选）

        Returns:
            是否满足所有条件
        """
        # 检查Action类型
        if expression.action_type:
            actual_type = self._extract_action_type(action_data)
            if actual_type != expression.action_type:
                return False

        # 检查轨道名称
        if expression.track_name:
            if track_name != expression.track_name:
                return False

        # 检查所有参数条件（AND关系）
        for condition in expression.conditions:
            if not self._evaluate_condition(condition, action_data):
                return False

        return True

    def _evaluate_condition(
        self,
        condition: QueryCondition,
        action_data: Dict[str, Any]
    ) -> bool:
        """评估单个条件"""
        # 获取参数值
        actual_value = action_data.get(condition.parameter)

        if actual_value is None:
            return False

        # 根据运算符评估
        op = condition.operator

        if op == ComparisonOperator.GT:
            return self._compare_numbers(actual_value, condition.value, lambda a, b: a > b)

        elif op == ComparisonOperator.LT:
            return self._compare_numbers(actual_value, condition.value, lambda a, b: a < b)

        elif op == ComparisonOperator.GTE:
            return self._compare_numbers(actual_value, condition.value, lambda a, b: a >= b)

        elif op == ComparisonOperator.LTE:
            return self._compare_numbers(actual_value, condition.value, lambda a, b: a <= b)

        elif op == ComparisonOperator.EQ:
            return self._compare_equal(actual_value, condition.value)

        elif op == ComparisonOperator.NEQ:
            return not self._compare_equal(actual_value, condition.value)

        elif op == ComparisonOperator.CONTAINS:
            return self._compare_contains(actual_value, condition.value)

        elif op == ComparisonOperator.BETWEEN:
            return self._compare_between(actual_value, condition.value, condition.value2)

        return False

    def _compare_numbers(
        self,
        actual: Any,
        expected: Any,
        comparator: Callable[[float, float], bool]
    ) -> bool:
        """数值比较"""
        try:
            actual_num = float(actual)
            expected_num = float(expected)
            return comparator(actual_num, expected_num)
        except (ValueError, TypeError):
            return False

    def _compare_equal(self, actual: Any, expected: Any) -> bool:
        """相等比较（支持字符串不区分大小写）"""
        if isinstance(actual, str) and isinstance(expected, str):
            return actual.lower() == expected.lower()
        return actual == expected

    def _compare_contains(self, actual: Any, expected: Any) -> bool:
        """包含比较（字符串）"""
        if isinstance(actual, str):
            return str(expected).lower() in actual.lower()
        return False

    def _compare_between(self, actual: Any, min_val: Any, max_val: Any) -> bool:
        """区间比较"""
        try:
            actual_num = float(actual)
            min_num = float(min_val)
            max_num = float(max_val)
            return min_num <= actual_num <= max_num
        except (ValueError, TypeError):
            return False

    def _extract_action_type(self, action_data: Dict[str, Any]) -> Optional[str]:
        """从Action数据中提取类型名称"""
        # 优先使用已解析的action_type字段（来自索引）
        if "action_type" in action_data:
            return action_data["action_type"]

        # 回退到$type字段（原始JSON）
        type_str = action_data.get("$type", "")

        if "|" in type_str:
            # Odin格式: "4|SkillSystem.Actions.DamageAction"
            type_name = type_str.split("|")[1].split(",")[0]
            # 提取最后一部分: "DamageAction"
            return type_name.split(".")[-1]

        return None


# ==================== 便捷函数 ====================

def parse_query(query: str) -> QueryExpression:
    """解析查询字符串（便捷函数）"""
    parser = QueryParser()
    return parser.parse(query)


def evaluate_query(
    query: str,
    action_data: Dict[str, Any],
    track_name: Optional[str] = None
) -> bool:
    """
    评估Action是否满足查询条件（便捷函数）

    Args:
        query: 查询字符串，如 "DamageAction where baseDamage > 200"
        action_data: Action数据
        track_name: 轨道名称

    Returns:
        是否满足条件

    Example:
        >>> action = {
        ...     "$type": "4|SkillSystem.Actions.DamageAction",
        ...     "baseDamage": 250,
        ...     "damageType": "Magical"
        ... }
        >>> evaluate_query("DamageAction where baseDamage > 200", action)
        True
    """
    parser = QueryParser()
    evaluator = QueryEvaluator()

    expression = parser.parse(query)
    return evaluator.evaluate(expression, action_data, track_name)

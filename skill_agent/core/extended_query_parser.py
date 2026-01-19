"""
扩展查询解析器
支持：OR逻辑、嵌套条件、聚合查询 (GROUP BY, COUNT, AVG, MIN, MAX)
"""

import re
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from .query_parser import ComparisonOperator, QueryCondition


class LogicalOperator(Enum):
    """逻辑运算符"""
    AND = "and"
    OR = "or"
    NOT = "not"


class AggregateFunction(Enum):
    """聚合函数"""
    COUNT = "count"
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"


@dataclass
class ConditionNode:
    """条件节点 - 支持嵌套"""
    condition: Optional[QueryCondition] = None  # 叶子节点的条件
    operator: Optional[LogicalOperator] = None  # 逻辑运算符
    children: List['ConditionNode'] = field(default_factory=list)  # 子节点
    
    def is_leaf(self) -> bool:
        return self.condition is not None
    
    def is_compound(self) -> bool:
        return self.operator is not None and len(self.children) > 0


@dataclass
class AggregateClause:
    """聚合子句"""
    function: AggregateFunction
    field: str
    alias: Optional[str] = None


@dataclass
class GroupByClause:
    """GROUP BY子句"""
    fields: List[str] = field(default_factory=list)
    having: Optional[ConditionNode] = None


@dataclass
class OrderByClause:
    """ORDER BY子句"""
    field: str
    descending: bool = False


@dataclass
class ExtendedQueryExpression:
    """扩展查询表达式"""
    # SELECT部分
    select_fields: List[str] = field(default_factory=list)  # 选择的字段
    aggregates: List[AggregateClause] = field(default_factory=list)  # 聚合函数
    
    # FROM部分
    action_type: Optional[str] = None  # Action类型过滤
    track_name: Optional[str] = None   # 轨道名称过滤
    
    # WHERE部分
    where: Optional[ConditionNode] = None  # 条件树
    
    # GROUP BY部分
    group_by: Optional[GroupByClause] = None
    
    # ORDER BY部分
    order_by: List[OrderByClause] = field(default_factory=list)
    
    # LIMIT部分
    limit: Optional[int] = None
    offset: int = 0


class ExtendedQueryParser:
    """扩展查询解析器"""
    
    OPERATOR_PATTERNS = {
        ">=": ComparisonOperator.GTE,
        "<=": ComparisonOperator.LTE,
        "!=": ComparisonOperator.NEQ,
        ">": ComparisonOperator.GT,
        "<": ComparisonOperator.LT,
        "=": ComparisonOperator.EQ,
        "contains": ComparisonOperator.CONTAINS,
        "between": ComparisonOperator.BETWEEN,
        "like": ComparisonOperator.CONTAINS,  # LIKE映射到CONTAINS
        "in": ComparisonOperator.EQ,  # IN简化处理
    }
    
    def parse(self, query: str) -> ExtendedQueryExpression:
        """
        解析扩展查询语法
        
        支持的语法:
        - SELECT field1, field2, COUNT(*), AVG(baseDamage) FROM DamageAction
        - WHERE (baseDamage > 100 AND damageType = 'Fire') OR duration > 30
        - GROUP BY action_type HAVING COUNT(*) > 5
        - ORDER BY baseDamage DESC
        - LIMIT 10 OFFSET 5
        
        简化语法（兼容原有）:
        - DamageAction where baseDamage > 100 or duration > 30
        """
        query = query.strip()
        expr = ExtendedQueryExpression()
        
        # 检测是否是SQL风格查询
        query_upper = query.upper()
        is_sql_style = any(kw in query_upper for kw in ['SELECT', 'FROM', 'GROUP BY'])
        
        if is_sql_style:
            self._parse_sql_style(query, expr)
        else:
            self._parse_simple_style(query, expr)
        
        return expr
    
    def _parse_sql_style(self, query: str, expr: ExtendedQueryExpression):
        """解析SQL风格查询"""
        # 分割各个子句
        parts = self._split_clauses(query)
        
        # 解析SELECT
        if 'select' in parts:
            self._parse_select(parts['select'], expr)
        
        # 解析FROM
        if 'from' in parts:
            expr.action_type = parts['from'].strip()
        
        # 解析WHERE
        if 'where' in parts:
            expr.where = self._parse_condition_tree(parts['where'])
        
        # 解析GROUP BY
        if 'group_by' in parts:
            self._parse_group_by(parts['group_by'], expr)
        
        # 解析HAVING
        if 'having' in parts and expr.group_by:
            expr.group_by.having = self._parse_condition_tree(parts['having'])
        
        # 解析ORDER BY
        if 'order_by' in parts:
            self._parse_order_by(parts['order_by'], expr)
        
        # 解析LIMIT
        if 'limit' in parts:
            self._parse_limit(parts['limit'], expr)
    
    def _parse_simple_style(self, query: str, expr: ExtendedQueryExpression):
        """解析简化风格查询（兼容原有语法）"""
        # 分割action_type和where子句
        if " where " in query.lower():
            parts = re.split(r'\s+where\s+', query, maxsplit=1, flags=re.IGNORECASE)
            action_part = parts[0].strip()
            where_part = parts[1].strip()
        else:
            action_part = query
            where_part = ""
        
        # 解析action_type
        if action_part and action_part.lower() not in ['all', '*']:
            expr.action_type = action_part
        
        # 解析where子句（支持OR）
        if where_part:
            expr.where = self._parse_condition_tree(where_part)
    
    def _split_clauses(self, query: str) -> Dict[str, str]:
        """分割SQL子句"""
        parts = {}
        
        # 使用正则分割各个子句
        patterns = [
            (r'\bSELECT\b\s+(.+?)(?=\bFROM\b|\bWHERE\b|\bGROUP\s+BY\b|\bORDER\s+BY\b|\bLIMIT\b|$)', 'select'),
            (r'\bFROM\b\s+(\w+)', 'from'),
            (r'\bWHERE\b\s+(.+?)(?=\bGROUP\s+BY\b|\bHAVING\b|\bORDER\s+BY\b|\bLIMIT\b|$)', 'where'),
            (r'\bGROUP\s+BY\b\s+(.+?)(?=\bHAVING\b|\bORDER\s+BY\b|\bLIMIT\b|$)', 'group_by'),
            (r'\bHAVING\b\s+(.+?)(?=\bORDER\s+BY\b|\bLIMIT\b|$)', 'having'),
            (r'\bORDER\s+BY\b\s+(.+?)(?=\bLIMIT\b|$)', 'order_by'),
            (r'\bLIMIT\b\s+(.+?)$', 'limit'),
        ]
        
        for pattern, key in patterns:
            match = re.search(pattern, query, re.IGNORECASE | re.DOTALL)
            if match:
                parts[key] = match.group(1).strip()
        
        return parts
    
    def _parse_select(self, select_str: str, expr: ExtendedQueryExpression):
        """解析SELECT子句"""
        items = [item.strip() for item in select_str.split(',')]
        
        for item in items:
            # 检查是否是聚合函数
            agg_match = re.match(
                r'(COUNT|SUM|AVG|MIN|MAX)\s*\(\s*(\*|\w+)\s*\)(?:\s+AS\s+(\w+))?',
                item,
                re.IGNORECASE
            )
            
            if agg_match:
                func_name = agg_match.group(1).upper()
                field = agg_match.group(2)
                alias = agg_match.group(3)
                
                expr.aggregates.append(AggregateClause(
                    function=AggregateFunction[func_name],
                    field=field if field != '*' else '*',
                    alias=alias
                ))
            elif item != '*':
                expr.select_fields.append(item)
    
    def _parse_condition_tree(self, condition_str: str) -> ConditionNode:
        """
        解析条件树（支持AND/OR和括号嵌套）
        """
        condition_str = condition_str.strip()
        
        # 处理括号
        if condition_str.startswith('(') and self._find_matching_paren(condition_str, 0) == len(condition_str) - 1:
            condition_str = condition_str[1:-1].strip()
        
        # 查找顶层OR（优先级最低）
        or_pos = self._find_top_level_operator(condition_str, 'or')
        if or_pos >= 0:
            left = condition_str[:or_pos].strip()
            right = condition_str[or_pos + 2:].strip()
            return ConditionNode(
                operator=LogicalOperator.OR,
                children=[
                    self._parse_condition_tree(left),
                    self._parse_condition_tree(right)
                ]
            )
        
        # 查找顶层AND
        and_pos = self._find_top_level_operator(condition_str, 'and')
        if and_pos >= 0:
            left = condition_str[:and_pos].strip()
            right = condition_str[and_pos + 3:].strip()
            return ConditionNode(
                operator=LogicalOperator.AND,
                children=[
                    self._parse_condition_tree(left),
                    self._parse_condition_tree(right)
                ]
            )
        
        # 叶子节点：单个条件
        condition = self._parse_single_condition(condition_str)
        return ConditionNode(condition=condition)
    
    def _find_top_level_operator(self, s: str, op: str) -> int:
        """查找顶层逻辑运算符位置（不在括号内）"""
        depth = 0
        i = 0
        s_lower = s.lower()
        
        while i < len(s):
            if s[i] == '(':
                depth += 1
            elif s[i] == ')':
                depth -= 1
            elif depth == 0:
                # 检查是否匹配运算符
                if s_lower[i:i+len(op)] == op:
                    # 确保是独立的词
                    before_ok = i == 0 or not s[i-1].isalnum()
                    after_ok = i + len(op) >= len(s) or not s[i+len(op)].isalnum()
                    if before_ok and after_ok:
                        return i
            i += 1
        
        return -1
    
    def _find_matching_paren(self, s: str, start: int) -> int:
        """查找匹配的右括号"""
        depth = 0
        for i in range(start, len(s)):
            if s[i] == '(':
                depth += 1
            elif s[i] == ')':
                depth -= 1
                if depth == 0:
                    return i
        return -1
    
    def _parse_single_condition(self, condition_str: str) -> Optional[QueryCondition]:
        """解析单个条件"""
        condition_str = condition_str.strip()
        
        # 处理BETWEEN
        between_match = re.match(
            r'(\w+)\s+between\s+(.+?)\s+and\s+(.+)',
            condition_str,
            re.IGNORECASE
        )
        if between_match:
            return QueryCondition(
                parameter=between_match.group(1),
                operator=ComparisonOperator.BETWEEN,
                value=self._parse_value(between_match.group(2)),
                value2=self._parse_value(between_match.group(3))
            )
        
        # 处理CONTAINS/LIKE
        contains_match = re.match(
            r'(\w+)\s+(contains|like)\s+(.+)',
            condition_str,
            re.IGNORECASE
        )
        if contains_match:
            return QueryCondition(
                parameter=contains_match.group(1),
                operator=ComparisonOperator.CONTAINS,
                value=self._parse_value(contains_match.group(3))
            )
        
        # 处理IN
        in_match = re.match(
            r'(\w+)\s+in\s*\((.+)\)',
            condition_str,
            re.IGNORECASE
        )
        if in_match:
            values = [self._parse_value(v.strip()) for v in in_match.group(2).split(',')]
            return QueryCondition(
                parameter=in_match.group(1),
                operator=ComparisonOperator.EQ,
                value=values  # 存储为列表
            )
        
        # 处理常规比较运算符
        for op_str, op_enum in self.OPERATOR_PATTERNS.items():
            if op_str in ['contains', 'between', 'like', 'in']:
                continue
            
            if op_str in condition_str:
                parts = condition_str.split(op_str, maxsplit=1)
                if len(parts) == 2:
                    return QueryCondition(
                        parameter=parts[0].strip(),
                        operator=op_enum,
                        value=self._parse_value(parts[1].strip())
                    )
        
        return None
    
    def _parse_value(self, value_str: str) -> Any:
        """解析值"""
        value_str = value_str.strip()
        
        # 字符串
        if (value_str.startswith("'") and value_str.endswith("'")) or \
           (value_str.startswith('"') and value_str.endswith('"')):
            return value_str[1:-1]
        
        # 布尔值
        if value_str.lower() == 'true':
            return True
        if value_str.lower() == 'false':
            return False
        
        # NULL
        if value_str.lower() == 'null':
            return None
        
        # 数字
        try:
            if '.' in value_str:
                return float(value_str)
            return int(value_str)
        except ValueError:
            pass
        
        return value_str
    
    def _parse_group_by(self, group_str: str, expr: ExtendedQueryExpression):
        """解析GROUP BY"""
        fields = [f.strip() for f in group_str.split(',')]
        expr.group_by = GroupByClause(fields=fields)
    
    def _parse_order_by(self, order_str: str, expr: ExtendedQueryExpression):
        """解析ORDER BY"""
        items = [item.strip() for item in order_str.split(',')]
        
        for item in items:
            parts = item.split()
            field = parts[0]
            desc = len(parts) > 1 and parts[1].upper() == 'DESC'
            expr.order_by.append(OrderByClause(field=field, descending=desc))
    
    def _parse_limit(self, limit_str: str, expr: ExtendedQueryExpression):
        """解析LIMIT"""
        parts = limit_str.split()
        expr.limit = int(parts[0])
        
        # 检查OFFSET
        if len(parts) > 1:
            if parts[1].upper() == 'OFFSET':
                expr.offset = int(parts[2])
            else:
                expr.offset = int(parts[1])


class ExtendedQueryEvaluator:
    """扩展查询评估器"""
    
    def evaluate_condition(
        self,
        node: ConditionNode,
        data: Dict[str, Any]
    ) -> bool:
        """评估条件树"""
        if node.is_leaf():
            return self._evaluate_single(node.condition, data)
        
        if node.operator == LogicalOperator.AND:
            return all(self.evaluate_condition(child, data) for child in node.children)
        
        if node.operator == LogicalOperator.OR:
            return any(self.evaluate_condition(child, data) for child in node.children)
        
        if node.operator == LogicalOperator.NOT:
            return not self.evaluate_condition(node.children[0], data)
        
        return True
    
    def _evaluate_single(self, cond: QueryCondition, data: Dict[str, Any]) -> bool:
        """评估单个条件"""
        if cond is None:
            return True
        
        actual = data.get(cond.parameter)
        if actual is None:
            # 尝试从parameters子字典获取
            params = data.get('parameters', {})
            actual = params.get(cond.parameter)
        
        if actual is None:
            return False
        
        op = cond.operator
        expected = cond.value
        
        if op == ComparisonOperator.EQ:
            if isinstance(expected, list):
                return actual in expected
            return self._compare_equal(actual, expected)
        
        if op == ComparisonOperator.NEQ:
            return not self._compare_equal(actual, expected)
        
        if op == ComparisonOperator.GT:
            return self._compare_numbers(actual, expected, lambda a, b: a > b)
        
        if op == ComparisonOperator.LT:
            return self._compare_numbers(actual, expected, lambda a, b: a < b)
        
        if op == ComparisonOperator.GTE:
            return self._compare_numbers(actual, expected, lambda a, b: a >= b)
        
        if op == ComparisonOperator.LTE:
            return self._compare_numbers(actual, expected, lambda a, b: a <= b)
        
        if op == ComparisonOperator.CONTAINS:
            return self._compare_contains(actual, expected)
        
        if op == ComparisonOperator.BETWEEN:
            return self._compare_between(actual, expected, cond.value2)
        
        return False
    
    def _compare_equal(self, actual: Any, expected: Any) -> bool:
        if isinstance(actual, str) and isinstance(expected, str):
            return actual.lower() == expected.lower()
        return actual == expected
    
    def _compare_numbers(self, actual: Any, expected: Any, op: Callable) -> bool:
        try:
            return op(float(actual), float(expected))
        except (ValueError, TypeError):
            return False
    
    def _compare_contains(self, actual: Any, expected: Any) -> bool:
        if isinstance(actual, str):
            return str(expected).lower() in actual.lower()
        return False
    
    def _compare_between(self, actual: Any, min_val: Any, max_val: Any) -> bool:
        try:
            a = float(actual)
            return float(min_val) <= a <= float(max_val)
        except (ValueError, TypeError):
            return False
    
    def aggregate(
        self,
        data: List[Dict[str, Any]],
        aggregates: List[AggregateClause],
        group_by: Optional[GroupByClause] = None
    ) -> List[Dict[str, Any]]:
        """执行聚合计算"""
        if not group_by:
            # 无分组，整体聚合
            result = {}
            for agg in aggregates:
                result[agg.alias or f"{agg.function.value}_{agg.field}"] = \
                    self._compute_aggregate(data, agg)
            return [result]
        
        # 分组聚合
        groups: Dict[tuple, List[Dict]] = {}
        for item in data:
            key = tuple(item.get(f) for f in group_by.fields)
            if key not in groups:
                groups[key] = []
            groups[key].append(item)
        
        results = []
        for key, group_data in groups.items():
            row = {}
            # 添加分组字段
            for i, field in enumerate(group_by.fields):
                row[field] = key[i]
            # 计算聚合
            for agg in aggregates:
                row[agg.alias or f"{agg.function.value}_{agg.field}"] = \
                    self._compute_aggregate(group_data, agg)
            results.append(row)
        
        # 应用HAVING
        if group_by.having:
            results = [r for r in results if self.evaluate_condition(group_by.having, r)]
        
        return results
    
    def _compute_aggregate(
        self,
        data: List[Dict[str, Any]],
        agg: AggregateClause
    ) -> Any:
        """计算单个聚合值"""
        if agg.function == AggregateFunction.COUNT:
            if agg.field == '*':
                return len(data)
            return sum(1 for d in data if d.get(agg.field) is not None)
        
        values = []
        for d in data:
            v = d.get(agg.field)
            if v is None:
                v = d.get('parameters', {}).get(agg.field)
            if v is not None:
                try:
                    values.append(float(v))
                except (ValueError, TypeError):
                    pass
        
        if not values:
            return None
        
        if agg.function == AggregateFunction.SUM:
            return sum(values)
        if agg.function == AggregateFunction.AVG:
            return round(sum(values) / len(values), 2)
        if agg.function == AggregateFunction.MIN:
            return min(values)
        if agg.function == AggregateFunction.MAX:
            return max(values)
        
        return None

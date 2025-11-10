"""
结构化查询引擎
集成细粒度索引、查询解析和缓存机制
"""

import time
from typing import Dict, List, Any, Optional
from pathlib import Path
from functools import lru_cache
from collections import OrderedDict

from query_parser import QueryParser, QueryEvaluator, QueryExpression
from fine_grained_indexer import FineGrainedIndexer
from chunked_json_store import ChunkedJsonStore


class LRUCache:
    """简单的LRU缓存实现"""

    def __init__(self, max_size: int = 100):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key in self.cache:
            # 移到末尾（最近使用）
            self.cache.move_to_end(key)
            self.hits += 1
            return self.cache[key]
        else:
            self.misses += 1
            return None

    def set(self, key: str, value: Any):
        """设置缓存值"""
        if key in self.cache:
            # 更新并移到末尾
            self.cache.move_to_end(key)
        self.cache[key] = value

        # 超过最大容量，删除最早的
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)

    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate, 4)
        }


class StructuredQueryEngine:
    """结构化查询引擎"""

    def __init__(
        self,
        skills_dir: str = "../../ai_agent_for_skill/Assets/Skills",
        cache_size: int = 100
    ):
        """
        Args:
            skills_dir: 技能文件目录
            cache_size: 缓存大小
        """
        self.indexer = FineGrainedIndexer(skills_dir)
        self.parser = QueryParser()
        self.evaluator = QueryEvaluator()
        self.json_store = ChunkedJsonStore()

        # 查询结果缓存
        self.query_cache = LRUCache(max_size=cache_size)

        # 统计摘要缓存（用于频繁访问的统计数据）
        self.stats_cache = LRUCache(max_size=20)

    def query(
        self,
        query_str: str,
        limit: int = 100,
        include_context: bool = True,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        执行结构化查询

        Args:
            query_str: 查询字符串，如 "DamageAction where baseDamage > 200"
            limit: 最大返回结果数
            include_context: 是否包含上下文信息（轨道、技能名称等）
            use_cache: 是否使用缓存

        Returns:
            {
                "results": [
                    {
                        "skill_name": "Flame Shockwave",
                        "skill_file": "FlameShockwave.json",
                        "track_name": "Damage Track",
                        "action_type": "DamageAction",
                        "action_index": 0,
                        "json_path": "tracks.$rcontent[2].actions.$rcontent[0]",
                        "line_number": 145,
                        "frame": 10,
                        "duration": 20,
                        "parameters": {...},
                        "summary": "..."
                    }
                ],
                "total_matches": 15,
                "query_time_ms": 123,
                "cache_hit": false
            }
        """
        start_time = time.time()

        # 检查缓存
        cache_key = f"{query_str}|{limit}|{include_context}"
        if use_cache:
            cached_result = self.query_cache.get(cache_key)
            if cached_result is not None:
                cached_result["cache_hit"] = True
                cached_result["query_time_ms"] = round((time.time() - start_time) * 1000, 2)
                return cached_result

        # 解析查询
        expression = self.parser.parse(query_str)

        # 执行查询
        results = self._execute_query(expression, include_context)

        # 限制结果数量
        limited_results = results[:limit]

        # 构建返回数据
        response = {
            "results": limited_results,
            "total_matches": len(results),
            "returned_count": len(limited_results),
            "query_time_ms": round((time.time() - start_time) * 1000, 2),
            "cache_hit": False
        }

        # 缓存结果
        if use_cache:
            self.query_cache.set(cache_key, response)

        return response

    def _execute_query(
        self,
        expression: QueryExpression,
        include_context: bool
    ) -> List[Dict[str, Any]]:
        """执行查询，遍历索引"""
        results = []

        index_data = self.indexer.get_index()

        # 遍历所有技能文件
        for file_path, file_index in index_data["files"].items():
            skill_name = file_index.get("skill_name", "Unknown")

            # 遍历所有轨道
            for track in file_index.get("tracks", []):
                track_name = track.get("track_name")

                # 遍历所有Action
                for action in track.get("actions", []):
                    # 评估是否满足条件
                    if self.evaluator.evaluate(expression, action, track_name):
                        result_item = {
                            "action_type": action["action_type"],
                            "action_index": action["action_index"],
                            "json_path": action["json_path"],
                            "line_number": action["line_number"],
                            "frame": action["frame"],
                            "duration": action["duration"],
                            "parameters": action["parameters"],
                            "summary": action["summary"]
                        }

                        # 添加上下文信息
                        if include_context:
                            result_item["skill_name"] = skill_name
                            result_item["skill_file"] = Path(file_path).name
                            result_item["track_name"] = track_name
                            result_item["track_index"] = track["track_index"]

                        results.append(result_item)

        return results

    def get_action_detail(
        self,
        skill_file: str,
        json_path: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取Action的完整详细信息（包含原始JSON）

        Args:
            skill_file: 技能文件名
            json_path: Action的JSON路径

        Returns:
            完整的Action数据
        """
        skills_dir = Path(self.indexer.skills_dir)
        full_path = skills_dir / skill_file

        if not full_path.exists():
            return None

        # 使用ChunkedJsonStore加载片段
        chunk = self.json_store.load_by_path(
            str(full_path),
            json_path,
            include_context=True
        )

        return chunk

    def get_statistics(
        self,
        query_str: Optional[str] = None,
        group_by: str = "action_type",
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        获取查询统计信息

        Args:
            query_str: 查询字符串（可选，不指定则统计全部）
            group_by: 分组字段，如 "action_type", "track_name"
            use_cache: 是否使用缓存

        Returns:
            {
                "total_actions": 120,
                "groups": {
                    "DamageAction": {
                        "count": 45,
                        "avg_baseDamage": 175.3,
                        "min_baseDamage": 50,
                        "max_baseDamage": 500
                    },
                    ...
                }
            }
        """
        cache_key = f"stats|{query_str}|{group_by}"
        if use_cache:
            cached = self.stats_cache.get(cache_key)
            if cached:
                return cached

        # 执行查询获取结果
        if query_str:
            query_result = self.query(query_str, limit=10000, use_cache=False)
            actions = query_result["results"]
        else:
            # 获取所有Action
            actions = []
            index_data = self.indexer.get_index()
            for file_index in index_data["files"].values():
                for track in file_index.get("tracks", []):
                    for action in track.get("actions", []):
                        actions.append({
                            **action,
                            "track_name": track["track_name"]
                        })

        # 分组统计
        groups = {}
        for action in actions:
            group_key = action.get(group_by, "Unknown")

            if group_key not in groups:
                groups[group_key] = {
                    "count": 0,
                    "actions": []
                }

            groups[group_key]["count"] += 1
            groups[group_key]["actions"].append(action)

        # 计算每组的参数统计
        for group_key, group_data in groups.items():
            group_actions = group_data["actions"]

            # 收集所有参数
            param_stats = {}
            for action in group_actions:
                for param_name, param_value in action.get("parameters", {}).items():
                    if param_name not in param_stats:
                        param_stats[param_name] = []

                    # 只统计数值参数
                    if isinstance(param_value, (int, float)):
                        param_stats[param_name].append(param_value)

            # 计算参数的min/max/avg
            for param_name, values in param_stats.items():
                if values:
                    group_data[f"avg_{param_name}"] = round(sum(values) / len(values), 2)
                    group_data[f"min_{param_name}"] = min(values)
                    group_data[f"max_{param_name}"] = max(values)

            # 删除临时的actions列表
            del group_data["actions"]

        stats = {
            "total_actions": len(actions),
            "groups": groups
        }

        # 缓存结果
        if use_cache:
            self.stats_cache.set(cache_key, stats)

        return stats

    def rebuild_index(self, force: bool = False) -> Dict[str, Any]:
        """
        重建细粒度索引

        Args:
            force: 强制重建所有文件

        Returns:
            索引统计信息
        """
        # 清空缓存
        self.query_cache.clear()
        self.stats_cache.clear()

        # 重建索引
        return self.indexer.index_all_skills(force_rebuild=force)

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            "query_cache": self.query_cache.get_stats(),
            "stats_cache": self.stats_cache.get_stats()
        }

    def clear_cache(self):
        """清空所有缓存"""
        self.query_cache.clear()
        self.stats_cache.clear()


# ==================== 便捷函数 ====================

def query_skills(
    query_str: str,
    limit: int = 100,
    skills_dir: str = None
) -> Dict[str, Any]:
    """
    执行结构化查询（便捷函数）

    Args:
        query_str: 查询字符串
        limit: 最大返回结果数
        skills_dir: 技能目录（可选）

    Returns:
        查询结果

    Examples:
        >>> query_skills("DamageAction where baseDamage > 200")
        {
            "results": [...],
            "total_matches": 15,
            "query_time_ms": 45.2
        }

        >>> query_skills("baseDamage between 100 and 300")
        >>> query_skills("animationClipName contains 'Attack'")
    """
    if skills_dir:
        engine = StructuredQueryEngine(skills_dir)
    else:
        engine = StructuredQueryEngine()

    return engine.query(query_str, limit=limit)

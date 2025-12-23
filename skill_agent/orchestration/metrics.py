"""
性能监控模块
P2-4: 提供 LLM 调用延迟、RAG 检索耗时、验证循环次数等指标统计
"""

import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@dataclass
class MetricRecord:
    """单次指标记录"""
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)


class PerformanceMetrics:
    """
    性能指标收集器（单例模式）
    
    收集的指标：
    - llm_latency: LLM 调用延迟（秒）
    - llm_ttfb: LLM 首字节延迟（秒）
    - rag_skill_search: RAG 技能检索耗时（秒）
    - rag_action_search: RAG Action 检索耗时（秒）
    - validation_attempts: 验证循环次数
    - json_parse_time: JSON 解析耗时（秒）
    - total_generation_time: 总生成耗时（秒）
    """
    
    _instance = None
    _class_lock = Lock()  # 类级别锁，用于单例创建
    
    def __new__(cls):
        if cls._instance is None:
            with cls._class_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self._metrics: Dict[str, List[MetricRecord]] = {}
        self._counters: Dict[str, int] = {}
        self._data_lock = Lock()  # 实例级别锁，用于数据操作
        self._max_records = 1000  # 每种指标最多保留1000条记录
        
        logger.info("PerformanceMetrics initialized")
    
    def record(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """
        记录一个指标值
        
        Args:
            name: 指标名称
            value: 指标值
            tags: 可选的标签（如 model_name, thread_id 等）
        """
        with self._data_lock:
            if name not in self._metrics:
                self._metrics[name] = []
            
            record = MetricRecord(name=name, value=value, tags=tags or {})
            self._metrics[name].append(record)
            
            # 限制记录数量
            if len(self._metrics[name]) > self._max_records:
                self._metrics[name] = self._metrics[name][-self._max_records:]
        
        logger.debug(f"Metric recorded: {name}={value:.3f} tags={tags}")
    
    def increment(self, name: str, amount: int = 1):
        """增加计数器"""
        with self._data_lock:
            self._counters[name] = self._counters.get(name, 0) + amount
    
    def get_counter(self, name: str) -> int:
        """获取计数器值"""
        return self._counters.get(name, 0)
    
    @contextmanager
    def timer(self, name: str, tags: Optional[Dict[str, str]] = None):
        """
        计时上下文管理器
        
        Usage:
            with metrics.timer("llm_latency", {"model": "deepseek"}):
                response = llm.invoke(...)
        """
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            self.record(name, elapsed, tags)
    
    def get_stats(self, name: str) -> Dict[str, Any]:
        """
        获取指标统计信息
        
        Returns:
            {
                "count": int,
                "avg": float,
                "min": float,
                "max": float,
                "p50": float,
                "p95": float,
                "p99": float,
                "last": float
            }
        """
        with self._data_lock:
            records = self._metrics.get(name, [])
        
        if not records:
            return {"count": 0}
        
        values = sorted([r.value for r in records])
        count = len(values)
        
        return {
            "count": count,
            "avg": sum(values) / count,
            "min": values[0],
            "max": values[-1],
            "p50": values[int(count * 0.5)],
            "p95": values[int(count * 0.95)] if count >= 20 else values[-1],
            "p99": values[int(count * 0.99)] if count >= 100 else values[-1],
            "last": records[-1].value
        }
    
    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有指标的统计信息"""
        stats = {}
        with self._data_lock:
            metric_names = list(self._metrics.keys())
            counter_names = list(self._counters.keys())
        
        for name in metric_names:
            stats[name] = self.get_stats(name)
        
        stats["counters"] = {name: self.get_counter(name) for name in counter_names}
        return stats
    
    def reset(self):
        """重置所有指标"""
        with self._data_lock:
            self._metrics.clear()
            self._counters.clear()
        logger.info("PerformanceMetrics reset")


# 全局单例
metrics = PerformanceMetrics()


# 便捷函数
def record_llm_latency(latency: float, model: str = "deepseek-reasoner"):
    """记录 LLM 调用延迟"""
    metrics.record("llm_latency", latency, {"model": model})


def record_llm_ttfb(ttfb: float, model: str = "deepseek-reasoner"):
    """记录 LLM 首字节延迟"""
    metrics.record("llm_ttfb", ttfb, {"model": model})


def record_rag_search(latency: float, search_type: str = "skill"):
    """记录 RAG 检索耗时"""
    metrics.record(f"rag_{search_type}_search", latency)


def record_validation_attempt(thread_id: str = ""):
    """记录验证尝试次数"""
    metrics.increment("validation_attempts")


def get_performance_summary() -> Dict[str, Any]:
    """获取性能摘要"""
    return metrics.get_all_stats()

"""
RAG 性能监控模块
用于追踪检索延迟、缓存命中率等关键指标
"""

import time
import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from collections import deque
from functools import wraps
from contextlib import contextmanager
import threading
import statistics

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    operation: str
    duration_ms: float
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class PerformanceMonitor:
    """
    RAG 性能监控器
    
    追踪以下指标：
    - 嵌入生成延迟
    - 向量检索延迟
    - BM25 检索延迟
    - 重排序延迟
    - 总检索延迟
    - 缓存命中率
    """
    
    def __init__(self, max_history: int = 1000, slow_threshold_ms: float = 500.0):
        """
        Args:
            max_history: 保留的历史记录数量
            slow_threshold_ms: 慢查询阈值（毫秒）
        """
        self.max_history = max_history
        self.slow_threshold_ms = slow_threshold_ms
        
        # 按操作类型存储历史记录
        self._history: Dict[str, deque] = {}
        
        # 统计计数器
        self._counters: Dict[str, int] = {
            'total_operations': 0,
            'slow_operations': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # 线程锁
        self._lock = threading.Lock()
        
        logger.info(f"PerformanceMonitor initialized (slow_threshold={slow_threshold_ms}ms)")
    
    def record(self, operation: str, duration_ms: float, metadata: Optional[Dict] = None):
        """
        记录一次操作的性能指标
        
        Args:
            operation: 操作名称（如 "embedding", "vector_search", "bm25_search"）
            duration_ms: 耗时（毫秒）
            metadata: 额外元数据
        """
        with self._lock:
            # 初始化操作历史队列
            if operation not in self._history:
                self._history[operation] = deque(maxlen=self.max_history)
            
            # 记录指标
            metric = PerformanceMetrics(
                operation=operation,
                duration_ms=duration_ms,
                timestamp=time.time(),
                metadata=metadata or {}
            )
            self._history[operation].append(metric)
            
            # 更新计数器
            self._counters['total_operations'] += 1
            if duration_ms > self.slow_threshold_ms:
                self._counters['slow_operations'] += 1
                logger.warning(f"Slow operation detected: {operation} took {duration_ms:.2f}ms")
    
    def record_cache_hit(self):
        """记录缓存命中"""
        with self._lock:
            self._counters['cache_hits'] += 1
    
    def record_cache_miss(self):
        """记录缓存未命中"""
        with self._lock:
            self._counters['cache_misses'] += 1
    
    @contextmanager
    def measure(self, operation: str, metadata: Optional[Dict] = None):
        """
        上下文管理器，用于测量操作耗时
        
        Usage:
            with monitor.measure("embedding"):
                embedding = model.encode(text)
        """
        start_time = time.perf_counter()
        try:
            yield
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.record(operation, duration_ms, metadata)
    
    def get_statistics(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """
        获取性能统计信息
        
        Args:
            operation: 指定操作名称，None 返回所有操作的统计
        
        Returns:
            统计信息字典
        """
        with self._lock:
            if operation:
                return self._get_operation_stats(operation)
            
            # 返回所有操作的统计
            stats = {
                'counters': self._counters.copy(),
                'cache_hit_rate': self._calculate_cache_hit_rate(),
                'operations': {}
            }
            
            for op_name in self._history:
                stats['operations'][op_name] = self._get_operation_stats(op_name)
            
            return stats
    
    def _get_operation_stats(self, operation: str) -> Dict[str, Any]:
        """获取单个操作的统计信息"""
        if operation not in self._history or not self._history[operation]:
            return {'count': 0}
        
        durations = [m.duration_ms for m in self._history[operation]]
        
        return {
            'count': len(durations),
            'min_ms': round(min(durations), 2),
            'max_ms': round(max(durations), 2),
            'avg_ms': round(statistics.mean(durations), 2),
            'median_ms': round(statistics.median(durations), 2),
            'p95_ms': round(self._percentile(durations, 95), 2),
            'p99_ms': round(self._percentile(durations, 99), 2),
            'slow_count': sum(1 for d in durations if d > self.slow_threshold_ms)
        }

    def _percentile(self, data: List[float], percentile: float) -> float:
        """计算百分位数"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = (len(sorted_data) - 1) * percentile / 100
        lower = int(index)
        upper = lower + 1
        if upper >= len(sorted_data):
            return sorted_data[-1]
        return sorted_data[lower] + (sorted_data[upper] - sorted_data[lower]) * (index - lower)

    def _calculate_cache_hit_rate(self) -> float:
        """计算缓存命中率"""
        total = self._counters['cache_hits'] + self._counters['cache_misses']
        if total == 0:
            return 0.0
        return round(self._counters['cache_hits'] / total, 4)

    def reset(self):
        """重置所有统计"""
        with self._lock:
            self._history.clear()
            for key in self._counters:
                self._counters[key] = 0
        logger.info("PerformanceMonitor reset")

    def get_slow_operations(self, limit: int = 10) -> List[PerformanceMetrics]:
        """获取最近的慢操作"""
        with self._lock:
            slow_ops = []
            for op_history in self._history.values():
                for metric in op_history:
                    if metric.duration_ms > self.slow_threshold_ms:
                        slow_ops.append(metric)

            # 按时间倒序排列
            slow_ops.sort(key=lambda x: x.timestamp, reverse=True)
            return slow_ops[:limit]


def timed(operation: str, monitor: Optional[PerformanceMonitor] = None):
    """
    装饰器，用于测量函数执行时间

    Usage:
        @timed("search_skills", monitor)
        def search_skills(self, query: str):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if monitor is None:
                return func(*args, **kwargs)

            with monitor.measure(operation):
                return func(*args, **kwargs)
        return wrapper
    return decorator


# 全局监控器实例
_global_monitor: Optional[PerformanceMonitor] = None


def get_global_monitor() -> PerformanceMonitor:
    """获取全局性能监控器"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor


def set_global_monitor(monitor: PerformanceMonitor):
    """设置全局性能监控器"""
    global _global_monitor
    _global_monitor = monitor


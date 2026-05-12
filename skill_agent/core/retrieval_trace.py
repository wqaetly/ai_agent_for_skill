"""
检索轨迹可视化模块 (借鉴 OpenViking)
记录和可视化完整的检索过程，便于调试和优化

特性:
- 记录查询扩展过程
- 记录混合检索各阶段分数
- 记录重排序前后变化
- 支持轨迹序列化和可视化
"""

import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class RetrievalStage(Enum):
    """检索阶段"""
    QUERY_UNDERSTANDING = "query_understanding"
    QUERY_EXPANSION = "query_expansion"
    VECTOR_SEARCH = "vector_search"
    BM25_SEARCH = "bm25_search"
    HYBRID_FUSION = "hybrid_fusion"
    RERANK = "rerank"
    FILTER = "filter"
    FINAL = "final"


@dataclass
class StageRecord:
    """单阶段记录"""
    stage: str
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass 
class RetrievalTrace:
    """完整检索轨迹"""
    trace_id: str
    original_query: str
    stages: List[StageRecord] = field(default_factory=list)
    total_duration_ms: float = 0.0
    final_results_count: int = 0
    created_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_stage(self, record: StageRecord):
        """添加阶段记录"""
        self.stages.append(record)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'trace_id': self.trace_id,
            'original_query': self.original_query,
            'stages': [s.to_dict() for s in self.stages],
            'total_duration_ms': self.total_duration_ms,
            'final_results_count': self.final_results_count,
            'created_at': self.created_at,
            'metadata': self.metadata
        }
    
    def get_stage_summary(self) -> List[Dict[str, Any]]:
        """获取阶段摘要（用于快速查看）"""
        return [
            {
                'stage': s.stage,
                'duration_ms': round(s.duration_ms, 2),
                'output_count': len(s.output_data.get('results', [])) 
                    if isinstance(s.output_data.get('results'), list) else 0
            }
            for s in self.stages
        ]
    
    def to_mermaid(self) -> str:
        """生成 Mermaid 流程图"""
        lines = ["flowchart TD"]
        
        for i, stage in enumerate(self.stages):
            node_id = f"S{i}"
            output_count = len(stage.output_data.get('results', []))
            label = f"{stage.stage}\\n{stage.duration_ms:.1f}ms"
            if output_count > 0:
                label += f"\\n→{output_count}条"
            
            lines.append(f'    {node_id}["{label}"]')
            
            if i > 0:
                lines.append(f"    S{i-1} --> {node_id}")
        
        return '\n'.join(lines)


class RetrievalTracer:
    """检索轨迹记录器"""
    
    def __init__(self, trace_id: Optional[str] = None, query: str = ""):
        self.trace_id = trace_id or self._generate_id()
        self.query = query
        self._trace = RetrievalTrace(
            trace_id=self.trace_id,
            original_query=query,
            created_at=datetime.now().isoformat()
        )
        self._start_time = time.perf_counter()
        self._stage_start: Optional[float] = None
        self._current_stage: Optional[str] = None
    
    def _generate_id(self) -> str:
        """生成轨迹 ID"""
        import hashlib
        ts = datetime.now().isoformat()
        return hashlib.md5(ts.encode()).hexdigest()[:12]
    
    def start_stage(self, stage: RetrievalStage, input_data: Dict[str, Any] = None):
        """开始记录新阶段"""
        self._stage_start = time.perf_counter()
        self._current_stage = stage.value
        self._current_input = input_data or {}
    
    def end_stage(
        self, 
        output_data: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ):
        """结束当前阶段"""
        if self._stage_start is None or self._current_stage is None:
            return
        
        duration = (time.perf_counter() - self._stage_start) * 1000
        
        record = StageRecord(
            stage=self._current_stage,
            input_data=self._current_input,
            output_data=output_data or {},
            duration_ms=duration,
            metadata=metadata or {},
            timestamp=datetime.now().isoformat()
        )
        
        self._trace.add_stage(record)
        self._stage_start = None
        self._current_stage = None
    
    def record_stage(
        self,
        stage: RetrievalStage,
        input_data: Dict[str, Any] = None,
        output_data: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None,
        duration_ms: float = 0.0
    ):
        """直接记录完整阶段（不计时）"""
        record = StageRecord(
            stage=stage.value,
            input_data=input_data or {},
            output_data=output_data or {},
            duration_ms=duration_ms,
            metadata=metadata or {},
            timestamp=datetime.now().isoformat()
        )
        self._trace.add_stage(record)

    def finalize(self, results_count: int = 0) -> RetrievalTrace:
        """完成轨迹记录并返回"""
        self._trace.total_duration_ms = (time.perf_counter() - self._start_time) * 1000
        self._trace.final_results_count = results_count
        return self._trace

    def get_trace(self) -> RetrievalTrace:
        """获取当前轨迹"""
        return self._trace


class TraceStorage:
    """轨迹存储（用于历史分析）"""

    def __init__(self, storage_path: str = "Data/traces", max_traces: int = 1000):
        from pathlib import Path
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.max_traces = max_traces

        # 内存中保留最近的轨迹
        self._recent_traces: List[RetrievalTrace] = []

    def save(self, trace: RetrievalTrace):
        """保存轨迹"""
        self._recent_traces.append(trace)

        # 限制内存中的轨迹数量
        if len(self._recent_traces) > self.max_traces:
            self._recent_traces = self._recent_traces[-self.max_traces:]

    def get_recent(self, count: int = 10) -> List[Dict[str, Any]]:
        """获取最近的轨迹"""
        return [t.to_dict() for t in self._recent_traces[-count:]]

    def get_slow_queries(self, threshold_ms: float = 500) -> List[Dict[str, Any]]:
        """获取慢查询"""
        return [
            t.to_dict() for t in self._recent_traces
            if t.total_duration_ms > threshold_ms
        ]

    def get_statistics(self) -> Dict[str, Any]:
        """获取轨迹统计"""
        if not self._recent_traces:
            return {'count': 0}

        durations = [t.total_duration_ms for t in self._recent_traces]
        return {
            'count': len(self._recent_traces),
            'avg_duration_ms': sum(durations) / len(durations),
            'max_duration_ms': max(durations),
            'min_duration_ms': min(durations),
            'total_queries': len(self._recent_traces)
        }


def format_trace_for_display(trace: RetrievalTrace) -> str:
    """格式化轨迹用于显示"""
    lines = [
        f"=== 检索轨迹 [{trace.trace_id}] ===",
        f"查询: {trace.original_query}",
        f"总耗时: {trace.total_duration_ms:.2f}ms",
        f"结果数: {trace.final_results_count}",
        "",
        "阶段详情:",
    ]

    for i, stage in enumerate(trace.stages, 1):
        output_count = len(stage.output_data.get('results', []))
        lines.append(f"  {i}. {stage.stage}")
        lines.append(f"     耗时: {stage.duration_ms:.2f}ms")
        if output_count > 0:
            lines.append(f"     输出: {output_count} 条")
        if stage.metadata:
            for k, v in stage.metadata.items():
                lines.append(f"     {k}: {v}")

    return '\n'.join(lines)


def create_trace_context_manager(query: str):
    """创建轨迹上下文管理器"""
    class TraceContext:
        def __init__(self, query: str):
            self.tracer = RetrievalTracer(query=query)

        def __enter__(self):
            return self.tracer

        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is None:
                self.tracer.finalize()
            return False

    return TraceContext(query)


"""
流式输出核心模块
提供技能生成过程中的实时进度反馈

主要功能：
1. 定义标准化的进度事件类型
2. 提供流式输出工具函数
3. 支持多种消费方式（回调、异步迭代器等）
"""

import logging
from enum import Enum
from typing import Any, Dict, Optional, Callable, AsyncIterator, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


# ==================== 进度事件类型 ====================

class ProgressEventType(str, Enum):
    """进度事件类型枚举"""
    # 阶段性事件
    GENERATION_STARTED = "generation_started"      # 生成开始
    GENERATION_COMPLETED = "generation_completed"  # 生成完成
    GENERATION_FAILED = "generation_failed"        # 生成失败

    # 骨架阶段
    SKELETON_STARTED = "skeleton_started"          # 骨架生成开始
    SKELETON_COMPLETED = "skeleton_completed"      # 骨架生成完成
    SKELETON_FAILED = "skeleton_failed"            # 骨架生成失败

    # Track阶段
    TRACK_STARTED = "track_started"                # Track生成开始
    TRACK_COMPLETED = "track_completed"            # Track生成完成
    TRACK_FAILED = "track_failed"                  # Track生成失败

    # 批次阶段
    BATCH_PLANNING = "batch_planning"              # 批次规划中
    BATCH_STARTED = "batch_started"                # 批次生成开始
    BATCH_COMPLETED = "batch_completed"            # 批次生成完成
    BATCH_VALIDATING = "batch_validating"          # 批次验证中
    BATCH_FIXING = "batch_fixing"                  # 批次修复中
    BATCH_FAILED = "batch_failed"                  # 批次生成失败

    # 组装阶段
    ASSEMBLING_TRACK = "assembling_track"          # 组装Track中
    ASSEMBLING_SKILL = "assembling_skill"          # 组装技能中

    # 验证阶段
    VALIDATING = "validating"                      # 验证中
    VALIDATION_PASSED = "validation_passed"        # 验证通过
    VALIDATION_FAILED = "validation_failed"        # 验证失败

    # LLM调用
    LLM_CALLING = "llm_calling"                    # LLM调用中
    LLM_COMPLETED = "llm_completed"                # LLM调用完成

    # RAG检索
    RAG_SEARCHING = "rag_searching"                # RAG检索中
    RAG_COMPLETED = "rag_completed"                # RAG检索完成
    
    # Action匹配问题（需要用户介入）
    ACTION_MISMATCH = "action_mismatch"            # Action不匹配，需要用户补全

    # 通用
    INFO = "info"                                  # 普通信息
    WARNING = "warning"                            # 警告
    ERROR = "error"                                # 错误


@dataclass
class ProgressEvent:
    """
    进度事件数据类

    用于标准化流式输出的事件格式
    """
    event_type: ProgressEventType           # 事件类型
    message: str                            # 人类可读的消息

    # 进度信息
    progress: Optional[float] = None        # 总体进度 (0.0 - 1.0)
    current_step: Optional[int] = None      # 当前步骤
    total_steps: Optional[int] = None       # 总步骤数

    # 上下文信息
    phase: Optional[str] = None             # 当前阶段 (skeleton/track/batch/assemble)
    track_index: Optional[int] = None       # 当前Track索引
    track_name: Optional[str] = None        # 当前Track名称
    total_tracks: Optional[int] = None      # Track总数
    batch_index: Optional[int] = None       # 当前批次索引
    total_batches: Optional[int] = None     # 批次总数

    # 详细数据
    data: Dict[str, Any] = field(default_factory=dict)  # 附加数据

    # 时间戳
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = asdict(self)
        result["event_type"] = self.event_type.value
        # 移除None值
        return {k: v for k, v in result.items() if v is not None}

    def __str__(self) -> str:
        """格式化为可读字符串"""
        parts = [f"[{self.event_type.value}]"]

        if self.progress is not None:
            parts.append(f"{self.progress*100:.1f}%")
        elif self.current_step is not None and self.total_steps is not None:
            parts.append(f"[{self.current_step}/{self.total_steps}]")

        if self.track_name:
            parts.append(f"Track: {self.track_name}")

        if self.batch_index is not None and self.total_batches is not None:
            parts.append(f"Batch: {self.batch_index + 1}/{self.total_batches}")

        parts.append(self.message)

        return " ".join(parts)


# ==================== 进度计算器 ====================

class ProgressCalculator:
    """
    进度计算器

    根据当前状态计算总体进度百分比
    """

    # 各阶段权重
    PHASE_WEIGHTS = {
        "skeleton": 0.1,      # 骨架生成占 10%
        "tracks": 0.8,        # Track生成占 80%
        "assemble": 0.1,      # 组装占 10%
    }

    def __init__(self, total_tracks: int = 1, batches_per_track: int = 1):
        """
        初始化进度计算器

        Args:
            total_tracks: Track总数
            batches_per_track: 每个Track的平均批次数
        """
        self.total_tracks = max(1, total_tracks)
        self.batches_per_track = max(1, batches_per_track)

        # 当前状态
        self.skeleton_done = False
        self.current_track = 0
        self.current_batch = 0
        self.current_track_batches = batches_per_track
        self.assemble_done = False

    def update_track_info(self, total_tracks: int, current_track: int,
                          total_batches: int, current_batch: int):
        """更新Track和批次信息"""
        self.total_tracks = max(1, total_tracks)
        self.current_track = current_track
        self.current_track_batches = max(1, total_batches)
        self.current_batch = current_batch

    def set_skeleton_done(self):
        """标记骨架生成完成"""
        self.skeleton_done = True

    def set_assemble_done(self):
        """标记组装完成"""
        self.assemble_done = True

    def calculate(self) -> float:
        """
        计算当前总体进度

        Returns:
            进度值 (0.0 - 1.0)
        """
        progress = 0.0

        # 骨架阶段
        if self.skeleton_done:
            progress += self.PHASE_WEIGHTS["skeleton"]

        # Track阶段
        if self.total_tracks > 0:
            # 已完成的Track贡献
            completed_tracks_progress = (self.current_track / self.total_tracks)

            # 当前Track内的批次进度
            if self.current_track < self.total_tracks and self.current_track_batches > 0:
                current_track_progress = (self.current_batch / self.current_track_batches)
                current_track_contribution = current_track_progress / self.total_tracks
            else:
                current_track_contribution = 0

            track_progress = completed_tracks_progress + current_track_contribution
            progress += self.PHASE_WEIGHTS["tracks"] * track_progress

        # 组装阶段
        if self.assemble_done:
            progress += self.PHASE_WEIGHTS["assemble"]

        return min(1.0, progress)


# ==================== 流式输出工具函数 ====================

def create_progress_event(
    event_type: ProgressEventType,
    message: str,
    calculator: Optional[ProgressCalculator] = None,
    **kwargs
) -> ProgressEvent:
    """
    创建进度事件的便捷函数

    Args:
        event_type: 事件类型
        message: 消息内容
        calculator: 进度计算器（可选，用于自动计算进度）
        **kwargs: 其他ProgressEvent字段

    Returns:
        ProgressEvent实例
    """
    # 优先使用 kwargs 中显式传入的 progress，否则使用 calculator 计算
    progress = kwargs.pop("progress", None)
    if progress is None and calculator:
        progress = calculator.calculate()

    return ProgressEvent(
        event_type=event_type,
        message=message,
        progress=progress,
        **kwargs
    )


def emit_progress(
    writer: Optional[Callable],
    event_type: ProgressEventType,
    message: str,
    calculator: Optional[ProgressCalculator] = None,
    **kwargs
):
    """
    发送进度事件

    Args:
        writer: StreamWriter实例（从LangGraph获取）
        event_type: 事件类型
        message: 消息内容
        calculator: 进度计算器
        **kwargs: 其他字段
    """
    if writer is None:
        # 没有writer时只记录日志
        logger.debug(f"[{event_type.value}] {message}")
        return

    event = create_progress_event(
        event_type=event_type,
        message=message,
        calculator=calculator,
        **kwargs
    )

    try:
        writer(event.to_dict())
    except Exception as e:
        logger.warning(f"发送进度事件失败: {e}")


# ==================== 流式输出消费者 ====================

class StreamConsumer:
    """
    流式输出消费者基类

    用于处理从图执行中接收的流式事件
    """

    def on_event(self, event: Dict[str, Any]):
        """
        处理单个事件

        Args:
            event: 事件数据字典
        """
        raise NotImplementedError

    def on_complete(self, final_result: Dict[str, Any]):
        """
        处理完成事件

        Args:
            final_result: 最终结果
        """
        pass

    def on_error(self, error: Exception):
        """
        处理错误事件

        Args:
            error: 异常对象
        """
        pass


class PrintStreamConsumer(StreamConsumer):
    """打印输出的消费者（用于调试）"""

    def __init__(self, show_progress_bar: bool = True):
        self.show_progress_bar = show_progress_bar
        self.last_progress = 0.0

    def on_event(self, event: Dict[str, Any]):
        event_type = event.get("event_type", "unknown")
        message = event.get("message", "")
        progress = event.get("progress")

        # 构建输出
        prefix = self._get_event_icon(event_type)

        if progress is not None and self.show_progress_bar:
            bar = self._make_progress_bar(progress)
            print(f"{prefix} {bar} {message}")
            self.last_progress = progress
        else:
            print(f"{prefix} {message}")

    def on_complete(self, final_result: Dict[str, Any]):
        skill_name = final_result.get("assembled_skill", {}).get("skillName", "Unknown")
        is_valid = final_result.get("is_valid", False)
        status = "✅ 成功" if is_valid else "⚠️ 有警告"
        print(f"\n{'='*50}")
        print(f"🎉 技能生成完成: {skill_name} ({status})")
        print(f"{'='*50}")

    def on_error(self, error: Exception):
        print(f"\n❌ 生成失败: {error}")

    def _get_event_icon(self, event_type: str) -> str:
        """获取事件图标"""
        icons = {
            "generation_started": "🚀",
            "generation_completed": "🎉",
            "generation_failed": "❌",
            "skeleton_started": "🦴",
            "skeleton_completed": "✅",
            "track_started": "🎯",
            "track_completed": "✅",
            "batch_started": "📦",
            "batch_completed": "✅",
            "batch_validating": "🔍",
            "batch_fixing": "🔧",
            "assembling_track": "🔧",
            "assembling_skill": "🔧",
            "validating": "🔍",
            "validation_passed": "✅",
            "validation_failed": "⚠️",
            "llm_calling": "🤖",
            "rag_searching": "🔎",
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
        }
        return icons.get(event_type, "•")

    def _make_progress_bar(self, progress: float, width: int = 20) -> str:
        """生成进度条"""
        filled = int(width * progress)
        empty = width - filled
        bar = "█" * filled + "░" * empty
        return f"[{bar}] {progress*100:5.1f}%"


class CallbackStreamConsumer(StreamConsumer):
    """基于回调的消费者"""

    def __init__(
        self,
        on_progress: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_complete_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_error_callback: Optional[Callable[[Exception], None]] = None,
    ):
        self._on_progress = on_progress
        self._on_complete = on_complete_callback
        self._on_error = on_error_callback

    def on_event(self, event: Dict[str, Any]):
        if self._on_progress:
            self._on_progress(event)

    def on_complete(self, final_result: Dict[str, Any]):
        if self._on_complete:
            self._on_complete(final_result)

    def on_error(self, error: Exception):
        if self._on_error:
            self._on_error(error)


# ==================== 流式执行包装器 ====================

async def stream_graph_execution(
    graph,
    initial_state: Dict[str, Any],
    config: Dict[str, Any],
    consumer: Optional[StreamConsumer] = None,
) -> Dict[str, Any]:
    """
    流式执行图并处理事件

    Args:
        graph: 编译后的LangGraph
        initial_state: 初始状态
        config: 执行配置
        consumer: 事件消费者（可选）

    Returns:
        最终执行结果
    """
    if consumer is None:
        consumer = PrintStreamConsumer()

    final_result = None

    try:
        # 使用多种流模式
        async for stream_mode, chunk in graph.astream(
            initial_state,
            config,
            stream_mode=["updates", "custom"]
        ):
            if stream_mode == "custom":
                # 自定义进度事件
                consumer.on_event(chunk)
            elif stream_mode == "updates":
                # 节点更新事件
                # 从updates中提取最新状态
                if isinstance(chunk, dict):
                    for node_name, node_output in chunk.items():
                        if isinstance(node_output, dict):
                            # 保存最新结果
                            if "final_result" in node_output or "assembled_skill" in node_output:
                                final_result = node_output

        # 如果没有从updates获取到结果，尝试获取最终状态
        if final_result is None:
            state = await graph.aget_state(config)
            if state and state.values:
                final_result = state.values

        if final_result:
            consumer.on_complete(final_result)

        return final_result or {}

    except Exception as e:
        consumer.on_error(e)
        raise


def stream_graph_execution_sync(
    graph,
    initial_state: Dict[str, Any],
    config: Dict[str, Any],
    consumer: Optional[StreamConsumer] = None,
) -> Dict[str, Any]:
    """
    同步版本的流式执行

    Args:
        graph: 编译后的LangGraph
        initial_state: 初始状态
        config: 执行配置
        consumer: 事件消费者（可选）

    Returns:
        最终执行结果
    """
    if consumer is None:
        consumer = PrintStreamConsumer()

    final_result = None

    try:
        # 使用多种流模式
        for stream_mode, chunk in graph.stream(
            initial_state,
            config,
            stream_mode=["updates", "custom"]
        ):
            if stream_mode == "custom":
                # 自定义进度事件
                consumer.on_event(chunk)
            elif stream_mode == "updates":
                # 节点更新事件
                if isinstance(chunk, dict):
                    for node_name, node_output in chunk.items():
                        if isinstance(node_output, dict):
                            if "final_result" in node_output or "assembled_skill" in node_output:
                                final_result = node_output

        # 获取最终状态
        if final_result is None:
            state = graph.get_state(config)
            if state and state.values:
                final_result = state.values

        if final_result:
            consumer.on_complete(final_result)

        return final_result or {}

    except Exception as e:
        consumer.on_error(e)
        raise


# ==================== 导出 ====================

__all__ = [
    # 类型
    "ProgressEventType",
    "ProgressEvent",
    "ProgressCalculator",
    # 工具函数
    "create_progress_event",
    "emit_progress",
    # 消费者
    "StreamConsumer",
    "PrintStreamConsumer",
    "CallbackStreamConsumer",
    # 执行器
    "stream_graph_execution",
    "stream_graph_execution_sync",
]

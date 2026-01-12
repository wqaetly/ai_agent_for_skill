"""
流式输出辅助模块
提供 StreamWriter 获取和进度事件发送功能
"""

import logging
from typing import Any, Dict, Optional

from langgraph.config import get_stream_writer

from ...streaming import ProgressEventType, emit_progress

logger = logging.getLogger(__name__)


def get_writer_safe() -> Optional[Any]:
    """
    安全获取 StreamWriter
    
    在非流式执行环境中不会报错
    """
    try:
        writer = get_stream_writer()
        logger.debug(f"Got StreamWriter: {type(writer)}")
        return writer
    except Exception as e:
        logger.debug(f"Cannot get StreamWriter: {e}")
        return None


def emit_node_progress(
    event_type: ProgressEventType,
    message: str,
    phase: str = "unknown",
    progress: float = 0.0,
    writer: Optional[Any] = None,
    **kwargs
):
    """
    发送节点进度事件的通用函数

    Args:
        event_type: 事件类型
        message: 消息内容
        phase: 阶段名称 (skeleton/track/batch/finalize)
        progress: 进度值 (0.0-1.0)
        writer: StreamWriter 实例，如果为 None 则尝试自动获取
        **kwargs: 其他参数
    """
    if writer is None:
        writer = get_writer_safe()
    
    if writer is None:
        logger.debug(f"[{event_type.value}] {message}")
        return

    emit_progress(
        writer,
        event_type,
        message,
        progress=progress,
        phase=phase,
        **kwargs
    )


def emit_skeleton_progress(
    event_type: ProgressEventType,
    message: str,
    progress: float = 0.05,
    **kwargs
):
    """发送骨架生成进度事件"""
    emit_node_progress(event_type, message, phase="skeleton", progress=progress, **kwargs)


def emit_track_progress(
    event_type: ProgressEventType,
    message: str,
    track_index: int,
    total_tracks: int,
    track_name: str = "",
    **kwargs
):
    """
    发送 Track 生成进度事件
    
    进度计算：骨架 10% + tracks 80%（按比例分配）
    """
    base_progress = 0.1
    track_weight = 0.8 / max(1, total_tracks)

    if event_type == ProgressEventType.TRACK_STARTED:
        progress = base_progress + track_index * track_weight
    elif event_type == ProgressEventType.TRACK_COMPLETED:
        progress = base_progress + (track_index + 1) * track_weight
    else:
        progress = base_progress + (track_index + 0.5) * track_weight

    emit_node_progress(
        event_type,
        message,
        phase="track",
        progress=progress,
        track_index=track_index,
        track_name=track_name,
        total_tracks=total_tracks,
        **kwargs
    )


def emit_batch_progress(
    event_type: ProgressEventType,
    message: str,
    state: Optional[Dict[str, Any]] = None,
    **kwargs
):
    """
    发送批次生成进度事件
    
    自动从 state 中提取上下文信息
    """
    extra_data = {}
    if state:
        track_plan = state.get("track_plan", [])
        current_track_idx = state.get("current_track_index", 0)
        batch_plan = state.get("current_track_batch_plan", [])
        current_batch_idx = state.get("current_batch_index", 0)

        extra_data["track_index"] = current_track_idx
        extra_data["total_tracks"] = len(track_plan)
        extra_data["batch_index"] = current_batch_idx
        extra_data["total_batches"] = len(batch_plan)

        if track_plan:
            skeleton_progress = 0.1
            track_progress = 0.0
            total_tracks = len(track_plan)
            
            if total_tracks > 0:
                completed_tracks = current_track_idx
                current_track_batch_progress = (
                    current_batch_idx / len(batch_plan) if batch_plan else 0
                )
                track_progress = (completed_tracks + current_track_batch_progress) / total_tracks
                track_progress *= 0.8

            extra_data["progress"] = skeleton_progress + track_progress

        if current_track_idx < len(track_plan):
            extra_data["track_name"] = track_plan[current_track_idx].get("trackName", "")

    extra_data.update(kwargs)
    
    writer = get_writer_safe()
    if writer is None:
        logger.debug(f"[{event_type.value}] {message}")
        return

    emit_progress(writer, event_type, message, **extra_data)


def emit_finalize_progress(
    event_type: ProgressEventType,
    message: str,
    is_valid: bool = True,
    **kwargs
):
    """发送最终化进度事件"""
    progress = 1.0 if is_valid else 0.95
    emit_node_progress(event_type, message, phase="finalize", progress=progress, **kwargs)

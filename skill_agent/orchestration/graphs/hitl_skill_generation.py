"""
Human-in-the-loop 技能生成图

在关键节点添加中断点，支持人工审核：
1. 骨架生成后 - 审核技能结构
2. 技能组装后 - 审核最终配置

使用方式：
1. 调用 invoke/stream 后，图会在中断点暂停
2. 用户审核后，调用 update_state 修改状态
3. 再次调用 invoke 继续执行
"""

from langgraph.graph import StateGraph, END
import os
import logging
from typing import Dict, Any, List, Optional, Literal

from langchain_core.messages import AIMessage
from .utils import get_checkpointer
from ..nodes.progressive_skill_nodes import (
    ProgressiveSkillGenerationState,
    skeleton_generator_node,
    skeleton_fixer_node,
    should_continue_to_track_generation,
    track_generator_node,
    track_validator_node,
    track_accumulator_node,
    should_continue_track_loop,
    skill_assembler_node,
    finalize_progressive_node,
    should_finalize_or_fail,
)

logger = logging.getLogger(__name__)


def build_hitl_skill_generation_graph(
    interrupt_after_skeleton: bool = True,
    interrupt_after_assembly: bool = True,
    interrupt_on_action_mismatch: bool = True,
):
    """
    构建支持 Human-in-the-loop 的技能生成图
    
    Args:
        interrupt_after_skeleton: 骨架生成后是否中断
        interrupt_after_assembly: 技能组装后是否中断
        interrupt_on_action_mismatch: 检测到无效 Action 类型时是否中断
    
    Returns:
        编译后的 LangGraph
    """
    workflow = StateGraph(ProgressiveSkillGenerationState)
    
    # 添加节点
    workflow.add_node("skeleton_generator", skeleton_generator_node)
    workflow.add_node("skeleton_fixer", skeleton_fixer_node)
    workflow.add_node("track_generator", track_generator_node)
    workflow.add_node("track_validator", track_validator_node)
    workflow.add_node("track_accumulator", track_accumulator_node)
    workflow.add_node("skill_assembler", skill_assembler_node)
    workflow.add_node("finalize", finalize_progressive_node)
    
    # Action 类型不匹配时的中断节点（空节点，仅用于中断）
    def action_mismatch_interrupt_node(state):
        """当检测到无效 Action 类型时，此节点会被中断，等待用户决定"""
        missing_types = state.get("missing_action_types", [])
        details = state.get("action_mismatch_details", "")
        logger.info(f"Action mismatch interrupt: {missing_types}")
        return {
            "messages": [AIMessage(content=f"[等待用户确认] 检测到无效的 Action 类型:\n{details}\n\n请选择:\n1. 继续生成（忽略此问题）\n2. 终止生成")]
        }
    
    workflow.add_node("action_mismatch_interrupt", action_mismatch_interrupt_node)
    
    # 用户确认后继续或终止的条件函数
    def should_continue_after_mismatch(state) -> Literal["continue_generation", "abort_generation"]:
        """用户确认后决定是否继续"""
        # 检查用户是否选择继续（通过 update_state 设置）
        user_choice = state.get("user_action_mismatch_choice", "continue")
        if user_choice == "abort":
            return "abort_generation"
        return "continue_generation"
    
    # 入口点
    workflow.set_entry_point("skeleton_generator")
    
    # 边定义
    workflow.add_conditional_edges(
        "skeleton_generator",
        should_continue_to_track_generation,
        {
            "generate_tracks": "track_generator",
            "fix_skeleton": "skeleton_fixer",
            "skeleton_failed": "finalize"
        }
    )
    
    workflow.add_conditional_edges(
        "skeleton_fixer",
        should_continue_to_track_generation,
        {
            "generate_tracks": "track_generator",
            "fix_skeleton": "skeleton_fixer",
            "skeleton_failed": "finalize"
        }
    )
    
    workflow.add_edge("track_generator", "track_validator")
    workflow.add_edge("track_validator", "track_accumulator")
    
    workflow.add_conditional_edges(
        "track_accumulator",
        should_continue_track_loop,
        {
            "next_track": "track_generator",
            "assemble": "skill_assembler",
            "fix_track": "track_generator",
            "action_mismatch_interrupt": "action_mismatch_interrupt"
        }
    )
    
    # Action mismatch 中断后的条件边
    workflow.add_conditional_edges(
        "action_mismatch_interrupt",
        should_continue_after_mismatch,
        {
            "continue_generation": "track_accumulator",
            "abort_generation": "finalize"
        }
    )
    
    workflow.add_conditional_edges(
        "skill_assembler",
        should_finalize_or_fail,
        {"finalize": "finalize", "failed": "finalize"}
    )
    
    workflow.add_edge("finalize", END)
    
    # 配置中断点
    interrupt_before = []
    interrupt_after = []
    
    if interrupt_after_skeleton:
        # 骨架生成后中断，让用户审核
        interrupt_after.append("skeleton_generator")
    
    if interrupt_after_assembly:
        # 技能组装后中断，让用户审核最终配置
        interrupt_after.append("skill_assembler")
    
    if interrupt_on_action_mismatch:
        # 检测到无效 Action 类型时中断，让用户决定是否继续
        interrupt_before.append("action_mismatch_interrupt")
    
    # 持久化配置
    checkpoint_dir = os.path.join(
        os.path.dirname(__file__), "..", "..", "Data", "checkpoints"
    )
    checkpoint_db = os.path.join(checkpoint_dir, "hitl_skill_generation.db")
    checkpointer = get_checkpointer(checkpoint_db)
    
    logger.info(f"HITL graph: interrupt_before={interrupt_before}, interrupt_after={interrupt_after}")
    
    return workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=interrupt_before,
        interrupt_after=interrupt_after,
        debug=False
    )


# 全局实例
_hitl_graph = None


def get_hitl_skill_generation_graph():
    """获取 HITL 技能生成图单例"""
    global _hitl_graph
    if _hitl_graph is None:
        _hitl_graph = build_hitl_skill_generation_graph()
        logger.info("HITL skill generation graph initialized")
    return _hitl_graph


# ==================== HITL 辅助函数 ====================

def create_hitl_config(thread_id: str) -> Dict[str, Any]:
    """创建 HITL 配置"""
    return {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 100
    }


async def start_skill_generation_hitl(
    requirement: str,
    thread_id: str,
    similar_skills: list = None,
) -> Dict[str, Any]:
    """
    启动 HITL 技能生成（会在骨架生成后暂停）
    
    Returns:
        当前状态（包含 skill_skeleton 供审核）
    """
    graph = get_hitl_skill_generation_graph()
    
    initial_state = {
        "requirement": requirement,
        "similar_skills": similar_skills or [],
        "skill_skeleton": {},
        "skeleton_validation_errors": [],
        "skeleton_retry_count": 0,
        "max_skeleton_retries": 2,
        "track_plan": [],
        "current_track_index": 0,
        "current_track_data": {},
        "generated_tracks": [],
        "current_track_errors": [],
        "track_retry_count": 0,
        "max_track_retries": 3,
        "used_action_types": [],
        # Action匹配中断状态
        "action_mismatch": False,
        "missing_action_types": [],
        "action_mismatch_details": "",
        "user_action_mismatch_choice": "continue",  # 默认继续
        "assembled_skill": {},
        "final_validation_errors": [],
        "final_result": {},
        "is_valid": False,
        "messages": [],
    }
    
    config = create_hitl_config(thread_id)
    result = await graph.ainvoke(initial_state, config)
    return result


async def approve_and_continue(
    thread_id: str,
    modifications: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    审核通过并继续执行
    
    Args:
        thread_id: 线程ID
        modifications: 可选的状态修改（如修改 skill_skeleton）
    
    Returns:
        继续执行后的状态
    """
    graph = get_hitl_skill_generation_graph()
    config = create_hitl_config(thread_id)
    
    # 如果有修改，先更新状态
    if modifications:
        graph.update_state(config, modifications)
        logger.info(f"State updated with modifications: {list(modifications.keys())}")
    
    # 继续执行
    result = await graph.ainvoke(None, config)
    return result


def get_current_state(thread_id: str) -> Optional[Dict[str, Any]]:
    """获取当前状态（用于审核）"""
    graph = get_hitl_skill_generation_graph()
    config = create_hitl_config(thread_id)
    
    try:
        state = graph.get_state(config)
        return state.values if state else None
    except Exception as e:
        logger.error(f"Failed to get state: {e}")
        return None


async def handle_action_mismatch_response(
    thread_id: str,
    user_choice: str = "continue"
) -> Dict[str, Any]:
    """
    处理用户对 Action 类型不匹配的响应
    
    Args:
        thread_id: 线程ID
        user_choice: 用户选择 - "continue" 继续生成, "abort" 终止生成
    
    Returns:
        继续执行后的状态
    """
    graph = get_hitl_skill_generation_graph()
    config = create_hitl_config(thread_id)
    
    # 更新用户选择并重置 action_mismatch 标记
    modifications = {
        "user_action_mismatch_choice": user_choice,
        "action_mismatch": False,  # 重置标记，允许继续
    }
    
    graph.update_state(config, modifications)
    logger.info(f"User chose to {user_choice} after action mismatch")
    
    # 继续执行
    result = await graph.ainvoke(None, config)
    return result


__all__ = [
    "build_hitl_skill_generation_graph",
    "get_hitl_skill_generation_graph",
    "start_skill_generation_hitl",
    "approve_and_continue",
    "get_current_state",
    "handle_action_mismatch_response",
]

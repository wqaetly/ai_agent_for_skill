"""
Action批次级渐进式技能生成图
实现最细粒度的渐进式生成，适用于超级复杂技能

流程：
1. 骨架生成（复用）
2. Track批次规划（新）→ 遍历每个Track
3. 批次Action生成循环（新）→ 遍历每个批次
   - 生成 → 验证 → 修复（可选）→ 保存
4. Track组装（新）→ 将批次actions合并为完整Track
5. 技能组装（复用）

优势：
- Token消耗降低50%
- 错误隔离性优秀（单批次失败不影响其他批次）
- 生成质量提升（避免长输出导致的质量下降）
- 支持流式输出（实时进度反馈）
"""

from langgraph.graph import StateGraph, END
from langgraph.errors import GraphRecursionError
import os
import logging
from typing import Optional, Callable, Dict, Any
from .utils import get_checkpointer
from ..nodes.action_batch_skill_nodes import (
    ActionBatchProgressiveState,
    # 阶段1: 骨架生成（复用）
    skeleton_generator_node,
    should_continue_to_track_generation,
    # 阶段2: Track批次规划
    plan_track_batches_node,
    # 阶段3: 批次Action生成
    batch_action_generator_node,
    batch_action_validator_node,
    batch_action_fixer_node,
    batch_action_saver_node,
    should_fix_batch,
    should_continue_batches,
    # 阶段4: Track组装
    track_assembler_node_batch,
    should_continue_tracks_batch,
    # 阶段5: 技能组装（复用）
    skill_assembler_node,
    finalize_progressive_node,
    should_finalize_or_fail,
)
from ..streaming import (
    StreamConsumer,
    PrintStreamConsumer,
    CallbackStreamConsumer,
    stream_graph_execution,
    stream_graph_execution_sync,
)

logger = logging.getLogger(__name__)


def build_action_batch_skill_generation_graph():
    """
    构建Action批次级渐进式技能生成 LangGraph

    流程:
    1. skeleton_generator: 生成技能骨架
    2. 判断骨架是否有效
    3. plan_track_batches: 为当前Track规划批次
    4. batch_action_generator: 生成当前批次的actions
    5. batch_action_validator: 验证批次
    6. 判断验证结果:
       - 通过 → batch_action_saver
       - 失败且未达重试上限 → batch_action_fixer → 重新验证
       - 失败且达重试上限 → batch_action_saver（跳过）
    7. 判断是否继续批次:
       - 还有批次 → 回到 batch_action_generator
       - 批次全部完成 → track_assembler_batch（组装Track）
    8. 判断是否继续Track:
       - 还有Track → 回到 plan_track_batches
       - Track全部完成 → skill_assembler
    9. skill_assembler: 组装完整技能
    10. finalize: 输出最终结果

    Returns:
        编译后的 LangGraph
    """
    workflow = StateGraph(ActionBatchProgressiveState)

    # ==================== 添加节点 ====================

    # 阶段1: 骨架生成
    workflow.add_node("skeleton_generator", skeleton_generator_node)

    # 阶段2: Track批次规划
    workflow.add_node("plan_track_batches", plan_track_batches_node)

    # 阶段3: 批次Action生成循环
    workflow.add_node("batch_action_generator", batch_action_generator_node)
    workflow.add_node("batch_action_validator", batch_action_validator_node)
    workflow.add_node("batch_action_fixer", batch_action_fixer_node)
    workflow.add_node("batch_action_saver", batch_action_saver_node)

    # 阶段4: Track组装
    workflow.add_node("track_assembler", track_assembler_node_batch)

    # 阶段5: 技能组装
    workflow.add_node("skill_assembler", skill_assembler_node)
    workflow.add_node("finalize", finalize_progressive_node)

    # ==================== 设置入口点 ====================
    workflow.set_entry_point("skeleton_generator")

    # ==================== 定义边 ====================

    # 骨架生成后的条件分支
    workflow.add_conditional_edges(
        "skeleton_generator",
        should_continue_to_track_generation,
        {
            "generate_tracks": "plan_track_batches",  # 骨架有效 → 规划Track批次
            "skeleton_failed": "finalize"              # 骨架无效 → 直接结束
        }
    )

    # Track批次规划 → 开始生成第一个批次
    workflow.add_edge("plan_track_batches", "batch_action_generator")

    # 批次生成 → 验证
    workflow.add_edge("batch_action_generator", "batch_action_validator")

    # 批次验证后的条件分支
    workflow.add_conditional_edges(
        "batch_action_validator",
        should_fix_batch,
        {
            "save": "batch_action_saver",   # 验证通过 → 保存
            "fix": "batch_action_fixer",    # 需要修复 → 进入fixer
            "skip": "batch_action_saver"    # 达到上限 → 跳过（保存空或部分结果）
        }
    )

    # 批次修复 → 重新验证
    workflow.add_edge("batch_action_fixer", "batch_action_validator")

    # 批次保存后的条件分支
    workflow.add_conditional_edges(
        "batch_action_saver",
        should_continue_batches,
        {
            "continue": "batch_action_generator",  # 继续下一个批次
            "assemble_track": "track_assembler"    # 所有批次完成 → 组装Track
        }
    )

    # Track组装后的条件分支
    workflow.add_conditional_edges(
        "track_assembler",
        should_continue_tracks_batch,
        {
            "continue": "plan_track_batches",  # 继续下一个Track
            "assemble_skill": "skill_assembler"  # 所有Track完成 → 组装技能
        }
    )

    # 技能组装后的条件分支
    workflow.add_conditional_edges(
        "skill_assembler",
        should_finalize_or_fail,
        {
            "finalize": "finalize",  # 组装成功 → 最终化
            "failed": "finalize"      # 组装失败 → 也进入最终化（带错误信息）
        }
    )

    # 最终化 → 结束
    workflow.add_edge("finalize", END)

    # ==================== 配置持久化 ====================

    checkpoint_dir = os.path.join(
        os.path.dirname(__file__), "..", "..", "Data", "checkpoints"
    )
    checkpoint_db = os.path.join(checkpoint_dir, "action_batch_skill_generation.db")

    checkpointer = get_checkpointer(checkpoint_db)

    # ==================== 编译图 ====================

    return workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=[],
        interrupt_after=[],
        debug=False
    )


# 全局图实例（单例）
_action_batch_skill_generation_graph = None


def get_action_batch_skill_generation_graph():
    """获取Action批次级技能生成图的单例实例"""
    global _action_batch_skill_generation_graph

    if _action_batch_skill_generation_graph is None:
        _action_batch_skill_generation_graph = build_action_batch_skill_generation_graph()
        logger.info("✅ Action批次级渐进式技能生成图已初始化")

    return _action_batch_skill_generation_graph


# ==================== 状态初始化 ====================

def _create_action_batch_initial_state(
    requirement: str,
    similar_skills: list = None,
    max_batch_retries: int = 2,
    token_budget: int = 100000,
    thread_id: str = None
) -> dict:
    """
    创建Action批次级渐进式生成的初始状态

    Args:
        requirement: 需求描述
        similar_skills: 相似技能列表（可选）
        max_batch_retries: 单个批次的最大重试次数
        token_budget: Token预算上限
        thread_id: 线程ID

    Returns:
        初始状态字典
    """
    return {
        "requirement": requirement,
        "similar_skills": similar_skills or [],
        # 阶段1
        "skill_skeleton": {},
        "skeleton_validation_errors": [],
        "track_plan": [],
        # 阶段2
        "current_track_index": 0,
        "current_track_batch_plan": [],
        # 阶段3
        "current_batch_index": 0,
        "current_batch_actions": [],
        "current_batch_errors": [],
        "batch_retry_count": 0,
        "max_batch_retries": max_batch_retries,
        # 语义上下文
        "batch_context": {},
        # Token监控
        "total_tokens_used": 0,
        "batch_token_history": [],
        "token_budget": token_budget,
        "adaptive_batch_size": 3,  # 默认批次大小
        # 阶段4
        "accumulated_track_actions": [],
        "generated_tracks": [],
        # 阶段5
        "assembled_skill": {},
        "final_validation_errors": [],
        # 兼容字段
        "final_result": {},
        "is_valid": False,
        # 通用
        "messages": [],
        "thread_id": thread_id or "",
    }


# ==================== 便捷调用接口 ====================

async def generate_skill_action_batch(
    requirement: str,
    similar_skills: list = None,
    max_batch_retries: int = 2,
    token_budget: int = 100000,
    resume_thread_id: str = None
) -> dict:
    """
    Action批次级渐进式技能生成（异步，支持断点恢复）

    Args:
        requirement: 需求描述
        similar_skills: 相似技能列表（可选）
        max_batch_retries: 单个批次的最大重试次数（默认2,快速失败）
        token_budget: Token预算上限（默认100000）
        resume_thread_id: 恢复的thread_id（如提供，将尝试从checkpoint恢复）

    Returns:
        包含 final_result、messages 等的字典
    """
    graph = get_action_batch_skill_generation_graph()

    # 生成thread_id
    thread_id = resume_thread_id or f"action_batch_{hash(requirement) % 10000}"

    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 200  # 批次级需要更多循环（5 Tracks × 3 batches × 多次重试）
    }

    # 尝试从checkpoint恢复
    if resume_thread_id:
        try:
            state = await graph.aget_state(config)
            if state and state.values:
                logger.info(f"✅ 从checkpoint恢复执行 (thread_id={resume_thread_id})")
                logger.info(f"   恢复状态: Track {state.values.get('current_track_index', 0)}/{len(state.values.get('track_plan', []))}, "
                           f"批次 {state.values.get('current_batch_index', 0)}")
                # 继续执行
                result = await graph.ainvoke(None, config)
                return result
        except Exception as e:
            logger.warning(f"⚠️ 从checkpoint恢复失败，将重新开始: {e}")

    # 初始化新状态
    initial_state = _create_action_batch_initial_state(
        requirement=requirement,
        similar_skills=similar_skills,
        max_batch_retries=max_batch_retries,
        token_budget=token_budget,
        thread_id=thread_id
    )

    try:
        result = await graph.ainvoke(initial_state, config)
        return result
    except GraphRecursionError as e:
        logger.error(f"❌ 图执行超过递归限制(200): {e}")
        return {
            "requirement": requirement,
            "final_result": {},
            "is_valid": False,
            "thread_id": thread_id,  # 返回thread_id以便后续恢复
            "messages": [{"type": "error", "content": f"生成过程超过递归限制，技能可能过于复杂: {str(e)}"}],
        }


def generate_skill_action_batch_sync(
    requirement: str,
    similar_skills: list = None,
    max_batch_retries: int = 2,
    token_budget: int = 100000,
    resume_thread_id: str = None
) -> dict:
    """
    Action批次级渐进式技能生成（同步，支持断点恢复）

    Args:
        requirement: 需求描述
        similar_skills: 相似技能列表（可选）
        max_batch_retries: 单个批次的最大重试次数（默认2）
        token_budget: Token预算上限（默认100000）
        resume_thread_id: 恢复的thread_id（如提供，将尝试从checkpoint恢复）

    Returns:
        包含 final_result、messages 等的字典
    """
    graph = get_action_batch_skill_generation_graph()

    # 生成thread_id
    thread_id = resume_thread_id or f"action_batch_{hash(requirement) % 10000}"

    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 200
    }

    # 尝试从checkpoint恢复
    if resume_thread_id:
        try:
            state = graph.get_state(config)
            if state and state.values:
                logger.info(f"✅ 从checkpoint恢复执行 (thread_id={resume_thread_id})")
                logger.info(f"   恢复状态: Track {state.values.get('current_track_index', 0)}/{len(state.values.get('track_plan', []))}, "
                           f"批次 {state.values.get('current_batch_index', 0)}")
                # 继续执行
                result = graph.invoke(None, config)
                return result
        except Exception as e:
            logger.warning(f"⚠️ 从checkpoint恢复失败，将重新开始: {e}")

    # 初始化新状态
    initial_state = _create_action_batch_initial_state(
        requirement=requirement,
        similar_skills=similar_skills,
        max_batch_retries=max_batch_retries,
        token_budget=token_budget,
        thread_id=thread_id
    )

    try:
        result = graph.invoke(initial_state, config)
        return result
    except GraphRecursionError as e:
        logger.error(f"❌ 图执行超过递归限制(200): {e}")
        return {
            "requirement": requirement,
            "final_result": {},
            "is_valid": False,
            "thread_id": thread_id,  # 返回thread_id以便后续恢复
            "messages": [{"type": "error", "content": f"生成过程超过递归限制，技能可能过于复杂: {str(e)}"}],
        }


def get_generation_progress(thread_id: str) -> dict:
    """
    获取技能生成进度（用于断点恢复前查看状态）

    Args:
        thread_id: 线程ID

    Returns:
        进度信息字典
    """
    graph = get_action_batch_skill_generation_graph()

    config = {"configurable": {"thread_id": thread_id}}

    try:
        state = graph.get_state(config)
        if not state or not state.values:
            return {"status": "not_found", "message": f"未找到thread_id={thread_id}的checkpoint"}

        values = state.values
        track_plan = values.get("track_plan", [])
        generated_tracks = values.get("generated_tracks", [])
        batch_plan = values.get("current_track_batch_plan", [])

        return {
            "status": "found",
            "thread_id": thread_id,
            "requirement": values.get("requirement", "")[:50] + "...",
            "skill_name": values.get("skill_skeleton", {}).get("skillName", "未生成"),
            "progress": {
                "total_tracks": len(track_plan),
                "completed_tracks": len(generated_tracks),
                "current_track_index": values.get("current_track_index", 0),
                "current_batch_index": values.get("current_batch_index", 0),
                "total_batches_in_track": len(batch_plan),
            },
            "token_usage": {
                "total_used": values.get("total_tokens_used", 0),
                "budget": values.get("token_budget", 100000),
                "usage_rate": f"{values.get('total_tokens_used', 0) / values.get('token_budget', 100000) * 100:.1f}%",
            },
            "is_complete": values.get("is_valid", False),
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


# ==================== 可视化 ====================

def visualize_action_batch_graph():
    """
    生成 Mermaid 图表（用于文档）

    Returns:
        Mermaid 格式的图表字符串
    """
    graph = get_action_batch_skill_generation_graph()
    return graph.get_graph().draw_mermaid()


# ==================== 流式输出API ====================

async def generate_skill_action_batch_streaming(
    requirement: str,
    similar_skills: list = None,
    max_batch_retries: int = 2,
    token_budget: int = 100000,
    consumer: Optional[StreamConsumer] = None,
    on_progress: Optional[Callable[[Dict[str, Any]], None]] = None,
    resume_thread_id: str = None
) -> dict:
    """
    Action批次级渐进式技能生成（异步流式，支持实时进度反馈）

    这是推荐的生成方式，提供实时进度反馈。

    Args:
        requirement: 需求描述
        similar_skills: 相似技能列表（可选）
        max_batch_retries: 单个批次的最大重试次数（默认2）
        token_budget: Token预算上限（默认100000）
        consumer: 流式消费者（可选，默认使用PrintStreamConsumer）
        on_progress: 进度回调函数（可选，简化用法）
        resume_thread_id: 恢复的thread_id（如提供，将尝试从checkpoint恢复）

    Returns:
        包含 final_result、messages 等的字典

    Example:
        # 使用回调函数
        async def my_progress(event):
            print(f"Progress: {event.get('progress', 0)*100:.1f}%")

        result = await generate_skill_action_batch_streaming(
            "创建一个火球术技能",
            on_progress=my_progress
        )

        # 使用自定义消费者
        from skill_agent.orchestration.streaming import PrintStreamConsumer
        result = await generate_skill_action_batch_streaming(
            "创建一个火球术技能",
            consumer=PrintStreamConsumer(show_progress_bar=True)
        )
    """
    graph = get_action_batch_skill_generation_graph()

    # 生成thread_id
    thread_id = resume_thread_id or f"action_batch_stream_{hash(requirement) % 10000}"

    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 200
    }

    # 选择消费者
    if consumer is None:
        if on_progress is not None:
            consumer = CallbackStreamConsumer(on_progress=on_progress)
        else:
            consumer = PrintStreamConsumer(show_progress_bar=True)

    # 尝试从checkpoint恢复
    if resume_thread_id:
        try:
            state = await graph.aget_state(config)
            if state and state.values:
                logger.info(f"✅ 从checkpoint恢复流式执行 (thread_id={resume_thread_id})")
                # 继续执行（流式）
                result = await stream_graph_execution(
                    graph, None, config, consumer
                )
                return result
        except Exception as e:
            logger.warning(f"⚠️ 从checkpoint恢复失败，将重新开始: {e}")

    # 初始化新状态
    initial_state = _create_action_batch_initial_state(
        requirement=requirement,
        similar_skills=similar_skills,
        max_batch_retries=max_batch_retries,
        token_budget=token_budget,
        thread_id=thread_id
    )

    try:
        result = await stream_graph_execution(
            graph, initial_state, config, consumer
        )
        return result

    except GraphRecursionError as e:
        logger.error(f"❌ 图执行超过递归限制(200): {e}")
        return {
            "requirement": requirement,
            "final_result": {},
            "is_valid": False,
            "thread_id": thread_id,
            "messages": [{"type": "error", "content": f"生成过程超过递归限制: {str(e)}"}],
        }


def generate_skill_action_batch_streaming_sync(
    requirement: str,
    similar_skills: list = None,
    max_batch_retries: int = 2,
    token_budget: int = 100000,
    consumer: Optional[StreamConsumer] = None,
    on_progress: Optional[Callable[[Dict[str, Any]], None]] = None,
    resume_thread_id: str = None
) -> dict:
    """
    Action批次级渐进式技能生成（同步流式，支持实时进度反馈）

    Args:
        requirement: 需求描述
        similar_skills: 相似技能列表（可选）
        max_batch_retries: 单个批次的最大重试次数（默认2）
        token_budget: Token预算上限（默认100000）
        consumer: 流式消费者（可选，默认使用PrintStreamConsumer）
        on_progress: 进度回调函数（可选，简化用法）
        resume_thread_id: 恢复的thread_id

    Returns:
        包含 final_result、messages 等的字典

    Example:
        # 最简用法（自动打印进度）
        result = generate_skill_action_batch_streaming_sync("创建一个火球术技能")

        # 使用回调
        def my_progress(event):
            print(f"[{event.get('event_type')}] {event.get('message')}")

        result = generate_skill_action_batch_streaming_sync(
            "创建一个火球术技能",
            on_progress=my_progress
        )
    """
    graph = get_action_batch_skill_generation_graph()

    # 生成thread_id
    thread_id = resume_thread_id or f"action_batch_stream_{hash(requirement) % 10000}"

    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 200
    }

    # 选择消费者
    if consumer is None:
        if on_progress is not None:
            consumer = CallbackStreamConsumer(on_progress=on_progress)
        else:
            consumer = PrintStreamConsumer(show_progress_bar=True)

    # 尝试从checkpoint恢复
    if resume_thread_id:
        try:
            state = graph.get_state(config)
            if state and state.values:
                logger.info(f"✅ 从checkpoint恢复流式执行 (thread_id={resume_thread_id})")
                result = stream_graph_execution_sync(
                    graph, None, config, consumer
                )
                return result
        except Exception as e:
            logger.warning(f"⚠️ 从checkpoint恢复失败，将重新开始: {e}")

    # 初始化新状态
    initial_state = _create_action_batch_initial_state(
        requirement=requirement,
        similar_skills=similar_skills,
        max_batch_retries=max_batch_retries,
        token_budget=token_budget,
        thread_id=thread_id
    )

    try:
        result = stream_graph_execution_sync(
            graph, initial_state, config, consumer
        )
        return result

    except GraphRecursionError as e:
        logger.error(f"❌ 图执行超过递归限制(200): {e}")
        return {
            "requirement": requirement,
            "final_result": {},
            "is_valid": False,
            "thread_id": thread_id,
            "messages": [{"type": "error", "content": f"生成过程超过递归限制: {str(e)}"}],
        }


def create_progress_callback(
    on_batch_complete: Optional[Callable[[int, int, int], None]] = None,
    on_track_complete: Optional[Callable[[str, int, int], None]] = None,
    on_progress_update: Optional[Callable[[float, str], None]] = None,
) -> Callable[[Dict[str, Any]], None]:
    """
    创建进度回调函数（便捷工厂）

    Args:
        on_batch_complete: 批次完成回调 (batch_idx, total_batches, action_count)
        on_track_complete: Track完成回调 (track_name, track_idx, total_tracks)
        on_progress_update: 进度更新回调 (progress_percent, message)

    Returns:
        可用于流式API的回调函数

    Example:
        callback = create_progress_callback(
            on_batch_complete=lambda b, t, a: print(f"批次 {b+1}/{t} 完成，{a} 个actions"),
            on_track_complete=lambda n, i, t: print(f"Track '{n}' 完成 ({i+1}/{t})"),
            on_progress_update=lambda p, m: print(f"进度 {p:.1f}%: {m}")
        )

        result = generate_skill_action_batch_streaming_sync(
            "创建火球术",
            on_progress=callback
        )
    """
    def callback(event: Dict[str, Any]):
        event_type = event.get("event_type", "")
        progress = event.get("progress")
        message = event.get("message", "")

        # 进度更新
        if on_progress_update and progress is not None:
            on_progress_update(progress * 100, message)

        # 批次完成
        if event_type == "batch_completed" and on_batch_complete:
            data = event.get("data", {})
            batch_idx = event.get("batch_index", 0)
            total_batches = event.get("total_batches", 1)
            action_count = data.get("action_count", 0)
            on_batch_complete(batch_idx, total_batches, action_count)

        # Track完成
        if event_type == "track_completed" and on_track_complete:
            data = event.get("data", {})
            track_name = data.get("track_name", "")
            track_idx = event.get("track_index", 0)
            total_tracks = event.get("total_tracks", 1)
            on_track_complete(track_name, track_idx, total_tracks)

    return callback

"""
渐进式技能生成图（Progressive Skill Generation Graph）
实现三阶段生成：骨架生成 → 逐Track生成 → 技能组装

相比一次性生成的优势：
1. Token 消耗降低 30%+（每阶段输出更短）
2. 错误隔离（单 track 失败不影响整体）
3. 精准 RAG 检索（根据 track 类型过滤）
4. 进度可见（用户体验提升）
"""

from langgraph.graph import StateGraph, END
import os
import logging
from .utils import get_checkpointer

from ..nodes.progressive_skill_nodes import (
    ProgressiveSkillGenerationState,
    # 阶段1：骨架生成
    skeleton_generator_node,
    should_continue_to_track_generation,
    # 阶段2：Track 生成循环
    track_action_generator_node,
    track_validator_node,
    track_fixer_node,
    track_saver_node,
    should_fix_track,
    should_continue_tracks,
    # 阶段3：技能组装
    skill_assembler_node,
    finalize_progressive_node,
    should_finalize_or_fail,
)

logger = logging.getLogger(__name__)


def build_progressive_skill_generation_graph():
    """
    构建渐进式技能生成 LangGraph

    流程：
    1. skeleton_generator: 生成技能骨架和 track 计划
    2. 判断骨架是否有效：
       - 有效 → 进入 track 生成循环
       - 无效 → 直接失败
    3. track_action_generator: 为当前 track 生成 actions
    4. track_validator: 验证当前 track
    5. 判断验证结果：
       - 通过 → track_saver（保存）
       - 失败且未达重试上限 → track_fixer（修复）→ 重新验证
       - 失败且达到上限 → track_saver（跳过，带警告）
    6. 判断是否继续：
       - 还有 track → 回到 track_action_generator
       - 全部完成 → skill_assembler
    7. skill_assembler: 组装完整技能
    8. finalize: 输出最终结果

    Returns:
        编译后的 LangGraph
    """
    # 创建 StateGraph
    workflow = StateGraph(ProgressiveSkillGenerationState)

    # ==================== 添加节点 ====================

    # 阶段1：骨架生成
    workflow.add_node("skeleton_generator", skeleton_generator_node)

    # 阶段2：Track 生成循环
    workflow.add_node("track_action_generator", track_action_generator_node)
    workflow.add_node("track_validator", track_validator_node)
    workflow.add_node("track_fixer", track_fixer_node)
    workflow.add_node("track_saver", track_saver_node)

    # 阶段3：技能组装
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
            "generate_tracks": "track_action_generator",  # 骨架有效 → 开始生成 tracks
            "skeleton_failed": "finalize"                  # 骨架无效 → 直接结束
        }
    )

    # Track 生成 → 验证
    workflow.add_edge("track_action_generator", "track_validator")

    # Track 验证后的条件分支
    workflow.add_conditional_edges(
        "track_validator",
        should_fix_track,
        {
            "save": "track_saver",   # 验证通过 → 保存
            "fix": "track_fixer",    # 需要修复 → 进入 fixer
            "skip": "track_saver"    # 达到上限 → 跳过（保存空或部分结果）
        }
    )

    # Track 修复 → 重新验证
    workflow.add_edge("track_fixer", "track_validator")

    # Track 保存后的条件分支
    workflow.add_conditional_edges(
        "track_saver",
        should_continue_tracks,
        {
            "continue": "track_action_generator",  # 继续生成下一个 track
            "assemble": "skill_assembler"          # 全部完成 → 组装
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

    # 创建 checkpoints 目录
    checkpoint_dir = os.path.join(
        os.path.dirname(__file__), "..", "..", "Data", "checkpoints"
    )
    checkpoint_db = os.path.join(checkpoint_dir, "progressive_skill_generation.db")

    # 获取 checkpointer（部署环境返回 None）
    checkpointer = get_checkpointer(checkpoint_db)

    # ==================== 编译图 ====================

    return workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=[],  # 可选：支持 human-in-the-loop
        interrupt_after=[],
        debug=False
    )


# 全局图实例（单例）
_progressive_skill_generation_graph = None


def get_progressive_skill_generation_graph():
    """获取渐进式技能生成图的单例实例"""
    global _progressive_skill_generation_graph

    if _progressive_skill_generation_graph is None:
        _progressive_skill_generation_graph = build_progressive_skill_generation_graph()
        logger.info("✅ 渐进式技能生成图已初始化")

    return _progressive_skill_generation_graph


# ==================== 便捷调用接口 ====================

async def generate_skill_progressive(
    requirement: str,
    similar_skills: list = None,
    max_track_retries: int = 3
) -> dict:
    """
    渐进式技能生成（异步）

    Args:
        requirement: 需求描述
        similar_skills: 相似技能列表（可选，用于 RAG）
        max_track_retries: 单个 track 的最大重试次数

    Returns:
        包含 final_result、messages 等的字典
    """
    graph = get_progressive_skill_generation_graph()

    initial_state = {
        "requirement": requirement,
        "similar_skills": similar_skills or [],
        # 阶段1输出
        "skill_skeleton": {},
        "skeleton_validation_errors": [],
        # 阶段2状态
        "track_plan": [],
        "current_track_index": 0,
        "current_track_data": {},
        "generated_tracks": [],
        "current_track_errors": [],
        "track_retry_count": 0,
        "max_track_retries": max_track_retries,
        # 阶段3输出
        "assembled_skill": {},
        "final_validation_errors": [],
        # 兼容旧版字段
        "final_result": {},
        "is_valid": False,
        # 通用
        "messages": [],
    }

    # 配置
    config = {
        "configurable": {"thread_id": f"progressive_{hash(requirement) % 10000}"},
        "recursion_limit": 100  # 渐进式生成可能有更多循环
    }

    result = await graph.ainvoke(initial_state, config)
    return result


def generate_skill_progressive_sync(
    requirement: str,
    similar_skills: list = None,
    max_track_retries: int = 3
) -> dict:
    """
    渐进式技能生成（同步）

    Args:
        requirement: 需求描述
        similar_skills: 相似技能列表（可选）
        max_track_retries: 单个 track 的最大重试次数

    Returns:
        包含 final_result、messages 等的字典
    """
    graph = get_progressive_skill_generation_graph()

    initial_state = {
        "requirement": requirement,
        "similar_skills": similar_skills or [],
        # 阶段1输出
        "skill_skeleton": {},
        "skeleton_validation_errors": [],
        # 阶段2状态
        "track_plan": [],
        "current_track_index": 0,
        "current_track_data": {},
        "generated_tracks": [],
        "current_track_errors": [],
        "track_retry_count": 0,
        "max_track_retries": max_track_retries,
        # 阶段3输出
        "assembled_skill": {},
        "final_validation_errors": [],
        # 兼容旧版字段
        "final_result": {},
        "is_valid": False,
        # 通用
        "messages": [],
    }

    # 配置
    config = {
        "configurable": {"thread_id": f"progressive_{hash(requirement) % 10000}"},
        "recursion_limit": 100
    }

    result = graph.invoke(initial_state, config)
    return result


# ==================== 可视化 ====================

def visualize_progressive_graph():
    """
    生成 Mermaid 图表（用于文档）

    Returns:
        Mermaid 格式的图表字符串
    """
    graph = get_progressive_skill_generation_graph()
    return graph.get_graph().draw_mermaid()

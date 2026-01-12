"""
并行渐进式技能生成图（Parallel Progressive Skill Generation Graph）
实现三阶段生成：骨架生成 → 并行Track生成 → 技能组装

相比串行版本的优势：
1. Track 并行生成，显著降低总耗时（预估提升 40-60%）
2. 使用 LangGraph Send API 实现 Map-Reduce 模式
3. 保留错误隔离能力（单 track 失败不影响其他）
"""

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
import os
import logging
import operator
from typing import Any, Dict, List, TypedDict, Annotated, Optional
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

from .utils import get_checkpointer
from ..config import get_skill_gen_config
from ..nodes.progressive_skill_nodes import (
    skeleton_generator_node,
    skeleton_fixer_node,
    should_continue_to_track_generation,
    skill_assembler_node,
    finalize_progressive_node,
    should_finalize_or_fail,
    validate_skeleton,
    infer_track_type,
    search_actions_by_track_type,
    format_action_schemas_for_prompt,
    validate_track,
    get_default_actions_for_track_type,
)

logger = logging.getLogger(__name__)


# ==================== 并行 Track 生成的 State 定义 ====================

def merge_track_results(left: List[Dict], right: List[Dict]) -> List[Dict]:
    """
    合并 Track 结果的 reducer 函数
    
    用于 operator.add 无法处理的复杂合并场景
    """
    if left is None:
        left = []
    if right is None:
        right = []
    return left + right


class ParallelTrackState(TypedDict):
    """
    单个 Track 并行生成的输入状态
    
    由 Send 对象传递给 parallel_track_generator 节点
    """
    track_index: int
    track_plan_item: Dict[str, Any]
    skill_skeleton: Dict[str, Any]
    requirement: str
    max_track_retries: int


class ParallelProgressiveState(TypedDict):
    """
    并行渐进式技能生成的主状态
    
    与串行版本的主要区别：
    - generated_tracks 使用 operator.add reducer 支持并行写入
    - 移除 current_track_index 等串行控制字段
    """
    # === 输入 ===
    requirement: str
    similar_skills: List[Dict[str, Any]]
    
    # === 阶段1输出 ===
    skill_skeleton: Dict[str, Any]
    skeleton_validation_errors: List[str]
    skeleton_retry_count: int
    max_skeleton_retries: int
    
    # === 阶段2状态（并行） ===
    track_plan: List[Dict[str, Any]]
    # 使用 operator.add 作为 reducer，支持并行节点写入
    generated_tracks: Annotated[List[Dict[str, Any]], operator.add]
    track_errors: Annotated[List[str], operator.add]
    max_track_retries: int
    
    # === 阶段3输出 ===
    assembled_skill: Dict[str, Any]
    final_validation_errors: List[str]
    
    # === 兼容旧版 ===
    final_result: Dict[str, Any]
    is_valid: bool
    
    # === 通用 ===
    messages: Annotated[List[AnyMessage], add_messages]


# ==================== 并行 Track 生成节点 ====================

def parallel_track_generator_node(state: ParallelTrackState) -> Dict[str, Any]:
    """
    并行 Track 生成节点
    
    每个 Track 独立生成，由 Send 对象分发
    包含内置的验证和重试逻辑
    
    Args:
        state: 单个 Track 的生成状态（由 Send 传入）
    
    Returns:
        包含 generated_tracks 的字典（会被 reducer 合并）
    """
    import json
    import time
    from langchain_core.messages import AIMessage
    from pydantic import ValidationError
    from ..prompts.prompt_manager import get_prompt_manager
    from ..nodes.json_utils import extract_json_from_markdown
    from ..nodes.skill_nodes import get_openai_client
    from ..schemas import SkillTrack
    
    track_index = state["track_index"]
    track_plan_item = state["track_plan_item"]
    skeleton = state["skill_skeleton"]
    requirement = state["requirement"]
    max_retries = state.get("max_track_retries", 3)
    
    track_name = track_plan_item.get("trackName", f"Track_{track_index}")
    purpose = track_plan_item.get("purpose", "")
    estimated_actions = track_plan_item.get("estimatedActions", 1)
    
    logger.info(f"[Parallel] Starting Track [{track_index}]: {track_name}")
    
    # RAG 检索
    track_type = infer_track_type(track_name)
    relevant_actions = search_actions_by_track_type(
        track_type=track_type,
        purpose=purpose,
        top_k=5
    )
    
    if not relevant_actions:
        logger.warning(f"[Parallel] No RAG results for {track_name}, using defaults")
        relevant_actions = get_default_actions_for_track_type(track_type)
    
    action_schemas_text = format_action_schemas_for_prompt(relevant_actions)
    
    # 获取 Prompt
    prompt_mgr = get_prompt_manager()
    prompt = prompt_mgr.get_prompt("track_action_generation")
    
    # 重试循环
    retry_count = 0
    last_error = None
    track_data = None
    
    while retry_count <= max_retries:
        try:
            client = get_openai_client()
            
            prompt_inputs = {
                "skillName": skeleton.get("skillName", "Unknown"),
                "totalDuration": skeleton.get("totalDuration", 150),
                "trackName": track_name,
                "purpose": purpose,
                "estimatedActions": estimated_actions,
                "relevant_actions": action_schemas_text or "No reference"
            }
            prompt_value = prompt.invoke(prompt_inputs)
            
            # 转换为 OpenAI 格式
            openai_messages = []
            for msg in prompt_value.to_messages():
                msg_type = msg.__class__.__name__.lower()
                if "system" in msg_type:
                    openai_messages.append({"role": "system", "content": msg.content})
                elif "human" in msg_type:
                    openai_messages.append({"role": "user", "content": msg.content})
                else:
                    openai_messages.append({"role": "user", "content": msg.content})
            
            # 非流式调用（并行时流式意义不大）
            model_name = get_skill_gen_config().llm.model
            response = client.chat.completions.create(
                model=model_name,
                messages=openai_messages,
                stream=False
            )
            
            content = response.choices[0].message.content
            json_content = extract_json_from_markdown(content)
            track_dict = json.loads(json_content)
            
            # Pydantic 验证
            validated = SkillTrack.model_validate(track_dict)
            track_data = validated.model_dump()
            
            # 确保 trackName 正确
            track_data["trackName"] = track_name
            
            # 业务验证
            total_duration = skeleton.get("totalDuration", 150)
            validation_errors = validate_track(track_data, total_duration)
            
            if not validation_errors:
                logger.info(f"[Parallel] Track [{track_index}] {track_name} completed successfully")
                break
            else:
                last_error = "; ".join(validation_errors)
                logger.warning(f"[Parallel] Track [{track_index}] validation failed: {last_error}")
                retry_count += 1
                
        except Exception as e:
            last_error = str(e)
            logger.error(f"[Parallel] Track [{track_index}] error: {e}")
            retry_count += 1
    
    # 返回结果
    if track_data and retry_count <= max_retries:
        return {
            "generated_tracks": [track_data],
            "track_errors": []
        }
    else:
        error_msg = f"Track [{track_index}] {track_name} failed after {retry_count} retries: {last_error}"
        logger.error(f"[Parallel] {error_msg}")
        return {
            "generated_tracks": [],
            "track_errors": [error_msg]
        }


def route_after_skeleton(state: ParallelProgressiveState):
    """
    骨架生成后的路由函数
    
    返回值：
    - List[Send]: 骨架有效时，返回 Send 列表进行并行 Track 生成
    - "skeleton_fixer": 骨架需要修复
    - "finalize": 骨架失败
    """
    errors = state.get("skeleton_validation_errors", [])
    retry_count = state.get("skeleton_retry_count", 0)
    max_retries = state.get("max_skeleton_retries", 2)
    track_plan = state.get("track_plan", [])
    
    # 骨架有效且有 track_plan -> 并行分发
    if not errors and track_plan:
        skeleton = state.get("skill_skeleton", {})
        requirement = state.get("requirement", "")
        max_track_retries = state.get("max_track_retries", 3)
        
        logger.info(f"[Route] Skeleton valid, dispatching {len(track_plan)} tracks")
        
        return [
            Send(
                "parallel_track_generator",
                {
                    "track_index": i,
                    "track_plan_item": track_item,
                    "skill_skeleton": skeleton,
                    "requirement": requirement,
                    "max_track_retries": max_track_retries
                }
            )
            for i, track_item in enumerate(track_plan)
        ]
    
    # 骨架需要修复
    if errors and retry_count < max_retries:
        logger.info(f"[Route] Skeleton needs fix (retry {retry_count + 1}/{max_retries})")
        return "skeleton_fixer"
    
    # 骨架失败
    logger.warning("[Route] Skeleton failed, going to finalize")
    return "finalize"


# ==================== 构建并行图 ====================

def build_parallel_progressive_graph():
    """
    构建并行渐进式技能生成 LangGraph
    
    流程：
    1. skeleton_generator: 生成技能骨架和 track 计划
    2. 判断骨架是否有效：
       - 有效 → fan_out 到并行 track 生成
       - 需修复 → skeleton_fixer
       - 失败 → finalize
    3. parallel_track_generator: 并行生成所有 tracks（Map）
    4. skill_assembler: 收集并组装完整技能（Reduce）
    5. finalize: 输出最终结果
    """
    workflow = StateGraph(ParallelProgressiveState)
    
    # 阶段1：骨架生成
    workflow.add_node("skeleton_generator", skeleton_generator_node)
    workflow.add_node("skeleton_fixer", skeleton_fixer_node)
    
    # 阶段2：并行 Track 生成
    workflow.add_node("parallel_track_generator", parallel_track_generator_node)
    
    # 阶段3：技能组装
    workflow.add_node("skill_assembler", skill_assembler_node)
    workflow.add_node("finalize", finalize_progressive_node)
    
    # 入口点
    workflow.add_edge(START, "skeleton_generator")
    
    # 骨架生成后：使用 fan_out_to_tracks 进行并行分发
    # 当骨架有效时返回 Send 列表，否则返回路由字符串
    workflow.add_conditional_edges(
        "skeleton_generator",
        route_after_skeleton,
        ["parallel_track_generator", "skeleton_fixer", "finalize"]
    )
    
    # 骨架修复后重新判断
    workflow.add_conditional_edges(
        "skeleton_fixer",
        route_after_skeleton,
        ["parallel_track_generator", "skeleton_fixer", "finalize"]
    )
    
    # Fan-in: 所有并行 Track 完成后进入组装
    workflow.add_edge("parallel_track_generator", "skill_assembler")
    
    # 技能组装后的条件分支
    workflow.add_conditional_edges(
        "skill_assembler",
        should_finalize_or_fail,
        {
            "finalize": "finalize",
            "failed": "finalize"
        }
    )
    
    workflow.add_edge("finalize", END)
    
    # 配置持久化
    checkpoint_dir = os.path.join(
        os.path.dirname(__file__), "..", "..", "Data", "checkpoints"
    )
    checkpoint_db = os.path.join(checkpoint_dir, "parallel_progressive.db")
    checkpointer = get_checkpointer(checkpoint_db)
    
    return workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=[],
        interrupt_after=[],
        debug=False
    )


# ==================== 全局实例 ====================

_parallel_progressive_graph = None


def get_parallel_progressive_graph():
    """获取并行渐进式技能生成图的单例实例"""
    global _parallel_progressive_graph
    
    if _parallel_progressive_graph is None:
        _parallel_progressive_graph = build_parallel_progressive_graph()
        logger.info("Parallel progressive skill generation graph initialized")
    
    return _parallel_progressive_graph


# ==================== 状态初始化 ====================

def _create_parallel_initial_state(
    requirement: str,
    similar_skills: list = None,
    max_track_retries: int = 3,
    max_skeleton_retries: int = 2
) -> dict:
    """创建并行渐进式技能生成的初始状态"""
    return {
        "requirement": requirement,
        "similar_skills": similar_skills or [],
        "skill_skeleton": {},
        "skeleton_validation_errors": [],
        "skeleton_retry_count": 0,
        "max_skeleton_retries": max_skeleton_retries,
        "track_plan": [],
        "generated_tracks": [],
        "track_errors": [],
        "max_track_retries": max_track_retries,
        "assembled_skill": {},
        "final_validation_errors": [],
        "final_result": {},
        "is_valid": False,
        "messages": [],
    }


# ==================== 便捷调用接口 ====================

async def generate_skill_parallel(
    requirement: str,
    similar_skills: list = None,
    max_track_retries: int = 3
) -> dict:
    """
    并行渐进式技能生成（异步）
    
    相比串行版本，Track 生成阶段并行执行，显著降低总耗时。
    """
    graph = get_parallel_progressive_graph()
    
    initial_state = _create_parallel_initial_state(
        requirement=requirement,
        similar_skills=similar_skills,
        max_track_retries=max_track_retries
    )
    
    config = {
        "configurable": {"thread_id": f"parallel_{hash(requirement) % 10000}"},
        "recursion_limit": 100
    }
    
    result = await graph.ainvoke(initial_state, config)
    return result


def generate_skill_parallel_sync(
    requirement: str,
    similar_skills: list = None,
    max_track_retries: int = 3
) -> dict:
    """并行渐进式技能生成（同步）"""
    graph = get_parallel_progressive_graph()
    
    initial_state = _create_parallel_initial_state(
        requirement=requirement,
        similar_skills=similar_skills,
        max_track_retries=max_track_retries
    )
    
    config = {
        "configurable": {"thread_id": f"parallel_{hash(requirement) % 10000}"},
        "recursion_limit": 100
    }
    
    result = graph.invoke(initial_state, config)
    return result


def visualize_parallel_graph():
    """生成 Mermaid 图表"""
    graph = get_parallel_progressive_graph()
    return graph.get_graph().draw_mermaid()

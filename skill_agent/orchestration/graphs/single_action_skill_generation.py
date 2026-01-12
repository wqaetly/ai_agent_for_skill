"""
Single Action Progressive Skill Generation Graph

Implements the finest granularity generation:
Skeleton -> Track Plan -> Single Action Loop -> Track Assembly -> Skill Assembly

Advantages:
- Shortest context per LLM call, avoiding hallucination
- Finest error isolation (single action failure doesn't affect others)
- Highest generation quality (focus on one action at a time)
"""

from langgraph.graph import StateGraph, END
from langgraph.errors import GraphRecursionError
import os
import logging
from typing import Optional, Callable, Dict, Any

from .utils import get_checkpointer
from ..nodes.single_action_skill_nodes import (
    SingleActionProgressiveState,
    # Phase 1: Skeleton (reused)
    skeleton_generator_node,
    should_continue_to_track_generation,
    # Phase 2: Track Action Planning
    action_planner_node,
    # Phase 3: Single Action Loop
    single_action_generator_node,
    action_accumulator_node,
    should_continue_action_loop,
    # Phase 4: Track Assembly
    track_assembler_node,
    should_continue_track_loop,
    # Phase 5: Skill Assembly (reused)
    skill_assembler_node,
    finalize_progressive_node,
    should_finalize_or_fail,
)

logger = logging.getLogger(__name__)


def build_single_action_skill_generation_graph():
    """
    Build Single Action Progressive Skill Generation LangGraph

    Flow:
    1. skeleton_generator: Generate skill skeleton
    2. Check skeleton validity
    3. plan_track_actions: Plan actions for current track
    4. single_action_generator: Generate one action
    5. single_action_validator: Validate the action
    6. Conditional:
       - Pass -> single_action_saver
       - Fail & retry available -> single_action_fixer -> re-validate
       - Fail & max retries -> single_action_saver (skip)
    7. Conditional:
       - More actions -> back to single_action_generator
       - All actions done -> track_assembler
    8. Conditional:
       - More tracks -> back to plan_track_actions
       - All tracks done -> skill_assembler
    9. skill_assembler: Assemble complete skill
    10. finalize: Output final result
    """
    workflow = StateGraph(SingleActionProgressiveState)

    # Add nodes
    workflow.add_node("skeleton_generator", skeleton_generator_node)
    workflow.add_node("action_planner", action_planner_node)
    workflow.add_node("single_action_generator", single_action_generator_node)
    workflow.add_node("action_accumulator", action_accumulator_node)
    workflow.add_node("track_assembler", track_assembler_node)
    workflow.add_node("skill_assembler", skill_assembler_node)
    workflow.add_node("finalize", finalize_progressive_node)

    # Set entry point
    workflow.set_entry_point("skeleton_generator")

    # Define edges
    workflow.add_conditional_edges(
        "skeleton_generator",
        should_continue_to_track_generation,
        {
            "generate_tracks": "action_planner",
            "fix_skeleton": "skeleton_generator",
            "skeleton_failed": "finalize"
        }
    )

    workflow.add_edge("action_planner", "single_action_generator")
    workflow.add_edge("single_action_generator", "action_accumulator")

    workflow.add_conditional_edges(
        "action_accumulator",
        should_continue_action_loop,
        {
            "next_action": "single_action_generator",
            "assemble_track": "track_assembler"
        }
    )

    workflow.add_conditional_edges(
        "track_assembler",
        should_continue_track_loop,
        {
            "next_track": "action_planner",
            "assemble_skill": "skill_assembler"
        }
    )

    workflow.add_conditional_edges(
        "skill_assembler",
        should_finalize_or_fail,
        {
            "finalize": "finalize",
            "failed": "finalize"
        }
    )

    workflow.add_edge("finalize", END)

    # Configure persistence
    checkpoint_dir = os.path.join(
        os.path.dirname(__file__), "..", "..", "Data", "checkpoints"
    )
    checkpoint_db = os.path.join(checkpoint_dir, "single_action_skill_generation.db")
    checkpointer = get_checkpointer(checkpoint_db)

    return workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=[],
        interrupt_after=[],
        debug=False
    )


# Global singleton
_single_action_skill_generation_graph = None


def get_single_action_skill_generation_graph():
    """Get singleton instance"""
    global _single_action_skill_generation_graph
    if _single_action_skill_generation_graph is None:
        _single_action_skill_generation_graph = build_single_action_skill_generation_graph()
        logger.info("Single Action Skill Generation Graph initialized")
    return _single_action_skill_generation_graph


def _create_single_action_initial_state(
    requirement: str,
    similar_skills: list = None,
    max_action_retries: int = 2,
    thread_id: str = None
) -> dict:
    """Create initial state for single action generation"""
    return {
        "requirement": requirement,
        "similar_skills": similar_skills or [],
        # Phase 1
        "skill_skeleton": {},
        "skeleton_validation_errors": [],
        "skeleton_retry_count": 0,
        "max_skeleton_retries": 2,
        "track_plan": [],
        # Phase 2
        "current_track_index": 0,
        "current_track_action_plan": [],
        # Phase 3
        "current_action_index": 0,
        "current_action_data": {},
        "current_action_errors": [],
        "action_retry_count": 0,
        "max_action_retries": max_action_retries,
        # Track accumulation
        "accumulated_track_actions": [],
        "generated_tracks": [],
        # Phase 5
        "assembled_skill": {},
        "final_validation_errors": [],
        # Compatibility
        "final_result": {},
        "is_valid": False,
        # General
        "messages": [],
        "thread_id": thread_id or "",
    }


async def generate_skill_single_action(
    requirement: str,
    similar_skills: list = None,
    max_action_retries: int = 2,
    resume_thread_id: str = None
) -> dict:
    """
    Single Action Progressive Skill Generation (async)

    Args:
        requirement: Skill requirement description
        similar_skills: Similar skills for RAG (optional)
        max_action_retries: Max retries per action (default 2)
        resume_thread_id: Thread ID to resume from checkpoint

    Returns:
        Dict with final_result, messages, etc.
    """
    graph = get_single_action_skill_generation_graph()
    thread_id = resume_thread_id or f"single_action_{hash(requirement) % 10000}"

    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 500  # Higher limit for single action loops
    }

    if resume_thread_id:
        try:
            state = await graph.aget_state(config)
            if state and state.values:
                logger.info(f"Resuming from checkpoint: {resume_thread_id}")
                result = await graph.ainvoke(None, config)
                return result
        except Exception as e:
            logger.warning(f"Resume failed, starting fresh: {e}")

    initial_state = _create_single_action_initial_state(
        requirement=requirement,
        similar_skills=similar_skills,
        max_action_retries=max_action_retries,
        thread_id=thread_id
    )

    try:
        result = await graph.ainvoke(initial_state, config)
        return result
    except GraphRecursionError as e:
        logger.error(f"Recursion limit exceeded: {e}")
        return {
            "requirement": requirement,
            "final_result": {},
            "is_valid": False,
            "thread_id": thread_id,
            "messages": [{"type": "error", "content": f"Recursion limit exceeded: {e}"}],
        }


def generate_skill_single_action_sync(
    requirement: str,
    similar_skills: list = None,
    max_action_retries: int = 2,
    resume_thread_id: str = None
) -> dict:
    """Single Action Progressive Skill Generation (sync)"""
    graph = get_single_action_skill_generation_graph()
    thread_id = resume_thread_id or f"single_action_{hash(requirement) % 10000}"

    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 500
    }

    if resume_thread_id:
        try:
            state = graph.get_state(config)
            if state and state.values:
                logger.info(f"Resuming from checkpoint: {resume_thread_id}")
                result = graph.invoke(None, config)
                return result
        except Exception as e:
            logger.warning(f"Resume failed, starting fresh: {e}")

    initial_state = _create_single_action_initial_state(
        requirement=requirement,
        similar_skills=similar_skills,
        max_action_retries=max_action_retries,
        thread_id=thread_id
    )

    try:
        result = graph.invoke(initial_state, config)
        return result
    except GraphRecursionError as e:
        logger.error(f"Recursion limit exceeded: {e}")
        return {
            "requirement": requirement,
            "final_result": {},
            "is_valid": False,
            "thread_id": thread_id,
            "messages": [{"type": "error", "content": f"Recursion limit exceeded: {e}"}],
        }


def visualize_single_action_graph():
    """Generate Mermaid diagram"""
    graph = get_single_action_skill_generation_graph()
    return graph.get_graph().draw_mermaid()

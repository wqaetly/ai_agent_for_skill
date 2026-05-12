"""
Action-Batch Skill Generation runner — replaces
`graphs/action_batch_skill_generation.py`.

Topology (matches the legacy LangGraph):
    skeleton_generator
        -> batch_planner
            -> [batch_generator -> batch_accumulator]*  (per batch in track)
                -> track_assembler
                    -> [batch_planner -> ...]            (per track)
                        -> skill_assembler -> finalize

The legacy graph's `recursion_limit=200` is reproduced via plain integer
caps on the inner/outer loops.
"""

import logging
from typing import Any, Dict, Generator

from ..nodes.action_batch_skill_nodes import (
    skeleton_generator_node,
    batch_planner_node,
    batch_generator_node,
    batch_accumulator_node,
    track_assembler_node,
    skill_assembler_node,
    finalize_progressive_node,
    should_continue_to_track_generation,
    should_continue_batch_loop,
    should_continue_track_loop,
    should_finalize_or_fail,
)

logger = logging.getLogger(__name__)


def _build_initial_state(initial_state: Dict[str, Any]) -> Dict[str, Any]:
    """Mirror `_create_action_batch_initial_state` from the legacy graph."""
    return {
        "requirement": initial_state.get("requirement", ""),
        "similar_skills": initial_state.get("similar_skills", []),
        # Phase 1
        "skill_skeleton": initial_state.get("skill_skeleton", {}),
        "skeleton_validation_errors": initial_state.get(
            "skeleton_validation_errors", []
        ),
        "track_plan": initial_state.get("track_plan", []),
        # Phase 2
        "current_track_index": initial_state.get("current_track_index", 0),
        "current_track_batch_plan": initial_state.get("current_track_batch_plan", []),
        # Phase 3
        "current_batch_index": initial_state.get("current_batch_index", 0),
        "current_batch_actions": initial_state.get("current_batch_actions", []),
        "current_batch_errors": initial_state.get("current_batch_errors", []),
        "batch_retry_count": initial_state.get("batch_retry_count", 0),
        "max_batch_retries": initial_state.get("max_batch_retries", 2),
        # Semantic context
        "batch_context": initial_state.get("batch_context", {}),
        # Token budget
        "total_tokens_used": initial_state.get("total_tokens_used", 0),
        "batch_token_history": initial_state.get("batch_token_history", []),
        "token_budget": initial_state.get("token_budget", 100000),
        "adaptive_batch_size": initial_state.get("adaptive_batch_size", 3),
        # Phase 4
        "accumulated_track_actions": initial_state.get("accumulated_track_actions", []),
        "generated_tracks": initial_state.get("generated_tracks", []),
        # Phase 5
        "assembled_skill": initial_state.get("assembled_skill", {}),
        "final_validation_errors": initial_state.get("final_validation_errors", []),
        # Backward-compat
        "final_result": initial_state.get("final_result", {}),
        "is_valid": initial_state.get("is_valid", False),
        # Misc
        "messages": initial_state.get("messages", []),
        "thread_id": initial_state.get("thread_id", ""),
    }


def _merge(state: Dict[str, Any], delta: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph `add_messages` reducer behaviour: append, don't overwrite."""
    out = dict(state)
    for k, v in delta.items():
        if k == "messages" and isinstance(v, list):
            out["messages"] = list(state.get("messages", [])) + v
        else:
            out[k] = v
    return out


_MAX_BATCH_INNER_LOOPS = 200
_MAX_TRACK_OUTER_LOOPS = 50


def stream_action_batch_skill_generation(
    initial_state: Dict[str, Any]
) -> Generator[Dict[str, Any], None, None]:
    """Drain the action-batch pipeline and yield `(node, state)` events."""
    state = _build_initial_state(initial_state)

    # ============ Phase 1: skeleton_generator ============
    state = _merge(state, skeleton_generator_node(state))
    yield {"node": "skeleton_generator", "state": state}

    decision = should_continue_to_track_generation(state)
    if decision == "skeleton_failed":
        state = _merge(state, finalize_progressive_node(state))
        yield {"node": "finalize", "state": state}
        yield {"final": True, "result": state}
        return
    # Both `generate_tracks` and `fix_skeleton` go to `batch_planner` per
    # the legacy graph (it deliberately skips the fixer to keep the
    # pipeline forward-only).

    # ============ Phase 2-4: per-track batch_planner -> batch loop -> track_assembler ============
    track_loops = 0
    while True:
        track_loops += 1
        if track_loops > _MAX_TRACK_OUTER_LOOPS:
            logger.warning(
                "Action-batch outer track loop exceeded %s; forcing skill_assembler",
                _MAX_TRACK_OUTER_LOOPS,
            )
            break

        state = _merge(state, batch_planner_node(state))
        yield {"node": "batch_planner", "state": state}

        # Inner batch loop: keep producing batches until the accumulator
        # tells us the current track is done.
        batch_loops = 0
        while True:
            batch_loops += 1
            if batch_loops > _MAX_BATCH_INNER_LOOPS:
                logger.warning(
                    "Action-batch inner batch loop exceeded %s; forcing track_assembler",
                    _MAX_BATCH_INNER_LOOPS,
                )
                break

            state = _merge(state, batch_generator_node(state))
            yield {"node": "batch_generator", "state": state}

            state = _merge(state, batch_accumulator_node(state))
            yield {"node": "batch_accumulator", "state": state}

            if should_continue_batch_loop(state) == "assemble_track":
                break
            # else: "next_batch" -> loop

        state = _merge(state, track_assembler_node(state))
        yield {"node": "track_assembler", "state": state}

        if should_continue_track_loop(state) == "assemble_skill":
            break
        # else: "next_track" -> outer loop continues

    # ============ Phase 5: skill_assembler -> finalize ============
    state = _merge(state, skill_assembler_node(state))
    yield {"node": "skill_assembler", "state": state}

    # `should_finalize_or_fail` returns "finalize" or "failed"; both end up
    # at the same finalize node in the legacy graph.
    _ = should_finalize_or_fail(state)

    state = _merge(state, finalize_progressive_node(state))
    yield {"node": "finalize", "state": state}
    yield {"final": True, "result": state}


def run_action_batch_skill_generation(
    initial_state: Dict[str, Any]
) -> Dict[str, Any]:
    """Synchronous variant: drain the stream and return the final state."""
    final_state: Dict[str, Any] = {}
    for event in stream_action_batch_skill_generation(initial_state):
        if event.get("final"):
            final_state = event["result"]
    return final_state

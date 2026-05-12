"""
Progressive Skill Generation runner — replaces
`graphs/progressive_skill_generation.py`.

Three-phase pipeline:
    Phase 1: skeleton_generator [+ skeleton_fixer loop]
    Phase 2: track_generator -> track_validator -> track_accumulator
             (loop over every track in track_plan)
    Phase 3: skill_assembler -> finalize

The legacy LangGraph topology used `add_conditional_edges` with explicit
route maps. The runner replicates that behaviour with `match` dispatch on
the route function return values.

Notable safety improvement
--------------------------
The legacy graph mapped only three return values for
`should_continue_track_loop` (`next_track`, `assemble`, `fix_track`) but the
function can also return `action_mismatch_interrupt` — which would have
caused a `KeyError` inside LangGraph at runtime. Here we treat
`action_mismatch_interrupt` as a graceful early-`assemble` and append a
warning to `messages` so the user can still see whatever was produced.
"""

import logging
from typing import Any, Dict, Generator

from ..nodes.progressive_skill_nodes import (
    skeleton_generator_node,
    skeleton_fixer_node,
    track_generator_node,
    track_validator_node,
    track_accumulator_node,
    skill_assembler_node,
    finalize_progressive_node,
    should_continue_to_track_generation,
    should_continue_track_loop,
    should_finalize_or_fail,
)

logger = logging.getLogger(__name__)


def _build_initial_state(initial_state: Dict[str, Any]) -> Dict[str, Any]:
    """Mirror `_create_progressive_initial_state` from the legacy graph."""
    return {
        "requirement": initial_state.get("requirement", ""),
        "similar_skills": initial_state.get("similar_skills", []),
        # Phase 1
        "skill_skeleton": initial_state.get("skill_skeleton", {}),
        "skeleton_validation_errors": initial_state.get(
            "skeleton_validation_errors", []
        ),
        "skeleton_retry_count": initial_state.get("skeleton_retry_count", 0),
        "max_skeleton_retries": initial_state.get("max_skeleton_retries", 2),
        # Phase 2
        "track_plan": initial_state.get("track_plan", []),
        "current_track_index": initial_state.get("current_track_index", 0),
        "current_track_data": initial_state.get("current_track_data", {}),
        "generated_tracks": initial_state.get("generated_tracks", []),
        "current_track_errors": initial_state.get("current_track_errors", []),
        "track_retry_count": initial_state.get("track_retry_count", 0),
        "max_track_retries": initial_state.get("max_track_retries", 3),
        "used_action_types": initial_state.get("used_action_types", []),
        # Action mismatch
        "action_mismatch": initial_state.get("action_mismatch", False),
        "missing_action_types": initial_state.get("missing_action_types", []),
        "action_mismatch_details": initial_state.get("action_mismatch_details", ""),
        # Phase 3
        "assembled_skill": initial_state.get("assembled_skill", {}),
        "final_validation_errors": initial_state.get("final_validation_errors", []),
        # Backward-compat fields the legacy nodes also write to.
        "final_result": initial_state.get("final_result", {}),
        "is_valid": initial_state.get("is_valid", False),
        # Messages
        "messages": initial_state.get("messages", []),
    }


def _merge(state: Dict[str, Any], delta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Splice a node's partial return on top of the running state.

    `messages` is appended (LangGraph `add_messages` reducer behaviour).
    """
    out = dict(state)
    for k, v in delta.items():
        if k == "messages" and isinstance(v, list):
            out["messages"] = list(state.get("messages", [])) + v
        else:
            out[k] = v
    return out


# Hard caps, replacing LangGraph's `recursion_limit=100`.
_MAX_SKELETON_ATTEMPTS = 8
_MAX_TRACK_OUTER_LOOPS = 200


def stream_progressive_skill_generation(
    initial_state: Dict[str, Any]
) -> Generator[Dict[str, Any], None, None]:
    """
    Drive the three-phase pipeline and yield `(node, state)` progress events
    plus one terminal `{"final": True, "result": ...}` event.
    """
    state = _build_initial_state(initial_state)

    # ============ Phase 1: skeleton_generator [+ skeleton_fixer loop] ============
    state = _merge(state, skeleton_generator_node(state))
    yield {"node": "skeleton_generator", "state": state}

    skeleton_attempts = 0
    while True:
        decision = should_continue_to_track_generation(state)
        if decision == "generate_tracks":
            break
        if decision == "skeleton_failed":
            # Skip phase 2 entirely; fall through to finalize on an empty
            # `assembled_skill` so the existing failure path emits the right
            # messages.
            state = _merge(state, finalize_progressive_node(state))
            yield {"node": "finalize", "state": state}
            yield {"final": True, "result": state}
            return
        # decision == "fix_skeleton"
        skeleton_attempts += 1
        if skeleton_attempts > _MAX_SKELETON_ATTEMPTS:
            logger.warning(
                "Progressive skeleton fixer exceeded %s attempts; bailing out",
                _MAX_SKELETON_ATTEMPTS,
            )
            state = _merge(state, finalize_progressive_node(state))
            yield {"node": "finalize", "state": state}
            yield {"final": True, "result": state}
            return
        state = _merge(state, skeleton_fixer_node(state))
        yield {"node": "skeleton_fixer", "state": state}

    # ============ Phase 2: per-track generate -> validate -> accumulate loop ============
    track_loops = 0
    while True:
        track_loops += 1
        if track_loops > _MAX_TRACK_OUTER_LOOPS:
            logger.warning(
                "Progressive track loop exceeded %s iterations; forcing assemble",
                _MAX_TRACK_OUTER_LOOPS,
            )
            break

        state = _merge(state, track_generator_node(state))
        yield {"node": "track_generator", "state": state}

        state = _merge(state, track_validator_node(state))
        yield {"node": "track_validator", "state": state}

        state = _merge(state, track_accumulator_node(state))
        yield {"node": "track_accumulator", "state": state}

        decision = should_continue_track_loop(state)
        if decision == "next_track":
            continue
        if decision == "fix_track":
            # Legacy graph mapped fix_track back to `track_generator` (i.e.
            # regenerate the same track). We do exactly the same here.
            continue
        if decision == "action_mismatch_interrupt":
            # Safety improvement vs. the legacy graph (which would KeyError
            # because this branch was not in the conditional map): treat it
            # as an early `assemble` and append a warning message.
            warning = (
                "Action mismatch detected during progressive generation; "
                "assembling with the partial track set."
            )
            logger.warning(warning)
            state = _merge(state, {"messages": [{"type": "warning", "content": warning}]})
            break
        # decision == "assemble"
        break

    # ============ Phase 3: skill_assembler -> finalize ============
    state = _merge(state, skill_assembler_node(state))
    yield {"node": "skill_assembler", "state": state}

    # `should_finalize_or_fail` returns "finalize" or "failed"; both legacy
    # branches go to the same `finalize` node, so we just call it.
    _ = should_finalize_or_fail(state)

    state = _merge(state, finalize_progressive_node(state))
    yield {"node": "finalize", "state": state}
    yield {"final": True, "result": state}


def run_progressive_skill_generation(
    initial_state: Dict[str, Any]
) -> Dict[str, Any]:
    """Synchronous variant: drain the stream and return the final state."""
    final_state: Dict[str, Any] = {}
    for event in stream_progressive_skill_generation(initial_state):
        if event.get("final"):
            final_state = event["result"]
    return final_state

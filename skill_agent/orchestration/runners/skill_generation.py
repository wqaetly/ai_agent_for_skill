"""
Skill Generation runner — replaces `graphs/skill_generation.py`.

Topology (matches the legacy LangGraph):
    retrieve -> generate -> validate -> [fix -> generate -> ...] -> finalize

LangGraph's `add_conditional_edges` is replaced by a plain `while` driven by
the existing `should_continue` route function.
"""

from typing import Any, Dict, Generator

from ..nodes.skill_nodes import (
    retriever_node,
    generator_node,
    validator_node,
    fixer_node,
    finalize_node,
    should_continue,
)


def _build_initial_state(initial_state: Dict[str, Any]) -> Dict[str, Any]:
    """Fill in defaults for every field the legacy nodes expect."""
    return {
        "requirement": initial_state.get("requirement", ""),
        "similar_skills": initial_state.get("similar_skills", []),
        "generated_json": initial_state.get("generated_json", ""),
        "validation_errors": initial_state.get("validation_errors", []),
        "retry_count": initial_state.get("retry_count", 0),
        "max_retries": initial_state.get("max_retries", 3),
        "final_result": initial_state.get("final_result", {}),
        "messages": initial_state.get("messages", []),
    }


def _merge(state: Dict[str, Any], delta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply a node return value to the running state.

    The legacy nodes return *partial* dicts (just the fields they touched);
    we splice them on top of the current state. `messages` is appended
    rather than overwritten to mimic LangGraph's `add_messages` reducer.
    """
    out = dict(state)
    for k, v in delta.items():
        if k == "messages" and isinstance(v, list):
            out["messages"] = list(state.get("messages", [])) + v
        else:
            out[k] = v
    return out


def stream_skill_generation(
    initial_state: Dict[str, Any]
) -> Generator[Dict[str, Any], None, None]:
    """
    Run the legacy retrieve/generate/validate/fix loop and yield progress
    events of the form `{"node": str, "state": dict}` followed by a single
    `{"final": True, "result": dict}` event.
    """
    state = _build_initial_state(initial_state)

    state = _merge(state, retriever_node(state))
    yield {"node": "retrieve", "state": state}

    state = _merge(state, generator_node(state))
    yield {"node": "generate", "state": state}

    # Defensive cap (replaces LangGraph's recursion_limit=50).
    max_iterations = state["max_retries"] * 2 + 4

    for _ in range(max_iterations):
        state = _merge(state, validator_node(state))
        yield {"node": "validate", "state": state}

        decision = should_continue(state)
        if decision == "finalize":
            break

        state = _merge(state, fixer_node(state))
        yield {"node": "fix", "state": state}

        state = _merge(state, generator_node(state))
        yield {"node": "generate", "state": state}

    state = _merge(state, finalize_node(state))
    yield {"node": "finalize", "state": state}
    yield {"final": True, "result": state}


def run_skill_generation(initial_state: Dict[str, Any]) -> Dict[str, Any]:
    """Synchronous variant: drain the stream and return the final state."""
    final_state: Dict[str, Any] = {}
    for event in stream_skill_generation(initial_state):
        if event.get("final"):
            final_state = event["result"]
    return final_state

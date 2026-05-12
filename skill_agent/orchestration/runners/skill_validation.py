"""
Skill Validation runner — replaces `graphs/other_graphs.SkillValidation`.

Replicates the legacy validate -> fix -> validate loop using a plain `while`.
The underlying node logic is reused from `skill_nodes.validator_node` and
`skill_nodes.fixer_node` via tiny adapter shims (the legacy graph wrapped
them in `validation_only_node` / `fix_only_node` to translate field names —
we keep that translation here too).
"""

from typing import Any, Dict, Generator

from ..nodes.skill_nodes import validator_node, fixer_node


def _validate(state: Dict[str, Any]) -> Dict[str, Any]:
    """Adapter: feed `skill_json` into the legacy `validator_node`."""
    temp = {"generated_json": state["skill_json"]}
    out = validator_node(temp)
    return {**state, "validation_errors": out.get("validation_errors", [])}


def _fix(state: Dict[str, Any]) -> Dict[str, Any]:
    """Adapter: route `validator -> fixer` while keeping `skill_json` in sync."""
    temp = {
        "generated_json": state["skill_json"],
        "validation_errors": state.get("validation_errors", []),
        "retry_count": state.get("retry_count", 0),
    }
    out = fixer_node(temp)
    new_skill_json = out.get("generated_json", state["skill_json"])
    return {
        **state,
        "skill_json": new_skill_json,
        "fixed_json": new_skill_json,
        "retry_count": out.get("retry_count", state.get("retry_count", 0) + 1),
    }


def _should_continue(state: Dict[str, Any]) -> str:
    errors = state.get("validation_errors", [])
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)
    if not errors:
        return "end"
    if retry_count >= max_retries:
        return "end"
    return "fix"


def stream_skill_validation(
    initial_state: Dict[str, Any]
) -> Generator[Dict[str, Any], None, None]:
    """
    Validate -> fix -> validate loop. Mirrors the original LangGraph topology
    exactly so callers see identical results.
    """
    state = {
        "skill_json": initial_state["skill_json"],
        "validation_errors": [],
        "fixed_json": "",
        "retry_count": initial_state.get("retry_count", 0),
        "max_retries": initial_state.get("max_retries", 3),
        "final_result": {},
    }

    # Hard cap on iterations as a defensive replacement for LangGraph's
    # `recursion_limit` (which is gone with LangGraph removal).
    max_iterations = state["max_retries"] * 2 + 2

    for _ in range(max_iterations):
        state = _validate(state)
        yield {"node": "validate", "state": state}
        if _should_continue(state) == "end":
            break
        state = _fix(state)
        yield {"node": "fix", "state": state}

    state["final_result"] = {
        "skill_json": state.get("skill_json"),
        "validation_errors": state.get("validation_errors", []),
        "retry_count": state.get("retry_count", 0),
    }
    yield {"final": True, "result": state}


def run_skill_validation(initial_state: Dict[str, Any]) -> Dict[str, Any]:
    """Synchronous variant: drain the stream and return the final state."""
    final_state: Dict[str, Any] = {}
    for event in stream_skill_validation(initial_state):
        if event.get("final"):
            final_state = event["result"]
    return final_state

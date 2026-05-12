"""
Skill Detail runner — replaces `graphs/other_graphs.SkillDetail`.
Single-node wrapper around `tools.rag_tools.get_skill_detail`.
"""

from typing import Any, Dict, Generator

from ..tools.rag_tools import get_skill_detail


def _run_detail(state: Dict[str, Any]) -> Dict[str, Any]:
    skill_id = state["skill_id"]
    result = get_skill_detail.invoke({"skill_id": skill_id})
    return {**state, "result": result}


def run_skill_detail(initial_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Args:
        initial_state: {"skill_id": str}

    Returns:
        Final state with "result" populated.
    """
    return _run_detail(initial_state)


def stream_skill_detail(
    initial_state: Dict[str, Any]
) -> Generator[Dict[str, Any], None, None]:
    yield {"node": "detail", "state": initial_state}
    final_state = _run_detail(initial_state)
    yield {"node": "detail", "state": final_state}
    yield {"final": True, "result": final_state}

"""
Skill Search runner — replaces `graphs/other_graphs.SkillSearch`.

Single-node graph; the runner is therefore a thin wrapper around
`tools.rag_tools.search_skills_semantic` that exposes the same input/output
contract as the legacy graph.
"""

from typing import Any, Dict, Generator

from ..tools.rag_tools import search_skills_semantic


def _run_search(state: Dict[str, Any]) -> Dict[str, Any]:
    """Pure node: execute semantic search and return updated state."""
    query = state["query"]
    top_k = state.get("top_k", 5)
    filters = state.get("filters")
    results = search_skills_semantic.invoke({
        "query": query,
        "top_k": top_k,
        "filters": filters,
    })
    return {**state, "results": results}


def run_skill_search(initial_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Synchronous skill search.

    Args:
        initial_state: {"query": str, "top_k": int (optional), "filters": dict (optional)}

    Returns:
        Final state with "results" populated.
    """
    return _run_search(initial_state)


def stream_skill_search(
    initial_state: Dict[str, Any]
) -> Generator[Dict[str, Any], None, None]:
    """
    Streaming variant: yields one progress event then the final result.
    Mirrors the event protocol used by the complex runners so that the
    OpenAI compat adapter can treat all runners uniformly.
    """
    yield {"node": "search", "state": initial_state}
    final_state = _run_search(initial_state)
    yield {"node": "search", "state": final_state}
    yield {"final": True, "result": final_state}

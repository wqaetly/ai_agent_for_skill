"""
Parameter Inference runner — replaces `graphs/other_graphs.ParameterInference`.
Single-node wrapper around `tools.rag_tools.get_parameter_suggestions`.
"""

from typing import Any, Dict, Generator

from ..tools.rag_tools import get_parameter_suggestions


def _run_infer(state: Dict[str, Any]) -> Dict[str, Any]:
    skill_name = state["skill_name"]
    skill_type = state["skill_type"]
    action_list = state["action_list"]
    result = get_parameter_suggestions.invoke({
        "skill_name": skill_name,
        "skill_type": skill_type,
        "action_list": action_list,
    })
    return {**state, "result": result}


def run_parameter_inference(initial_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Args:
        initial_state: {"skill_name": str, "skill_type": str, "action_list": list[str]}

    Returns:
        Final state with "result" populated.
    """
    return _run_infer(initial_state)


def stream_parameter_inference(
    initial_state: Dict[str, Any]
) -> Generator[Dict[str, Any], None, None]:
    yield {"node": "infer", "state": initial_state}
    final_state = _run_infer(initial_state)
    yield {"node": "infer", "state": final_state}
    yield {"final": True, "result": final_state}

"""
ParameterInferenceComponent — single-node wrapper around
`run_parameter_inference`. Used by the `parameter_inference` flow.

This is the same code path that Unity Editor's "参数推荐" RPC calls,
exposed here so designers can test parameter suggestions interactively
in Lobe Chat.
"""

import json as _json
from typing import Any, List

from lfx.custom.custom_component.component import Component
from lfx.io import HandleInput, MessageTextInput, Output
from lfx.schema.data import Data

from skill_agent.orchestration.runners import run_parameter_inference


class ParameterInferenceComponent(Component):
    display_name: str = "Parameter Inference"
    description: str = (
        "Suggest reasonable parameter values for a skill based on its "
        "name, type and action list."
    )
    icon = "sliders"
    name = "ParameterInferenceComponent"

    inputs = [
        HandleInput(
            name="skill_name",
            display_name="Skill Name",
            input_types=["Message", "str"],
            required=True,
        ),
        MessageTextInput(
            name="skill_type",
            display_name="Skill Type",
            info="e.g. AOE / Single / Buff / Debuff",
            value="AOE",
        ),
        MessageTextInput(
            name="action_list_json",
            display_name="Action List (JSON Array)",
            info='JSON array of action type strings, e.g. ["DamageAction","BuffAction"]',
            value="[]",
        ),
    ]

    outputs = [
        Output(display_name="Suggestions", name="result", method="infer"),
    ]

    def _coerce_action_list(self) -> List[str]:
        raw = (self.action_list_json or "[]").strip()
        try:
            parsed = _json.loads(raw)
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
        except (ValueError, TypeError):
            pass
        return []

    def infer(self) -> Data:
        raw_name: Any = self.skill_name
        skill_name = raw_name.text if hasattr(raw_name, "text") else str(raw_name or "")
        result_state = run_parameter_inference({
            "skill_name": skill_name.strip(),
            "skill_type": (self.skill_type or "AOE").strip(),
            "action_list": self._coerce_action_list(),
        })
        self.status = result_state.get("result")
        return Data(data=result_state)

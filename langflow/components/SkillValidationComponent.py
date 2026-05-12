"""
SkillValidationComponent — wraps the `validate -> fix -> validate` loop
exposed by `run_skill_validation`. Used by the `skill_validation` flow.

The component takes a JSON string (the skill payload to validate),
optionally bumps `max_retries`, and emits a final state Data object
containing both the (possibly fixed) `skill_json` and any residual
`validation_errors`.
"""

from typing import Any

from lfx.custom.custom_component.component import Component
from lfx.io import HandleInput, IntInput, Output
from lfx.schema.data import Data

from skill_agent.orchestration.runners import run_skill_validation


class SkillValidationComponent(Component):
    display_name: str = "Skill Validation"
    description: str = (
        "Validate a skill JSON and (optionally) auto-fix it. Wraps the "
        "validate -> fix loop from the original LangGraph implementation."
    )
    icon = "shield-check"
    name = "SkillValidationComponent"

    inputs = [
        HandleInput(
            name="skill_json",
            display_name="Skill JSON",
            info="Skill payload to validate (Message or str).",
            input_types=["Message", "str"],
            required=True,
        ),
        IntInput(
            name="max_retries",
            display_name="Max Fix Retries",
            value=3,
            advanced=True,
        ),
    ]

    outputs = [
        Output(display_name="Validation Result", name="result", method="run_validation"),
    ]

    def run_validation(self) -> Data:
        raw: Any = self.skill_json
        skill_json_text = raw.text if hasattr(raw, "text") else str(raw or "")
        result_state = run_skill_validation({
            "skill_json": skill_json_text,
            "max_retries": int(self.max_retries or 3),
        })
        self.status = {
            "errors": result_state.get("validation_errors", []),
            "retry_count": result_state.get("retry_count", 0),
        }
        return Data(data=result_state)

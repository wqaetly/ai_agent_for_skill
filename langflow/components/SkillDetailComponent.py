"""
SkillDetailComponent — single-node wrapper around `run_skill_detail`.
Used by the `skill_detail` flow.
"""

from typing import Any

from lfx.custom.custom_component.component import Component
from lfx.io import HandleInput, Output
from lfx.schema.data import Data

from skill_agent.orchestration.runners import run_skill_detail


class SkillDetailComponent(Component):
    display_name: str = "Skill Detail"
    description: str = (
        "Look up the full configuration of a skill by its id "
        "(via the existing RAG engine)."
    )
    icon = "file-text"
    name = "SkillDetailComponent"

    inputs = [
        HandleInput(
            name="skill_id",
            display_name="Skill ID",
            info="Skill id to fetch (Message or str).",
            input_types=["Message", "str"],
            required=True,
        ),
    ]

    outputs = [
        Output(display_name="Detail", name="detail", method="fetch_detail"),
    ]

    def fetch_detail(self) -> Data:
        raw: Any = self.skill_id
        skill_id = raw.text if hasattr(raw, "text") else str(raw or "")
        result_state = run_skill_detail({"skill_id": skill_id.strip()})
        self.status = result_state.get("result")
        return Data(data=result_state)

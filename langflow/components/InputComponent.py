"""
InputComponent — accepts a free-form requirement string from the Langflow
playground and forwards it as the canonical `requirement` field every
runner consumes.

This component is intentionally minimal so that flow JSON files stay short
and that swapping the input source (e.g. for a future "messages history"
input) only touches this single file.
"""

from lfx.custom.custom_component.component import Component
from lfx.io import MessageTextInput, Output
from lfx.schema.message import Message


class InputComponent(Component):
    display_name: str = "Skill Requirement Input"
    description: str = (
        "Accepts a natural-language skill requirement and emits it as the "
        "shared `requirement` field consumed by every Skill Agent runner."
    )
    icon = "type"
    name = "InputComponent"

    inputs = [
        MessageTextInput(
            name="requirement",
            display_name="Requirement",
            info="Natural language description of the skill to build or query.",
            required=True,
        ),
    ]

    outputs = [
        Output(display_name="Requirement", name="requirement", method="build_requirement"),
    ]

    def build_requirement(self) -> Message:
        text = (self.requirement or "").strip()
        message = Message(text=text)
        self.status = text
        return message

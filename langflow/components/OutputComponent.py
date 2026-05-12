"""
OutputComponent — receives the final state dict produced by any runner and
emits it as a Markdown-friendly `Message` so the Lobe Chat front-end can
render syntax-highlighted JSON with one-click copy.
"""

import json
from typing import Any

from lfx.custom.custom_component.component import Component
from lfx.io import HandleInput, Output
from lfx.schema.message import Message


class OutputComponent(Component):
    display_name: str = "Skill Result Output"
    description: str = (
        "Renders a runner's final state dict as a fenced JSON Markdown "
        "block. Use this as the terminal node of every flow."
    )
    icon = "log-out"
    name = "OutputComponent"

    inputs = [
        HandleInput(
            name="result",
            display_name="Final Result",
            info="The final state dict produced by an upstream runner component.",
            input_types=["Data", "Message", "dict"],
            required=True,
        ),
    ]

    outputs = [
        Output(display_name="Markdown", name="markdown", method="format_result"),
    ]

    def format_result(self) -> Message:
        payload: Any = self.result
        # Unwrap the most common Langflow carrier types so the user can wire
        # an `OutputComponent` after either a raw dict, a `Data` object, or
        # an already-built `Message`.
        if hasattr(payload, "data") and isinstance(getattr(payload, "data"), dict):
            payload = payload.data
        elif hasattr(payload, "text"):
            try:
                payload = json.loads(payload.text)
            except (ValueError, TypeError):
                payload = {"text": payload.text}

        if not isinstance(payload, (dict, list)):
            payload = {"value": str(payload)}

        # Strip the noisy `messages` field by default — the Langflow
        # playground will still surface progress through streamed events,
        # and the OpenAI compat adapter has its own translation path.
        if isinstance(payload, dict) and "messages" in payload:
            payload = {k: v for k, v in payload.items() if k != "messages"}

        try:
            body = json.dumps(payload, ensure_ascii=False, indent=2)
        except (TypeError, ValueError):
            body = str(payload)

        rendered = f"```json\n{body}\n```"
        self.status = rendered
        return Message(text=rendered)

"""
ProgressiveGeneratorComponent — coarse-grained wrapper around
`stream_progressive_skill_generation`. Used by the
`progressive_skill_generation` flow.

Inside this single Langflow node we still drive the three legacy phases
(skeleton -> per-track loop -> assemble) and surface per-stage progress
through `self.status`. The OpenAI compat adapter is responsible for
forwarding those status updates to Lobe Chat as `delta.reasoning_content`.
"""

from typing import Any, List

from lfx.custom.custom_component.component import Component
from lfx.io import HandleInput, IntInput, Output
from lfx.schema.data import Data

from skill_agent.orchestration.runners import stream_progressive_skill_generation


class ProgressiveGeneratorComponent(Component):
    display_name: str = "Progressive Skill Generator"
    description: str = (
        "Three-phase progressive skill generation (skeleton → per-track → "
        "assemble). Streams per-node progress to the Playground."
    )
    icon = "layers"
    name = "ProgressiveGeneratorComponent"

    inputs = [
        HandleInput(
            name="requirement",
            display_name="Requirement",
            input_types=["Message", "str"],
            required=True,
        ),
        IntInput(
            name="max_track_retries",
            display_name="Max Track Retries",
            value=3,
            advanced=True,
        ),
        IntInput(
            name="max_skeleton_retries",
            display_name="Max Skeleton Retries",
            value=2,
            advanced=True,
        ),
    ]

    outputs = [
        Output(display_name="Final Skill", name="result", method="generate"),
    ]

    def _resolve_requirement(self) -> str:
        raw: Any = self.requirement
        return raw.text if hasattr(raw, "text") else str(raw or "")

    def generate(self) -> Data:
        initial_state = {
            "requirement": self._resolve_requirement().strip(),
            "max_track_retries": int(self.max_track_retries or 3),
            "max_skeleton_retries": int(self.max_skeleton_retries or 2),
        }

        progress_log: List[str] = []
        final_state: dict = {}
        for event in stream_progressive_skill_generation(initial_state):
            if event.get("final"):
                final_state = event["result"]
                continue
            node = event.get("node", "?")
            state = event.get("state", {})
            track_index = state.get("current_track_index")
            track_total = len(state.get("track_plan") or [])
            extra = ""
            if track_total:
                extra = f" (track {track_index}/{track_total})"
            progress_log.append(f"[{node}]{extra}")
            self.status = "\n".join(progress_log[-12:])

        self.status = {
            "node": "finalize",
            "is_valid": bool(final_state.get("is_valid")),
            "track_count": len(final_state.get("generated_tracks") or []),
        }
        return Data(data=final_state)

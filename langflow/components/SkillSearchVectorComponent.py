"""
SkillSearchVectorComponent — second half of the细粒度 `skill_search` flow.

Consumes the prepared payload from `SkillSearchEmbeddingComponent` and
calls `skill_agent.orchestration.runners.run_skill_search` (which in turn
hits the existing RAG engine + LanceDB vector store). The result is
exposed both as a Markdown table (for Lobe Chat) and as a raw `Data`
object (so other flows can chain further processing).
"""

from typing import Any

from lfx.custom.custom_component.component import Component
from lfx.io import HandleInput, Output
from lfx.schema.data import Data
from lfx.schema.message import Message

from skill_agent.orchestration.runners import run_skill_search


def _to_markdown_table(results: Any) -> str:
    """Render the results list as a markdown table; degrade to JSON if the
    shape is not a list-of-dicts."""
    import json as _json

    if not isinstance(results, list) or not results:
        return "_No matching skills found._"

    if not isinstance(results[0], dict):
        return f"```json\n{_json.dumps(results, ensure_ascii=False, indent=2)}\n```"

    headers = list(results[0].keys())
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in results:
        cells = []
        for h in headers:
            v = row.get(h, "")
            if isinstance(v, (dict, list)):
                v = _json.dumps(v, ensure_ascii=False)
            cells.append(str(v).replace("\n", " ").replace("|", "\\|"))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


class SkillSearchVectorComponent(Component):
    display_name: str = "Skill Search · Vector"
    description: str = (
        "Run semantic search against the LanceDB-backed RAG engine and "
        "return both a Markdown table and a structured Data object."
    )
    icon = "search"
    name = "SkillSearchVectorComponent"

    inputs = [
        HandleInput(
            name="payload",
            display_name="Search Payload",
            info="Structured payload from SkillSearchEmbeddingComponent.",
            input_types=["Data", "dict"],
            required=True,
        ),
    ]

    outputs = [
        Output(display_name="Markdown", name="markdown", method="run_search_markdown"),
        Output(display_name="Raw Data", name="data", method="run_search_data"),
    ]

    def _resolve_payload(self) -> dict:
        raw = self.payload
        if hasattr(raw, "data") and isinstance(getattr(raw, "data"), dict):
            return dict(raw.data)
        if isinstance(raw, dict):
            return dict(raw)
        return {"query": str(raw or ""), "top_k": 5, "filters": None}

    def _run(self) -> dict:
        state = self._resolve_payload()
        return run_skill_search(state)

    def run_search_markdown(self) -> Message:
        result_state = self._run()
        markdown = _to_markdown_table(result_state.get("results"))
        self.status = markdown
        return Message(text=markdown)

    def run_search_data(self) -> Data:
        result_state = self._run()
        return Data(data=result_state)

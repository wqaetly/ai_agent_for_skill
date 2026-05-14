"""Hello-Lobe smoke-test flow.

Purpose
-------
This is the very first flow we ship after switching the front-end from
Langflow Playground to Lobe Chat. It is intentionally a one-prompt
echo-style graph so we can verify the whole bring-up path end-to-end:

    Lobe Chat
      -> OpenAI Compat Adapter (skill_agent/openai_compat) on :2024
        -> Langflow Run API on :7860 (wqaetly/langflow @ dev)
          -> ChatInput -> Prompt -> OpenAIModelComponent (DeepSeek) -> ChatOutput

The flow is **not** part of the eight production flows; it never touches
the RAG engine and never imports `skill_agent.core.*`. It exists purely
so a developer can boot the stack and prove "Lobe Chat -> Langflow -> LLM"
is wired up before touching real flows.

Authoring rules (per langflow fork's LOCAL_DEV_GUIDELINES.md, section 2)
----------------------------------------------------------------------
- This flow's source of truth is THIS Python file. The sibling
  `hello_lobe.flow.json` is a **build artifact** produced by
  `Graph.dump(...)`. Do not hand-edit the JSON.
- Regenerate the JSON whenever you edit this file:

      # 1. Bring Langflow up once with LFX_DEV=1 so component schemas are
      #    reflected from source (otherwise dump() may emit stale fields).
      # 2. With the fork's venv active, run from repo root:

      .\\external\\langflow\\.venv\\Scripts\\python.exe ^
          langflow\\flows\\hello_lobe.py

  The script writes `langflow/flows/hello_lobe.flow.json` next to itself.
  Commit the .py and the .json together.
- Both `langflow/scripts/upload_flows.py` and Langflow's startup loader
  pick up `*.json` under `langflow/flows/`, so once the JSON is on disk
  the next `langflow run` (or `python upload_flows.py`) makes the flow
  reachable as flow-name `hello_lobe` on `POST /api/v1/run/hello_lobe`.

DeepSeek wiring
---------------
We reuse `OpenAIModelComponent` (NOT a custom component) because:
- The fork's OpenAI node is already DeepSeek-compatible: `openai_api_base`
  is a plain `StrInput`, `model_name` is a `combobox` (free-form), and
  `api_key` is a `SecretStrInput`. Langflow auto-resolves the secret by
  looking up an environment variable of the same name when the value is
  a bare identifier, which is exactly what `run_local.bat` feeds via
  `--env-file skill_agent/.env`.
- Keeping the LLM call on a stock node means this smoke test does not
  depend on any of our `langflow/components/*.py` work — if it breaks,
  we know the issue is in the bring-up path, not in our custom code.
"""

from __future__ import annotations

import json
from pathlib import Path

# Imports follow the same module layout as
# external/langflow/src/backend/base/langflow/initial_setup/starter_projects/basic_prompting.py
# (the canonical example endorsed by LOCAL_DEV_GUIDELINES.md section 2).
from lfx.components.input_output import ChatInput, ChatOutput
from lfx.components.models_and_agents import PromptComponent
from lfx.components.openai.openai_chat_model import OpenAIModelComponent
from lfx.graph import Graph


# Default prompt is intentionally trivial — we want the LLM round-trip,
# not prompt-engineering, to be the variable under test.
_DEFAULT_TEMPLATE = (
    "You are a friendly bring-up assistant. Reply in one short paragraph "
    "and confirm the request reached you.\n\n"
    "User: {user_input}\n\n"
    "Assistant:"
)

# DeepSeek defaults. Both values are intentionally string identifiers, not
# raw secrets — Langflow resolves `DEEPSEEK_API_KEY` against the env that
# `run_local.bat` injects via `--env-file skill_agent/.env`.
_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
_DEEPSEEK_MODEL_NAME = "deepseek-chat"
_DEEPSEEK_API_KEY_ENV = "DEEPSEEK_API_KEY"


def hello_lobe_graph(template: str | None = None) -> Graph:
    """Assemble the smoke-test graph.

    Mirrors `basic_prompting_graph` but points the OpenAI node at
    DeepSeek so we don't burn an OpenAI quota on a connectivity check.
    """
    chat_input = ChatInput()

    prompt_component = PromptComponent()
    prompt_component.set(
        template=template or _DEFAULT_TEMPLATE,
        user_input=chat_input.message_response,
    )

    llm_component = OpenAIModelComponent()
    llm_component.set(
        input_value=prompt_component.build_prompt,
        model_name=_DEEPSEEK_MODEL_NAME,
        openai_api_base=_DEEPSEEK_BASE_URL,
        api_key=_DEEPSEEK_API_KEY_ENV,
        # Keep the smoke test deterministic-ish; a non-zero temperature
        # also avoids confusing reasoning-model code paths.
        temperature=0.2,
    )

    chat_output = ChatOutput()
    chat_output.set(input_value=llm_component.text_response)

    return Graph(start=chat_input, end=chat_output)


def main() -> None:
    """Dump the graph to `hello_lobe.flow.json` next to this file."""
    graph = hello_lobe_graph()
    flow_dict = graph.dump(
        name="hello_lobe",
        description=(
            "Bring-up smoke test: ChatInput -> Prompt -> DeepSeek -> "
            "ChatOutput. Use OpenAI model id `hello-lobe` in Lobe Chat "
            "to hit this flow via the OpenAI Compat adapter."
        ),
    )

    out_path = Path(__file__).resolve().parent / "hello_lobe.flow.json"
    out_path.write_text(
        json.dumps(flow_dict, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()

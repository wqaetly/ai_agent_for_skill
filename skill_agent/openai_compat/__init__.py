"""
OpenAI Chat Completions compatible adapter for Skill Agent.

This package exposes the FastAPI server that:
  - Exposes /v1/models and /v1/chat/completions on port 2024.
  - Translates OpenAI Chat Completions requests into Langflow Run API calls.
  - Streams Langflow events back to the client as OpenAI SSE chunks
    (thinking -> delta.reasoning_content, final answer -> delta.content).

Implementation details are filled in by Task 5 of the migration plan
(see .codebuddy/plan/langflow_lobechat_migration/task-item.md).
"""

__all__ = []

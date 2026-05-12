"""
Pydantic schemas for the OpenAI Chat Completions compatibility adapter.

Only the subset of the OpenAI spec consumed by Lobe Chat is modelled here
(plus the small DeepSeek-Reasoner extension `reasoning_content` we re-emit
on the streaming path).
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Models endpoint
# ---------------------------------------------------------------------------

class ModelInfo(BaseModel):
    """Single entry of the `/v1/models` response."""

    id: str
    object: Literal["model"] = "model"
    created: int = Field(default_factory=lambda: int(time.time()))
    owned_by: str = "skill-agent"


class ModelsResponse(BaseModel):
    object: Literal["list"] = "list"
    data: List[ModelInfo]


# ---------------------------------------------------------------------------
# Chat completions request
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    """Subset of OpenAI message: text-only content is enough for our use-case."""
    model_config = ConfigDict(extra="allow")

    role: Literal["system", "user", "assistant", "tool"]
    # Lobe Chat sometimes sends a multipart `content` (list of parts); we
    # keep both shapes and flatten when extracting the requirement text.
    content: Union[str, List[Dict[str, Any]], None] = None
    name: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    model: str
    messages: List[ChatMessage]
    stream: bool = False
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    user: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def last_user_text(self) -> str:
        """Extract the most recent user message as plain text."""
        for msg in reversed(self.messages):
            if msg.role != "user":
                continue
            content = msg.content
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                # OpenAI multipart format: pull every `text` part out.
                parts: List[str] = []
                for p in content:
                    if isinstance(p, dict) and p.get("type") == "text":
                        parts.append(str(p.get("text", "")))
                return "\n".join(parts)
        return ""


# ---------------------------------------------------------------------------
# Chat completions response (non-streaming)
# ---------------------------------------------------------------------------

class ChatChoiceMessage(BaseModel):
    role: Literal["assistant"] = "assistant"
    content: Optional[str] = None
    reasoning_content: Optional[str] = None


class ChatChoice(BaseModel):
    index: int = 0
    message: ChatChoiceMessage
    finish_reason: Literal["stop", "length", "error"] = "stop"


class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex}")
    object: Literal["chat.completion"] = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[ChatChoice]
    usage: Usage = Field(default_factory=Usage)


# ---------------------------------------------------------------------------
# Chat completions streaming chunks
# ---------------------------------------------------------------------------

class ChatChunkDelta(BaseModel):
    """A streaming delta. Mirrors OpenAI's spec plus DeepSeek-Reasoner's
    `reasoning_content` field which Lobe Chat already understands."""

    model_config = ConfigDict(extra="allow")

    role: Optional[Literal["assistant"]] = None
    content: Optional[str] = None
    reasoning_content: Optional[str] = None


class ChatChunkChoice(BaseModel):
    index: int = 0
    delta: ChatChunkDelta
    finish_reason: Optional[Literal["stop", "length", "error"]] = None


class ChatCompletionChunk(BaseModel):
    id: str
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[ChatChunkChoice]


# ---------------------------------------------------------------------------
# OpenAI-style error envelope
# ---------------------------------------------------------------------------

class APIError(BaseModel):
    message: str
    type: str = "skill_agent_error"
    code: Optional[str] = None


class APIErrorResponse(BaseModel):
    error: APIError

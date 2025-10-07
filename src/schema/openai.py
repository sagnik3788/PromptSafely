from pydantic import BaseModel, Field, StringConstraints
from typing import Annotated, List, Optional


# ---- Models ------------------------------------------------------------------


class ChatMessage(BaseModel):
    """Represents a single message in a chat conversation."""

    # role for input to OpenAI (must be one of: user, system, assistant, tool)
    role: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True, pattern=r"^(user|system|assistant|tool)$"
        ),
    ]

    # content should be 1–9000 length
    content: Annotated[str, StringConstraints(min_length=1, max_length=9000)]


class ChatRequest(BaseModel):
    """Request payload for a chat completion API."""

    # model name must be 2–128 characters
    # using Annotated instead of constr (deprecated in Pydantic v3)
    # https://docs.pydantic.dev/latest/api/types/#pydantic.types.constr
    model: Annotated[str, StringConstraints(min_length=2, max_length=128)]

    # list of messages (1–20 items)
    messages: Annotated[List[ChatMessage], Field(min_length=1, max_length=20)]

    # max_tokens is optional, 1–8192
    max_tokens: Optional[int] = Field(None, ge=1, le=8192)

    # hardcoded to 1.0 as most tasks will be normal chat
    temperature: Optional[float] = Field(1.0, ge=0, le=2)

    # for now False; later may support streaming partial responses
    stream: bool = False


class ChatResponse(BaseModel):
    """Response payload from a chat completion API."""

    id: str
    object: str = "chat.completion"
    created: int
    model: str

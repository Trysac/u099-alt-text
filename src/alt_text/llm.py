"""LLM ports and deterministic test doubles for alt text generation."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Literal, Protocol, TypedDict

from .errors import AltTextError


class Message(TypedDict):
    """One chat message."""

    role: Literal["system", "user", "assistant"]
    content: str


class LLMPort(Protocol):
    """A text-only chat model."""

    def complete(self, messages: Sequence[Message], *, max_tokens: int) -> str:
        """Return the reply to ``messages``; errors propagate to the caller unchanged."""
        ...


class VisionLLMPort(LLMPort, Protocol):
    """A chat model that can also look at one image."""

    def complete_with_image(
        self,
        messages: Sequence[Message],
        *,
        image: bytes,
        mime_type: str,
        max_tokens: int,
    ) -> str:
        """Return the reply to ``messages`` about ``image``."""
        ...


class RecordingExhaustedError(AltTextError):
    """Raised by :class:`RecordedLLM` when it has no recorded reply left."""

    def __init__(self) -> None:
        """Create the error with the ``invalid_reply`` code."""
        super().__init__("invalid_reply", "no recorded reply is left")


@dataclass(frozen=True)
class RecordedCall:
    """A snapshot of one call made to a :class:`RecordedLLM`."""

    messages: tuple[Message, ...]
    max_tokens: int
    image_size: int | None
    mime_type: str | None


def _snapshot(messages: Sequence[Message]) -> tuple[Message, ...]:
    return tuple(Message(role=m["role"], content=m["content"]) for m in messages)


class RecordedLLM:
    """Replays fixed replies in order and records every served call in ``calls``."""

    def __init__(self, replies: Sequence[str]) -> None:
        """Store ``replies``; ``calls`` starts empty."""
        self._replies = tuple(replies)
        self._position = 0
        self.calls: list[RecordedCall] = []

    def complete(self, messages: Sequence[Message], *, max_tokens: int) -> str:
        """Return the next recorded reply."""
        return self._next(messages, max_tokens, None, None)

    def complete_with_image(
        self,
        messages: Sequence[Message],
        *,
        image: bytes,
        mime_type: str,
        max_tokens: int,
    ) -> str:
        """Return the next recorded reply; only the image size is recorded."""
        return self._next(messages, max_tokens, len(image), mime_type)

    def _next(
        self,
        messages: Sequence[Message],
        max_tokens: int,
        image_size: int | None,
        mime_type: str | None,
    ) -> str:
        if self._position >= len(self._replies):
            raise RecordingExhaustedError()
        reply = self._replies[self._position]
        self._position += 1
        call = RecordedCall(
            messages=_snapshot(messages),
            max_tokens=max_tokens,
            image_size=image_size,
            mime_type=mime_type,
        )
        self.calls.append(call)
        return reply


class FakeLLM:
    """Answers every call with a function of the messages."""

    def __init__(self, fn: Callable[[Sequence[Message]], str]) -> None:
        """Store the reply function."""
        self._fn = fn

    def complete(self, messages: Sequence[Message], *, max_tokens: int) -> str:
        """Return ``fn(messages)``."""
        return self._fn(messages)

    def complete_with_image(
        self,
        messages: Sequence[Message],
        *,
        image: bytes,
        mime_type: str,
        max_tokens: int,
    ) -> str:
        """Return ``fn(messages)``; the image is ignored."""
        return self._fn(messages)

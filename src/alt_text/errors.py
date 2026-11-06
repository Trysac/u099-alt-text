"""Typed errors raised by the alt_text package."""

from __future__ import annotations

from typing import Literal

ErrorCode = Literal["unsupported_image", "too_large", "invalid_reply"]

_MAX_MESSAGE_CHARS = 200


class AltTextError(Exception):
    """Base class of every error raised on purpose by this library.

    Attributes:
        code: Stable machine-readable error code.
    """

    def __init__(self, code: ErrorCode, message: str) -> None:
        """Create an error; the message is cut to 200 characters."""
        super().__init__(message[:_MAX_MESSAGE_CHARS])
        self.code: ErrorCode = code

"""Lint alt text against WCAG 2.2 SC 1.1.1, the WAI alt decision tree and WHATWG rules.

The 150 character default is a screen-reader convention, not a WCAG requirement.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, get_args

from .errors import AltTextError

Purpose = Literal["informative", "functional", "decorative", "complex"]
PURPOSES: tuple[str, ...] = get_args(Purpose)

DEFAULT_MAX_CHARS = 150
MAX_ALT_INPUT_CHARS = 100_000

_MESSAGES = {
    "ALT001": "Alt text starts with a redundant prefix such as 'image of' or 'photo of'.",
    "ALT002": "Alt text is longer than the configured maximum number of characters.",
    "ALT003": "Alt text looks like a file name or a camera-generated name.",
    "ALT004": "Alt text is empty but the image is not decorative.",
    "ALT005": "Alt text is not empty but the image is decorative.",
    "ALT006": "Alt text is a placeholder word that describes nothing.",
    "ALT007": "Alt text contains a URL.",
    "ALT008": "Alt text of a functional image says 'click here', 'link' or 'button'.",
}

_REDUNDANT_PREFIX = re.compile(r"(?:image|picture|photo|graphic)\s+of\b", re.IGNORECASE)
_IMAGE_EXTENSION = re.compile(r"\.(?:png|jpe?g|gif|webp|svg|bmp|tiff?|avif)$", re.IGNORECASE)
_CAMERA_PATTERN = r"(?<![a-z0-9])(?:img|dsc|dscn|dscf|pxl|mvimg)[_-]?\d{4,}(?![a-z0-9])"
_CAMERA_NAME = re.compile(_CAMERA_PATTERN, re.IGNORECASE)
_URL = re.compile(r"(?<![a-z0-9])(?:https?://|www\.)", re.IGNORECASE)
_CLICK_WORDS = re.compile(r"\b(?:click\s+here|link|button)\b", re.IGNORECASE)
_PLACEHOLDERS = frozenset({"image", "photo", "picture", "logo", "untitled", "spacer"})
_TRAILING = " \t\r\n.!?,;:\u2026"


@dataclass(frozen=True)
class AltIssue:
    """One problem found in an alt text.

    Attributes:
        code: Stable rule code, ``ALT001`` to ``ALT008``.
        message: Human-readable explanation of the rule.
    """

    code: str
    message: str


def _issue(code: str) -> AltIssue:
    return AltIssue(code=code, message=_MESSAGES[code])


def _is_filename_like(text: str, filename: str | None) -> bool:
    if filename:
        name = filename.replace("\\", "/").rsplit("/", 1)[-1].strip().casefold()
        if text.casefold() == name:
            return True
    return bool(_IMAGE_EXTENSION.search(text) or _CAMERA_NAME.search(text))


def check_alt(alt: str, purpose: str, filename: str | None, max_chars: int) -> list[AltIssue]:
    """Lint ``alt`` without validating arguments or input size; callers bound the input."""
    text = alt.strip()
    if purpose == "decorative":
        return [_issue("ALT005")] if text else []
    if not text:
        return [_issue("ALT004")]
    codes: list[str] = []
    if _REDUNDANT_PREFIX.match(text):
        codes.append("ALT001")
    if len(text) > max_chars:
        codes.append("ALT002")
    if _is_filename_like(text, filename):
        codes.append("ALT003")
    if text.rstrip(_TRAILING).casefold() in _PLACEHOLDERS:
        codes.append("ALT006")
    if _URL.search(text):
        codes.append("ALT007")
    if purpose == "functional" and _CLICK_WORDS.search(text):
        codes.append("ALT008")
    return [_issue(code) for code in codes]


def lint_alt_text(
    alt: str,
    *,
    purpose: Purpose = "informative",
    filename: str | None = None,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> list[AltIssue]:
    """Lint one alt text and return the issues found, ordered by code.

    Phrases are matched casefolded at word boundaries. A decorative image only gets
    ``ALT005`` when its alt text is not empty; an empty alt text of any other purpose
    only gets ``ALT004``.

    Args:
        alt: The alt text to check (at most 100 000 characters).
        purpose: ``informative``, ``functional``, ``decorative`` or ``complex``.
        filename: Optional file name of the image, used for the ``ALT003`` check.
        max_chars: Length limit for ``ALT002``.

    Raises:
        AltTextError: ``too_large`` if ``alt`` exceeds the input size limit.
        TypeError: if ``alt`` is not a string.
        ValueError: if ``purpose`` or ``max_chars`` is invalid.
    """
    if not isinstance(alt, str):
        raise TypeError("alt must be a string")
    if purpose not in PURPOSES:
        raise ValueError("purpose must be informative, functional, decorative or complex")
    if max_chars < 1:
        raise ValueError("max_chars must be at least 1")
    if len(alt) > MAX_ALT_INPUT_CHARS:
        raise AltTextError("too_large", "alt text exceeds the input size limit")
    return check_alt(alt, purpose, filename, max_chars)

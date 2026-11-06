"""Scan HTML for ``<img>`` elements and lint their alt attributes."""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser

from .errors import AltTextError
from .lint import DEFAULT_MAX_CHARS, AltIssue, Purpose, check_alt

DEFAULT_MAX_HTML_CHARS = 5_000_000
MAX_IMAGES = 10_000

_DECORATIVE_ROLES = frozenset({"presentation", "none"})


@dataclass(frozen=True)
class ImgFinding:
    """One ``<img>`` element found in an HTML document.

    Attributes:
        line: 1-based line of the start tag.
        src: Value of the ``src`` attribute, or ``None`` if absent.
        alt: Value of the ``alt`` attribute, or ``None`` if absent.
        missing_alt: ``alt`` is absent and no presentation role excuses it.
        decorative: ``alt`` is empty or the role is ``presentation`` or ``none``.
        issues: Lint issues found for this image.
    """

    line: int
    src: str | None
    alt: str | None
    missing_alt: bool
    decorative: bool
    issues: tuple[AltIssue, ...]


def _filename_from_src(src: str | None) -> str | None:
    if src is None or src.strip().casefold().startswith("data:"):
        return None
    path = src.strip().split("#", 1)[0].split("?", 1)[0]
    return path.rsplit("/", 1)[-1] or None


def _build_finding(line: int, attrs: list[tuple[str, str | None]]) -> ImgFinding:
    values: dict[str, str] = {}
    for name, value in attrs:
        values.setdefault(name, value or "")
    alt = values.get("alt")
    src = values.get("src")
    roles = values.get("role", "").split()
    role_decorative = bool(roles) and roles[0].casefold() in _DECORATIVE_ROLES
    decorative = (alt is not None and not alt.strip()) or role_decorative
    missing_alt = alt is None and not role_decorative
    purpose: Purpose = "decorative" if decorative else "informative"
    issues = check_alt(alt or "", purpose, _filename_from_src(src), DEFAULT_MAX_CHARS)
    return ImgFinding(
        line=line,
        src=src,
        alt=alt,
        missing_alt=missing_alt,
        decorative=decorative,
        issues=tuple(issues),
    )


class _ImgCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.findings: list[ImgFinding] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "img":
            return
        if len(self.findings) >= MAX_IMAGES:
            raise AltTextError("too_large", "document has too many images")
        self.findings.append(_build_finding(self.getpos()[0], attrs))


def scan_html(html: str, *, max_chars: int = DEFAULT_MAX_HTML_CHARS) -> list[ImgFinding]:
    """Find every ``<img>`` in ``html`` and lint its alt attribute.

    Images are never fetched. An image counts as decorative when its alt attribute is empty
    or its role is ``presentation`` or ``none``; it has a missing alt when the attribute is
    absent and no such role is present.

    Args:
        html: The document text.
        max_chars: Maximum accepted document length.

    Raises:
        AltTextError: ``too_large`` if the document is longer than ``max_chars`` or holds
            more than 10 000 images.
        TypeError: if ``html`` is not a string.
        ValueError: if ``max_chars`` is smaller than 1.
    """
    if not isinstance(html, str):
        raise TypeError("html must be a string")
    if max_chars < 1:
        raise ValueError("max_chars must be at least 1")
    if len(html) > max_chars:
        raise AltTextError("too_large", "document exceeds the input size limit")
    parser = _ImgCollector()
    parser.feed(html)
    parser.close()
    return parser.findings

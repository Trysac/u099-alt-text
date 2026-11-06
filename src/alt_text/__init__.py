"""Lint and generate image alt text following WCAG 2.2 and the WAI alt decision tree."""

from __future__ import annotations

from .errors import AltTextError
from .generate import AltTextResult, generate_alt_text
from .html_scan import ImgFinding, scan_html
from .images import ImageInfo, read_image_info
from .lint import AltIssue, Purpose, lint_alt_text

__all__ = [
    "AltIssue",
    "AltTextError",
    "AltTextResult",
    "ImageInfo",
    "ImgFinding",
    "Purpose",
    "__version__",
    "generate_alt_text",
    "lint_alt_text",
    "read_image_info",
    "scan_html",
]

__version__ = "0.1.0"

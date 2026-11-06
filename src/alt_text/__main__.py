"""Command line interface, run with ``python -m alt_text``.

Exit codes: 0 no findings, 1 findings, 2 usage, I/O or parse error.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

from .errors import AltTextError
from .generate import DEFAULT_MAX_IMAGE_BYTES, generate_alt_text
from .html_scan import ImgFinding, scan_html
from .lint import PURPOSES, lint_alt_text
from .llm import RecordedLLM

MAX_FILE_BYTES = 20_000_000
MAX_REPLIES_FILE_BYTES = 1_000_000

_REPLIES_ERROR = "replies file must be a JSON list of strings"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="alt-text", description="Lint and generate alt text.")
    sub = parser.add_subparsers(dest="command", required=True)
    lint = sub.add_parser("lint", help="lint every img element of an HTML file")
    lint.add_argument("file")
    lint.add_argument("--format", choices=("text", "json"), default="text")
    check = sub.add_parser("check", help="lint one alt text")
    check.add_argument("text")
    check.add_argument("--purpose", choices=PURPOSES, default="informative")
    check.add_argument("--filename")
    generate = sub.add_parser("generate", help="generate alt text from recorded model replies")
    generate.add_argument("image")
    generate.add_argument("--recorded", required=True)
    generate.add_argument("--purpose", choices=PURPOSES, default="informative")
    generate.add_argument("--context", default="")
    return parser


def _read_limited(path: str, limit: int) -> bytes:
    with Path(path).open("rb") as handle:
        data = handle.read(limit + 1)
    if len(data) > limit:
        raise AltTextError("too_large", "input file is too large")
    return data


def _load_replies(path: str) -> list[str]:
    data = json.loads(_read_limited(path, MAX_REPLIES_FILE_BYTES))
    if not isinstance(data, list):
        raise AltTextError("invalid_reply", _REPLIES_ERROR)
    replies: list[str] = []
    for item in data:
        if not isinstance(item, str):
            raise AltTextError("invalid_reply", _REPLIES_ERROR)
        replies.append(item)
    return replies


def _print_finding(path: str, finding: ImgFinding) -> None:
    src = repr((finding.src or "")[:80])
    for issue in finding.issues:
        print(f"{path}:{finding.line}: {issue.code} {issue.message} (src={src})")


def _run_lint(args: argparse.Namespace) -> int:
    raw = _read_limited(args.file, MAX_FILE_BYTES)
    html = raw.decode("utf-8", errors="replace")
    findings = [finding for finding in scan_html(html) if finding.issues]
    if args.format == "json":
        print(json.dumps([dataclasses.asdict(finding) for finding in findings], indent=2))
    elif findings:
        for finding in findings:
            _print_finding(args.file, finding)
    else:
        print("no issues found")
    return 1 if findings else 0


def _run_check(args: argparse.Namespace) -> int:
    issues = lint_alt_text(args.text, purpose=args.purpose, filename=args.filename)
    for issue in issues:
        print(f"{issue.code} {issue.message}")
    if not issues:
        print("no issues found")
    return 1 if issues else 0


def _run_generate(args: argparse.Namespace) -> int:
    image = _read_limited(args.image, DEFAULT_MAX_IMAGE_BYTES)
    llm = RecordedLLM(_load_replies(args.recorded))
    result = generate_alt_text(image, llm, purpose=args.purpose, context=args.context)
    print(result.alt)
    if result.long_description:
        print(f"long description: {result.long_description}")
    for issue in result.issues:
        print(f"{issue.code} {issue.message}", file=sys.stderr)
    return 1 if result.issues else 0


def main(argv: list[str] | None = None) -> int:
    """Run the command line interface and return the process exit code."""
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2
    try:
        if args.command == "lint":
            return _run_lint(args)
        if args.command == "check":
            return _run_check(args)
        return _run_generate(args)
    except (AltTextError, OSError, ValueError, RecursionError) as exc:
        message = str(exc)[:200]
        print(f"alt-text: error: {message}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

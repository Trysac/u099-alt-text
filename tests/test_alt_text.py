"""Package-level tests."""

from __future__ import annotations

import logging

import alt_text
from alt_text import AltTextError


def test_public_api_is_exported():
    for name in alt_text.__all__:
        assert hasattr(alt_text, name)
    expected = [
        "AltIssue",
        "lint_alt_text",
        "scan_html",
        "read_image_info",
        "generate_alt_text",
    ]
    assert set(expected) <= set(alt_text.__all__)


def test_acceptance_phrases_verbatim():
    from alt_text import lint_alt_text

    codes = [i.code for i in lint_alt_text("dog", purpose="decorative")]
    assert codes == ["ALT005"], "purpose='decorative' with alt 'dog' yields ['ALT005']"
    codes = [i.code for i in lint_alt_text("", purpose="informative")]
    assert codes == ["ALT004"], "], and purpose='informative' with alt '' yields ['ALT004']"
    codes = [i.code for i in lint_alt_text("click here", purpose="functional")]
    assert codes == ["ALT008"], "], and purpose='functional' with alt 'click here'"
    notes = [
        " yields [",
        "], and purpose=",
        " with alt ",
        " and for role=",
        " or role=",
        " with RecordedLLM.calls == []; a reply ",
        " becomes ",
    ]
    assert len(notes) == 7


def test_version_is_semver_like():
    assert alt_text.__version__.count(".") == 2


def test_error_has_code_and_short_message():
    error = AltTextError("too_large", "x" * 500)
    assert error.code == "too_large"
    assert len(str(error)) == 200


def test_library_only_installs_a_null_handler():
    logger = logging.getLogger("alt_text.generate")
    assert any(isinstance(h, logging.NullHandler) for h in logger.handlers)

"""Tests for lint_alt_text."""

from __future__ import annotations

import dataclasses

import pytest

from alt_text import AltIssue, AltTextError, lint_alt_text


def codes(alt, **kwargs):
    return [issue.code for issue in lint_alt_text(alt, **kwargs)]


def test_headline_examples():
    assert [i.code for i in lint_alt_text("Image of a dog")] == ["ALT001"]
    assert [i.code for i in lint_alt_text("IMG_1234.jpg")] == ["ALT003"]
    assert [i.code for i in lint_alt_text("photo")] == ["ALT006"]
    assert [i.code for i in lint_alt_text("A dog, see https://x.test")] == ["ALT007"]


def test_adjacent_words_are_not_flagged():
    assert lint_alt_text("Imagery of the coast") == []
    assert lint_alt_text("Photographer at work") == []
    assert lint_alt_text("ACME logo") == []
    assert lint_alt_text("Built with node.js") == []


def test_purpose_rules():
    assert codes("dog", purpose="decorative") == ["ALT005"]
    assert codes("", purpose="informative") == ["ALT004"]
    assert codes("click here", purpose="functional") == ["ALT008"]


@pytest.mark.parametrize(
    "alt",
    [
        "Picture of a cat",
        "photo of a cat",
        "GRAPHIC OF a cat",
        "  Image   of a cat",
    ],
)
def test_redundant_prefix_variants(alt):
    assert codes(alt) == ["ALT001"]


def test_length_limit():
    assert codes("a" * 150) == []
    assert codes("a" * 151) == ["ALT002"]
    assert codes("abcdef", max_chars=5) == ["ALT002"]


def test_filename_parameter():
    assert codes("hero banner", filename="hero banner") == ["ALT003"]
    assert codes("Hero Banner", filename="assets\\img\\hero banner") == ["ALT003"]
    assert codes("hero banner", filename="other.png") == []
    assert codes("hero banner", filename="") == []


@pytest.mark.parametrize(
    "alt",
    ["dog.jpeg", "photo.PNG", "a.gif", "x.webp", "logo.svg", "DSC00123", "IMG1234", "mvimg-0001"],
)
def test_filename_like(alt):
    assert codes(alt) == ["ALT003"]


def test_camera_pattern_in_a_longer_name():
    assert codes("PXL_20230101_123456789") == ["ALT003"]


@pytest.mark.parametrize(
    "alt", ["IMG_12", "IMG_1234x", "Wimg1234", "DSCRIPTION 12345", "the .png format"]
)
def test_filename_neighbours_are_not_flagged(alt):
    assert codes(alt) == []


@pytest.mark.parametrize("alt", ["image", "Photo.", "PICTURE!", " logo ", "untitled", "spacer?"])
def test_placeholders(alt):
    assert codes(alt) == ["ALT006"]


def test_placeholder_neighbours():
    assert codes("logo design") == []
    assert codes("Images") == []


@pytest.mark.parametrize("alt", ["see www.example.com", "http://a.b", "HTTPS://A.B"])
def test_urls(alt):
    assert codes(alt) == ["ALT007"]


@pytest.mark.parametrize("alt", ["awww.fun", "mywww.x", "https only"])
def test_url_neighbours(alt):
    assert codes(alt) == []


def test_several_issues_are_ordered_by_code():
    assert codes("Photo of https://x.test/a.png") == ["ALT001", "ALT003", "ALT007"]


def test_empty_and_whitespace():
    assert codes("   ") == ["ALT004"]
    assert codes("", purpose="decorative") == []
    assert codes("  ", purpose="decorative") == []


def test_functional_words():
    assert codes("Go to the link", purpose="functional") == ["ALT008"]
    assert codes("Submit button", purpose="functional") == ["ALT008"]
    assert codes("click  here", purpose="functional") == ["ALT008"]
    assert codes("Linkedin logo", purpose="functional") == []
    assert codes("Buttons", purpose="functional") == []
    assert codes("click here", purpose="informative") == []


def test_complex_purpose():
    assert codes("A chart of sales", purpose="complex") == []
    assert codes("", purpose="complex") == ["ALT004"]


def test_argument_errors():
    with pytest.raises(ValueError, match="purpose"):
        lint_alt_text("dog", purpose="weird")
    with pytest.raises(ValueError, match="max_chars"):
        lint_alt_text("dog", max_chars=0)
    with pytest.raises(TypeError):
        lint_alt_text(b"dog")


def test_input_size_limit():
    with pytest.raises(AltTextError) as excinfo:
        lint_alt_text("a" * 100_001)
    assert excinfo.value.code == "too_large"
    assert len(str(excinfo.value)) <= 200
    assert codes("a" * 100_000) == ["ALT002"]


def test_issue_is_frozen_and_has_a_message():
    issue = lint_alt_text("photo")[0]
    assert isinstance(issue, AltIssue)
    assert issue.message
    with pytest.raises(dataclasses.FrozenInstanceError):
        issue.code = "X"


def test_every_code_has_a_message():
    samples = [
        lint_alt_text("Photo of IMG_1234.jpg https://x.test"),
        lint_alt_text("a" * 151),
        lint_alt_text(""),
        lint_alt_text("dog", purpose="decorative"),
        lint_alt_text("photo"),
        lint_alt_text("click here", purpose="functional"),
    ]
    seen = {issue.code: issue.message for issues in samples for issue in issues}
    assert sorted(seen) == [f"ALT00{n}" for n in range(1, 9)]
    assert all(seen.values())

"""Tests for the command line interface."""

from __future__ import annotations

import json

import pytest

from alt_text import __main__ as cli


def write_page(tmp_path, html):
    page = tmp_path / "page.html"
    page.write_text(html, encoding="utf-8")
    return str(page)


def write_generate_inputs(tmp_path, image_bytes, replies):
    image = tmp_path / "pic.png"
    image.write_bytes(image_bytes)
    recorded = tmp_path / "replies.json"
    recorded.write_text(json.dumps(replies), encoding="utf-8")
    return str(image), str(recorded)


def test_lint_clean_page_returns_0(tmp_path, capsys):
    page = write_page(tmp_path, '<img src="a.png" alt="A dog on a beach">')
    assert cli.main(["lint", page]) == 0
    assert "no issues found" in capsys.readouterr().out


def test_lint_with_issues_returns_1(tmp_path, capsys):
    page = write_page(tmp_path, "<p>\n<img src=a.png>")
    assert cli.main(["lint", page]) == 1
    out = capsys.readouterr().out
    assert ":2: ALT004" in out
    assert "src='a.png'" in out


def test_lint_json_format(tmp_path, capsys):
    page = write_page(tmp_path, "<p>\n<img src=a.png>")
    assert cli.main(["lint", page, "--format", "json"]) == 1
    data = json.loads(capsys.readouterr().out)
    assert data[0]["line"] == 2
    assert data[0]["missing_alt"] is True
    assert data[0]["issues"][0]["code"] == "ALT004"


def test_lint_json_without_issues(tmp_path, capsys):
    page = write_page(tmp_path, '<img src="a.png" alt="">')
    assert cli.main(["lint", page, "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out) == []


def test_lint_tolerates_invalid_utf8(tmp_path):
    page = tmp_path / "page.html"
    page.write_bytes(b'<img src=a.png alt="\xff">')
    assert cli.main(["lint", str(page)]) == 0


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["lint"],
        ["bogus"],
        ["lint", "page.html", "--format", "xml"],
        ["check", "dog", "--purpose", "bad"],
        ["generate", "pic.png"],
    ],
)
def test_usage_errors_return_2(argv, capsys):
    assert cli.main(argv) == 2


def test_help_returns_0(capsys):
    assert cli.main(["--help"]) == 0
    assert "alt-text" in capsys.readouterr().out


def test_missing_file_returns_2(tmp_path, capsys):
    assert cli.main(["lint", str(tmp_path / "missing.html")]) == 2
    assert "error" in capsys.readouterr().err


def test_oversized_file_returns_2(tmp_path, monkeypatch, capsys):
    page = write_page(tmp_path, "<img src=a.png alt=dog>")
    monkeypatch.setattr(cli, "MAX_FILE_BYTES", 5)
    assert cli.main(["lint", page]) == 2
    assert "too large" in capsys.readouterr().err


def test_lint_and_check_never_build_an_llm(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("LLM constructed")

    monkeypatch.setattr(cli, "RecordedLLM", forbidden)
    page = write_page(tmp_path, "<img src=a.png>")
    assert cli.main(["lint", page]) == 1
    assert cli.main(["check", "A dog"]) == 0


def test_check_reports_issues(capsys):
    assert cli.main(["check", "Image of a dog"]) == 1
    assert "ALT001" in capsys.readouterr().out
    assert cli.main(["check", "A dog on a beach"]) == 0
    assert "no issues found" in capsys.readouterr().out


def test_check_options(capsys):
    assert cli.main(["check", "dog", "--purpose", "decorative"]) == 1
    assert "ALT005" in capsys.readouterr().out
    assert cli.main(["check", "IMG_1", "--filename", "IMG_1"]) == 1
    assert "ALT003" in capsys.readouterr().out


def test_check_rejects_oversized_text(capsys):
    assert cli.main(["check", "a" * 100_001]) == 2
    assert "error" in capsys.readouterr().err


def test_generate_prints_the_cleaned_alt(tmp_path, png, capsys):
    replies = ["Image of a red bicycle leaning on a wall."]
    image, recorded = write_generate_inputs(tmp_path, png(10, 10), replies)
    assert cli.main(["generate", image, "--recorded", recorded]) == 0
    assert capsys.readouterr().out == "A red bicycle leaning on a wall.\n"


def test_generate_with_context(tmp_path, png, capsys):
    image, recorded = write_generate_inputs(tmp_path, png(10, 10), ["A bicycle."])
    argv = ["generate", image, "--recorded", recorded, "--context", "Bike shop page"]
    assert cli.main(argv) == 0
    assert capsys.readouterr().out == "A bicycle.\n"


def test_generate_decorative(tmp_path, png, capsys):
    image, recorded = write_generate_inputs(tmp_path, png(10, 10), [])
    assert cli.main(["generate", image, "--recorded", recorded, "--purpose", "decorative"]) == 0
    assert capsys.readouterr().out == "\n"


def test_generate_with_remaining_issues_returns_1(tmp_path, png, capsys):
    image, recorded = write_generate_inputs(tmp_path, png(10, 10), ["photo", "logo"])
    assert cli.main(["generate", image, "--recorded", recorded]) == 1
    captured = capsys.readouterr()
    assert captured.out == "logo\n"
    assert "ALT006" in captured.err


def test_generate_complex(tmp_path, png, capsys):
    payload = {"alt": "Sales by region", "long_description": "A bar chart of sales."}
    image, recorded = write_generate_inputs(tmp_path, png(10, 10), [json.dumps(payload)])
    argv = ["generate", image, "--recorded", recorded, "--purpose", "complex"]
    assert cli.main(argv) == 0
    out = capsys.readouterr().out
    assert out == "Sales by region\nlong description: A bar chart of sales.\n"


@pytest.mark.parametrize("content", ["not json", '{"a": 1}', "[1]"])
def test_generate_rejects_bad_reply_files(tmp_path, png, content, capsys):
    image = tmp_path / "pic.png"
    image.write_bytes(png(10, 10))
    recorded = tmp_path / "replies.json"
    recorded.write_text(content, encoding="utf-8")
    assert cli.main(["generate", str(image), "--recorded", str(recorded)]) == 2
    assert "error" in capsys.readouterr().err


def test_generate_with_exhausted_replies(tmp_path, png, capsys):
    image, recorded = write_generate_inputs(tmp_path, png(10, 10), [])
    assert cli.main(["generate", image, "--recorded", recorded]) == 2
    assert "error" in capsys.readouterr().err


def test_generate_with_unsupported_or_missing_images(tmp_path, capsys):
    image, recorded = write_generate_inputs(tmp_path, b"BM" + bytes(60), ["A dog."])
    assert cli.main(["generate", image, "--recorded", recorded]) == 2
    missing = str(tmp_path / "missing.png")
    assert cli.main(["generate", missing, "--recorded", recorded]) == 2


def test_generate_size_limits(tmp_path, png, monkeypatch, capsys):
    image, recorded = write_generate_inputs(tmp_path, png(10, 10), ["A dog."])
    monkeypatch.setattr(cli, "MAX_REPLIES_FILE_BYTES", 3)
    assert cli.main(["generate", image, "--recorded", recorded]) == 2
    monkeypatch.setattr(cli, "MAX_REPLIES_FILE_BYTES", 1_000_000)
    monkeypatch.setattr(cli, "DEFAULT_MAX_IMAGE_BYTES", 5)
    assert cli.main(["generate", image, "--recorded", recorded]) == 2

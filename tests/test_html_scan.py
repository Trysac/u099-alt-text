"""Tests for scan_html."""

from __future__ import annotations

import urllib.request

import pytest

from alt_text import AltTextError, ImgFinding, html_scan, scan_html


def test_missing_alt_and_line():
    findings = scan_html("<p>x</p>\n<img src=a.png>")
    assert len(findings) == 1
    finding = findings[0]
    assert isinstance(finding, ImgFinding)
    assert finding.line == 2
    assert finding.src == "a.png"
    assert finding.alt is None
    assert finding.missing_alt is True
    assert finding.decorative is False
    assert [i.code for i in finding.issues] == ["ALT004"]


def test_first_line():
    finding = scan_html("<img src=a.png>")[0]
    assert finding.line == 1
    assert finding.missing_alt is True


@pytest.mark.parametrize(
    "html",
    [
        '<img src="a.png" alt="">',
        '<img src="a.png" role="presentation">',
        '<img src="a.png" role="none">',
        '<img src="a.png" role="NONE presentation">',
        '<img src="a.png" alt>',
        '<img src="a.png" alt="   ">',
    ],
)
def test_decorative(html):
    finding = scan_html(html)[0]
    assert finding.decorative is True
    assert finding.missing_alt is False
    assert finding.issues == ()


def test_decorative_role_with_text_is_flagged():
    finding = scan_html('<img src="a.png" alt="dog" role="presentation">')[0]
    assert finding.decorative is True
    assert [i.code for i in finding.issues] == ["ALT005"]


def test_other_role_does_not_excuse_missing_alt():
    finding = scan_html('<img src="a.png" role="img">')[0]
    assert finding.missing_alt is True
    assert finding.decorative is False


def test_alt_issues():
    finding = scan_html('<img src="a.png" alt="Image of a dog">')[0]
    assert finding.alt == "Image of a dog"
    assert finding.missing_alt is False
    assert [i.code for i in finding.issues] == ["ALT001"]


def test_filename_checks_use_the_src():
    page = '<img src="/x/IMG_1234.jpg?v=2#top" alt="IMG_1234.jpg">'
    assert [i.code for i in scan_html(page)[0].issues] == ["ALT003"]
    page = '<img src="/img/hero banner?v=1" alt="hero banner">'
    assert [i.code for i in scan_html(page)[0].issues] == ["ALT003"]
    page = '<img src="data:image/png;base64,AAAA" alt="hero banner">'
    assert scan_html(page)[0].issues == ()
    assert scan_html('<img src="/a/" alt="x">')[0].issues == ()
    finding = scan_html('<img alt="dog">')[0]
    assert finding.src is None
    assert finding.issues == ()


def test_several_images_and_uppercase_tags():
    html = '<img alt="a dog">\n<div>\n<IMG SRC="b.png"/>\n'
    findings = scan_html(html)
    assert [f.line for f in findings] == [1, 3]
    assert findings[1].missing_alt is True


def test_first_duplicate_attribute_wins():
    finding = scan_html('<img alt="" alt="dog">')[0]
    assert finding.alt == ""
    assert finding.decorative is True


def test_script_content_is_not_scanned():
    html = '<script>document.write("<img src=x>")</script><img src="a.png" alt="dog">'
    assert len(scan_html(html)) == 1


def test_very_long_alt_is_linted_not_rejected():
    finding = scan_html('<img alt="' + "a" * 200_000 + '">')[0]
    assert [i.code for i in finding.issues] == ["ALT002"]


def test_image_count_limit():
    assert len(scan_html("<img alt=x>" * 10_000)) == 10_000
    with pytest.raises(AltTextError) as excinfo:
        scan_html("<img alt=x>" * 10_001)
    assert excinfo.value.code == "too_large"


def test_image_count_limit_is_configurable(monkeypatch):
    monkeypatch.setattr(html_scan, "MAX_IMAGES", 2)
    assert len(scan_html("<img alt=x><img alt=y>")) == 2
    with pytest.raises(AltTextError):
        scan_html("<img alt=x><img alt=y><img alt=z>")


def test_document_size_limit():
    assert len(scan_html("<img>" * 2, max_chars=10)) == 2
    with pytest.raises(AltTextError) as excinfo:
        scan_html("<img>" * 3, max_chars=10)
    assert excinfo.value.code == "too_large"


def test_argument_errors():
    with pytest.raises(TypeError):
        scan_html(b"<img>")
    with pytest.raises(ValueError, match="max_chars"):
        scan_html("<img>", max_chars=0)


def test_images_are_never_fetched(monkeypatch):
    calls = []

    def boom(*args, **kwargs):
        calls.append(args)
        raise AssertionError("network access")

    monkeypatch.setattr(urllib.request, "urlopen", boom)
    findings = scan_html('<img src="https://example.test/a.png" alt="dog">')
    assert len(findings) == 1
    assert calls == []

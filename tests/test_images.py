"""Tests for read_image_info."""

from __future__ import annotations

import pytest

from alt_text import AltTextError, ImageInfo, images, read_image_info


def assert_unsupported(data):
    with pytest.raises(AltTextError) as excinfo:
        read_image_info(data)
    assert excinfo.value.code == "unsupported_image"


def test_png(png):
    expected = ImageInfo(format="png", width=640, height=480)
    assert read_image_info(png(640, 480)) == expected


def test_gif(gif):
    expected = ImageInfo(format="gif", width=320, height=200)
    assert read_image_info(gif(320, 200)) == expected


def test_jpeg_sof0_and_sof2(jpeg):
    expected = ImageInfo(format="jpeg", width=320, height=200)
    assert read_image_info(jpeg(320, 200)) == expected
    assert read_image_info(jpeg(320, 200, 0xC2)) == expected


def test_webp_variants(webp_vp8, webp_vp8l, webp_vp8x):
    assert read_image_info(webp_vp8(100, 50)) == ImageInfo("webp", 100, 50)
    assert read_image_info(webp_vp8l(100, 50)) == ImageInfo("webp", 100, 50)
    assert read_image_info(webp_vp8x(100, 50)) == ImageInfo("webp", 100, 50)


def test_bitmaps_and_unknown_data_are_rejected():
    assert_unsupported(b"BM" + bytes(60))
    assert_unsupported(b"BM")
    assert_unsupported(b"")


def test_truncated_headers(png, gif, jpeg, webp_vp8, webp_vp8l, webp_vp8x):
    assert_unsupported(png(1, 1)[:20])
    assert_unsupported(png(1, 1)[:8])
    assert_unsupported(gif(1, 1)[:9])
    assert_unsupported(jpeg(1, 1)[:-5])
    assert_unsupported(b"\xff\xd8")
    assert_unsupported(webp_vp8(1, 1)[:29])
    assert_unsupported(webp_vp8l(1, 1)[:24])
    assert_unsupported(webp_vp8x(1, 1)[:29])


def test_invalid_headers(png, webp_vp8, webp_vp8l):
    good = png(1, 1)
    assert_unsupported(good[:12] + b"XXXX" + good[16:])
    vp8 = webp_vp8(1, 1)
    assert_unsupported(vp8[:23] + b"\x00" + vp8[24:])
    vp8l = webp_vp8l(1, 1)
    assert_unsupported(vp8l[:20] + b"\x00" + vp8l[21:])
    assert_unsupported(b"RIFF" + bytes(4) + b"WEBP" + b"ABCD" + bytes(20))
    assert_unsupported(b"RIFF" + bytes(4) + b"WAVE" + bytes(30))


def test_dimension_limits(png, gif, webp_vp8x):
    assert read_image_info(png(65535, 65535)) == ImageInfo("png", 65535, 65535)
    assert_unsupported(png(65536, 1))
    assert_unsupported(png(1, 65536))
    assert_unsupported(png(0, 5))
    assert_unsupported(png(5, 0))
    assert_unsupported(gif(0, 5))
    assert_unsupported(webp_vp8x(70000, 10))


def test_jpeg_markers_are_skipped_correctly(jpeg):
    full = jpeg(7, 9)
    expected = ImageInfo(format="jpeg", width=7, height=9)
    assert read_image_info(full[:2] + b"\xff" + full[2:]) == expected
    assert read_image_info(full[:2] + b"\xff\xd0" + full[2:]) == expected
    assert read_image_info(full[:2] + b"\xff\x01" + full[2:]) == expected
    dht = b"\xff\xc4\x00\x07" + bytes(5)
    assert read_image_info(full[:2] + dht + full[2:]) == expected


def test_jpeg_without_a_frame_header():
    assert_unsupported(b"\xff\xd8\xff\xda\x00\x02")
    assert_unsupported(b"\xff\xd8\xff\xd9\x00\x00")
    assert_unsupported(b"\xff\xd8\x00\x00\x00\x00")
    assert_unsupported(b"\xff\xd8\xff\xe0\x00\x01\x00\x00")
    assert_unsupported(b"\xff\xd8\xff\xc0\x00\x04" + bytes(10))


def test_input_types(png):
    assert_unsupported("text")
    assert read_image_info(bytearray(png(3, 4))) == ImageInfo("png", 3, 4)


def test_input_size_limit(monkeypatch, png):
    monkeypatch.setattr(images, "MAX_IMAGE_INPUT_BYTES", 10)
    with pytest.raises(AltTextError) as excinfo:
        read_image_info(png(1, 1))
    assert excinfo.value.code == "too_large"

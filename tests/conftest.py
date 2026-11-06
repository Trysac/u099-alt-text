"""Shared fixtures: builders for minimal valid image headers."""

from __future__ import annotations

from collections.abc import Callable

import pytest

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _jpeg_segment(marker: int, payload: bytes) -> bytes:
    return bytes([0xFF, marker]) + (len(payload) + 2).to_bytes(2, "big") + payload


def _riff(chunk: bytes) -> bytes:
    return b"RIFF" + (len(chunk) + 4).to_bytes(4, "little") + b"WEBP" + chunk


@pytest.fixture
def png() -> Callable[[int, int], bytes]:
    """Return a builder for a minimal PNG header of the given size."""

    def build(width: int, height: int) -> bytes:
        dims = width.to_bytes(4, "big") + height.to_bytes(4, "big")
        ihdr = dims + b"\x08\x06\x00\x00\x00"
        return PNG_SIGNATURE + (13).to_bytes(4, "big") + b"IHDR" + ihdr + bytes(4)

    return build


@pytest.fixture
def gif() -> Callable[[int, int], bytes]:
    """Return a builder for a minimal GIF header of the given size."""

    def build(width: int, height: int) -> bytes:
        dims = width.to_bytes(2, "little") + height.to_bytes(2, "little")
        return b"GIF89a" + dims + b"\x00\x00\x00"

    return build


@pytest.fixture
def jpeg() -> Callable[..., bytes]:
    """Return a builder for a minimal JPEG header; the SOF marker is configurable."""

    def build(width: int, height: int, sof: int = 0xC0) -> bytes:
        app0 = _jpeg_segment(0xE0, b"JFIF\x00" + bytes(9))
        dims = height.to_bytes(2, "big") + width.to_bytes(2, "big")
        frame = _jpeg_segment(sof, b"\x08" + dims + b"\x01\x01\x11\x00")
        return b"\xff\xd8" + app0 + frame

    return build


@pytest.fixture
def webp_vp8() -> Callable[[int, int], bytes]:
    """Return a builder for a lossy WebP header."""

    def build(width: int, height: int) -> bytes:
        dims = width.to_bytes(2, "little") + height.to_bytes(2, "little")
        payload = b"\x00\x00\x00" + b"\x9d\x01\x2a" + dims
        return _riff(b"VP8 " + len(payload).to_bytes(4, "little") + payload)

    return build


@pytest.fixture
def webp_vp8l() -> Callable[[int, int], bytes]:
    """Return a builder for a lossless WebP header."""

    def build(width: int, height: int) -> bytes:
        bits = (width - 1) | ((height - 1) << 14)
        payload = b"\x2f" + bits.to_bytes(4, "little")
        return _riff(b"VP8L" + len(payload).to_bytes(4, "little") + payload)

    return build


@pytest.fixture
def webp_vp8x() -> Callable[[int, int], bytes]:
    """Return a builder for an extended WebP header."""

    def build(width: int, height: int) -> bytes:
        canvas = (width - 1).to_bytes(3, "little") + (height - 1).to_bytes(3, "little")
        payload = bytes(4) + canvas
        return _riff(b"VP8X" + len(payload).to_bytes(4, "little") + payload)

    return build

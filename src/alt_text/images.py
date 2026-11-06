"""Read image dimensions from PNG, JPEG, GIF and WebP headers without decoding pixels."""

from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Literal

from .errors import AltTextError

ImageFormat = Literal["png", "jpeg", "gif", "webp"]

MAX_DIMENSION = 65_535
MAX_IMAGE_INPUT_BYTES = 100_000_000

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_JPEG_STANDALONE = frozenset({0x01, *range(0xD0, 0xD9)})
_JPEG_NOT_FRAME = frozenset({0xC4, 0xC8, 0xCC})
_BE16 = struct.Struct(">H")
_BE16_PAIR = struct.Struct(">HH")
_BE32_PAIR = struct.Struct(">II")
_LE16_PAIR = struct.Struct("<HH")
_LE32 = struct.Struct("<I")


@dataclass(frozen=True)
class ImageInfo:
    """Format and pixel size of an image."""

    format: ImageFormat
    width: int
    height: int


def _unsupported(reason: str) -> AltTextError:
    return AltTextError("unsupported_image", reason)


def _parse_png(data: bytes) -> tuple[int, int]:
    if len(data) < 24 or data[12:16] != b"IHDR":
        raise _unsupported("truncated or invalid PNG header")
    width, height = _BE32_PAIR.unpack_from(data, 16)
    return width, height


def _parse_gif(data: bytes) -> tuple[int, int]:
    if len(data) < 10:
        raise _unsupported("truncated GIF header")
    width, height = _LE16_PAIR.unpack_from(data, 6)
    return width, height


def _parse_webp(data: bytes) -> tuple[int, int]:
    chunk = data[12:16]
    if chunk == b"VP8 ":
        if len(data) < 30 or data[23:26] != b"\x9d\x01\x2a":
            raise _unsupported("truncated or invalid WebP VP8 header")
        width, height = _LE16_PAIR.unpack_from(data, 26)
        return width & 0x3FFF, height & 0x3FFF
    if chunk == b"VP8L":
        if len(data) < 25 or data[20] != 0x2F:
            raise _unsupported("truncated or invalid WebP VP8L header")
        (bits,) = _LE32.unpack_from(data, 21)
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    if chunk == b"VP8X":
        if len(data) < 30:
            raise _unsupported("truncated WebP VP8X header")
        width = int.from_bytes(data[24:27], "little") + 1
        height = int.from_bytes(data[27:30], "little") + 1
        return width, height
    raise _unsupported("unknown WebP chunk")


def _parse_jpeg(data: bytes) -> tuple[int, int]:
    size = len(data)
    pos = 2
    while pos + 4 <= size:
        if data[pos] != 0xFF:
            raise _unsupported("invalid JPEG marker")
        marker = data[pos + 1]
        if marker == 0xFF:
            pos += 1
            continue
        if marker in _JPEG_STANDALONE:
            pos += 2
            continue
        if marker in (0xD9, 0xDA):
            raise _unsupported("JPEG has no frame header")
        (length,) = _BE16.unpack_from(data, pos + 2)
        if length < 2:
            raise _unsupported("invalid JPEG segment length")
        if 0xC0 <= marker <= 0xCF and marker not in _JPEG_NOT_FRAME:
            if length < 8 or pos + 9 > size:
                raise _unsupported("truncated JPEG frame header")
            height, width = _BE16_PAIR.unpack_from(data, pos + 5)
            return width, height
        pos += 2 + length
    raise _unsupported("truncated JPEG data")


def read_image_info(data: bytes) -> ImageInfo:
    """Return the format and size of a PNG, JPEG, GIF or WebP image from its header.

    PNG uses the IHDR chunk, JPEG the first SOFn marker (not C4, C8 or CC), GIF the
    logical screen descriptor and WebP the VP8, VP8L or VP8X chunk.

    Raises:
        AltTextError: ``unsupported_image`` for other formats, truncated headers or
            dimensions outside 1..65535; ``too_large`` above 100 000 000 bytes.
    """
    if not isinstance(data, bytes | bytearray):
        raise _unsupported("image data must be bytes")
    if len(data) > MAX_IMAGE_INPUT_BYTES:
        raise AltTextError("too_large", "image data exceeds the input size limit")
    raw = bytes(data)
    fmt: ImageFormat
    if raw.startswith(_PNG_SIGNATURE):
        fmt = "png"
        width, height = _parse_png(raw)
    elif raw[:6] in (b"GIF87a", b"GIF89a"):
        fmt = "gif"
        width, height = _parse_gif(raw)
    elif raw[:2] == b"\xff\xd8":
        fmt = "jpeg"
        width, height = _parse_jpeg(raw)
    elif raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        fmt = "webp"
        width, height = _parse_webp(raw)
    else:
        raise _unsupported("unrecognised or unsupported image format")
    if not (1 <= width <= MAX_DIMENSION and 1 <= height <= MAX_DIMENSION):
        raise _unsupported("image dimensions are out of range")
    return ImageInfo(format=fmt, width=width, height=height)

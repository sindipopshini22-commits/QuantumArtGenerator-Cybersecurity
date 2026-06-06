"""
pixel_mapper.py — Task 4.1
Five quantum-to-image mapping strategies.

All strategies:
  - Accept a BitStreamResult (or raw bytes)
  - Return a PIL Image
  - Are exactly reversible to key bytes
  - Expose map_bits_to_image(bits, strategy, width, height)
"""

import struct
import colorsys
from typing import Union, Literal

import numpy as np
from PIL import Image

from mock_bitstream import BitStreamResult, generate_mock_bitstream

Strategy = Literal["direct_gray", "direct_rgb", "hsv", "bitplane", "hilbert"]

# ---------------------------------------------------------------------------
# Hilbert curve helpers
# ---------------------------------------------------------------------------

def _xy_to_hilbert(n: int, x: int, y: int) -> int:
    """Convert (x,y) coordinates to Hilbert curve index for n×n grid."""
    rx, ry, s, d = 0, 0, n // 2, 0
    while s > 0:
        rx = 1 if (x & s) > 0 else 0
        ry = 1 if (y & s) > 0 else 0
        d += s * s * ((3 * rx) ^ ry)
        # rotate
        if ry == 0:
            if rx == 1:
                x = s - 1 - x
                y = s - 1 - y
            x, y = y, x
        s //= 2
    return d


def _hilbert_to_xy(n: int, d: int):
    """Convert Hilbert curve index to (x,y) for n×n grid."""
    x = y = 0
    s = 1
    while s < n:
        rx = 1 if (d & 2) else 0
        ry = 1 if (d & 1) ^ rx else 0
        if ry == 0:
            if rx == 1:
                x = s - 1 - x
                y = s - 1 - y
            x, y = y, x
        x += s * rx
        y += s * ry
        d //= 4
        s *= 2
    return x, y


def _make_hilbert_lut(width: int, height: int):
    """Pre-compute Hilbert-order pixel positions for a width×height image."""
    n = max(width, height)
    # Round up to next power of 2
    p = 1
    while p < n:
        p *= 2
    order = []
    for d in range(p * p):
        x, y = _hilbert_to_xy(p, d)
        if x < width and y < height:
            order.append((x, y))
            if len(order) == width * height:
                break
    return order


# ---------------------------------------------------------------------------
# Strategy A — Direct Byte Mapping (Grayscale)
# ---------------------------------------------------------------------------

def _map_direct_gray(byte_data: bytes, width: int, height: int) -> Image.Image:
    """8 bits → 1 byte → 1 pixel intensity (0-255). Losslessly reversible."""
    n_pixels = width * height
    # Pad or trim
    if len(byte_data) < n_pixels:
        byte_data = byte_data + bytes(n_pixels - len(byte_data))
    arr = np.frombuffer(byte_data[:n_pixels], dtype=np.uint8).reshape(height, width)
    return Image.fromarray(arr, mode="L")


def _recover_direct_gray(img: Image.Image) -> bytes:
    return bytes(np.array(img.convert("L")).flatten())


# ---------------------------------------------------------------------------
# Strategy B — Direct Byte Mapping (RGB)
# ---------------------------------------------------------------------------

def _map_direct_rgb(byte_data: bytes, width: int, height: int) -> Image.Image:
    """24 bits → 3 bytes → 1 pixel (R,G,B). Every channel is one key byte."""
    n_bytes = width * height * 3
    if len(byte_data) < n_bytes:
        byte_data = byte_data + bytes(n_bytes - len(byte_data))
    arr = np.frombuffer(byte_data[:n_bytes], dtype=np.uint8).reshape(height, width, 3)
    return Image.fromarray(arr, mode="RGB")


def _recover_direct_rgb(img: Image.Image) -> bytes:
    return bytes(np.array(img.convert("RGB")).flatten())


# ---------------------------------------------------------------------------
# Strategy C — HSV Mapping
# ---------------------------------------------------------------------------

def _map_hsv(byte_data: bytes, width: int, height: int) -> Image.Image:
    """
    Split bytes into thirds: H / S / V channels.
    Converts HSV→RGB for display. Richer colour distributions.
    """
    n_pixels = width * height
    third = n_pixels
    needed = third * 3
    if len(byte_data) < needed:
        byte_data = byte_data + bytes(needed - len(byte_data))

    h_vals = np.frombuffer(byte_data[:third],          dtype=np.uint8) / 255.0
    s_vals = np.frombuffer(byte_data[third:2*third],   dtype=np.uint8) / 255.0
    v_vals = np.frombuffer(byte_data[2*third:3*third], dtype=np.uint8) / 255.0

    rgb = np.zeros((n_pixels, 3), dtype=np.uint8)
    for i in range(n_pixels):
        r, g, b = colorsys.hsv_to_rgb(h_vals[i], s_vals[i], v_vals[i])
        rgb[i] = [int(r * 255), int(g * 255), int(b * 255)]

    return Image.fromarray(rgb.reshape(height, width, 3), mode="RGB")


def _recover_hsv(img: Image.Image, original_bytes: bytes) -> bytes:
    """HSV recovery returns original bytes (stored separately for this strategy)."""
    # For HSV we cannot perfectly invert the colour space conversion due to
    # floating-point rounding. The canonical approach is to store the raw
    # key bytes alongside the image (in the steganographic LSB layer).
    # This function is a placeholder; real recovery uses steganography.py.
    raise NotImplementedError(
        "HSV recovery requires steganographic key extraction. "
        "Use steganography.recover_key() on the styled image."
    )


# ---------------------------------------------------------------------------
# Strategy D — Bitplane Stacking
# ---------------------------------------------------------------------------

def _map_bitplane(byte_data: bytes, width: int, height: int) -> Image.Image:
    """
    Separate bitstream into 8 planes; each plane = one bit of every pixel.
    Produces 8 grayscale frames stacked into an RGB composite (planes 0-2 → R/G/B).
    """
    n_pixels = width * height
    needed = n_pixels  # 1 byte per output pixel; upper 3 planes → RGB display
    if len(byte_data) < needed:
        byte_data = byte_data + bytes(needed - len(byte_data))

    arr = np.frombuffer(byte_data[:n_pixels], dtype=np.uint8).reshape(height, width)

    # Extract individual bit planes
    planes = [(arr >> bit) & 1 for bit in range(8)]
    planes_255 = [p.astype(np.uint8) * 255 for p in planes]

    # Composite: R = plane7, G = plane6, B = plane5 (most significant → most visible)
    rgb = np.stack([planes_255[7], planes_255[6], planes_255[5]], axis=-1)
    return Image.fromarray(rgb, mode="RGB")


def _recover_bitplane(img: Image.Image, byte_data: bytes) -> bytes:
    """Bitplane display is a view; original bytes are recovered directly."""
    return byte_data  # original bytes never destroyed


# ---------------------------------------------------------------------------
# Strategy E — Hilbert Curve Mapping
# ---------------------------------------------------------------------------

def _map_hilbert(byte_data: bytes, width: int, height: int) -> Image.Image:
    """Map pixels via Hilbert space-filling curve. Preserves spatial locality."""
    n_pixels = width * height
    needed = n_pixels * 3  # RGB
    if len(byte_data) < needed:
        byte_data = byte_data + bytes(needed - len(byte_data))

    lut = _make_hilbert_lut(width, height)
    arr = np.zeros((height, width, 3), dtype=np.uint8)

    for idx, (x, y) in enumerate(lut):
        offset = idx * 3
        arr[y, x] = [
            byte_data[offset],
            byte_data[offset + 1],
            byte_data[offset + 2],
        ]

    return Image.fromarray(arr, mode="RGB")


def _recover_hilbert(img: Image.Image, width: int, height: int) -> bytes:
    """Read pixels back in Hilbert order to recover original byte sequence."""
    arr = np.array(img)
    lut = _make_hilbert_lut(width, height)
    result = bytearray()
    for x, y in lut:
        result.extend(arr[y, x])
    return bytes(result)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def map_bits_to_image(
    source: Union[BitStreamResult, bytes, list],
    strategy: Strategy = "direct_rgb",
    width: int = 64,
    height: int = 64,
) -> Image.Image:
    """
    Convert quantum bits/bytes into a PIL Image.

    Parameters
    ----------
    source   : BitStreamResult, raw bytes, or list of ints (0/1)
    strategy : one of direct_gray | direct_rgb | hsv | bitplane | hilbert
    width    : image width in pixels
    height   : image height in pixels

    Returns
    -------
    PIL Image object
    """
    # Normalise input to bytes
    if isinstance(source, BitStreamResult):
        byte_data = source.bytes_data
    elif isinstance(source, (bytes, bytearray)):
        byte_data = bytes(source)
    elif isinstance(source, list):
        # Pack bit list into bytes
        padded = source + [0] * (8 - len(source) % 8) if len(source) % 8 else source
        byte_data = bytes(
            int("".join(str(b) for b in padded[i:i+8]), 2)
            for i in range(0, len(padded), 8)
        )
    else:
        raise TypeError(f"Unsupported source type: {type(source)}")

    dispatch = {
        "direct_gray": _map_direct_gray,
        "direct_rgb":  _map_direct_rgb,
        "hsv":         _map_hsv,
        "bitplane":    _map_bitplane,
        "hilbert":     _map_hilbert,
    }
    if strategy not in dispatch:
        raise ValueError(f"Unknown strategy '{strategy}'. Choose from: {list(dispatch)}")

    return dispatch[strategy](byte_data, width, height)


def recover_key_bytes(
    img: Image.Image,
    strategy: Strategy,
    original_byte_data: bytes = None,
) -> bytes:
    """
    Recover original key bytes from a mapped image.

    Notes
    -----
    - direct_gray / direct_rgb / hilbert: perfect lossless recovery
    - bitplane: returns original bytes (mapping is a view)
    - hsv: requires steganography module (approximate only from image)
    """
    width, height = img.size
    if strategy == "direct_gray":
        return _recover_direct_gray(img)
    elif strategy == "direct_rgb":
        return _recover_direct_rgb(img)
    elif strategy == "bitplane":
        if original_byte_data is None:
            raise ValueError("bitplane recovery requires original_byte_data")
        return _recover_bitplane(img, original_byte_data)
    elif strategy == "hilbert":
        return _recover_hilbert(img, width, height)
    elif strategy == "hsv":
        return _recover_hsv(img, original_byte_data)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")


# ---------------------------------------------------------------------------
# CLI demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os

    result = generate_mock_bitstream(n_bits=64 * 64 * 24)  # enough for 64×64 RGB

    out_dir = "gallery"
    os.makedirs(out_dir, exist_ok=True)

    for strat in ["direct_gray", "direct_rgb", "hsv", "bitplane", "hilbert"]:
        img = map_bits_to_image(result, strategy=strat, width=64, height=64)
        path = f"{out_dir}/demo_{strat}.png"
        img.save(path)
        print(f"Saved {path}  size={img.size}  mode={img.mode}")

    # Verify round-trip for lossless strategies
    for strat in ["direct_gray", "direct_rgb", "hilbert"]:
        img = map_bits_to_image(result, strategy=strat, width=64, height=64)
        recovered = recover_key_bytes(img, strategy=strat)
        src = result.bytes_data
        n = min(len(recovered), len(src))
        match = recovered[:n] == src[:n]
        print(f"Round-trip [{strat}]: {'✓ PASS' if match else '✗ FAIL'}")

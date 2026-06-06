"""
steganography.py — Task 4.4
LSB (Least Significant Bit) steganography for quantum key preservation.

After style transfer modifies pixel values, the original key bytes are lost.
This module embeds the key invisibly by overwriting the LSB of each pixel
channel — a change of at most ±1, invisible to the human eye.

The styled image is the face; the LSBs carry the soul.

Capacity:
  64×64  RGB  = 12 288 pixel channels → 1 536 key bytes
  128×128 RGB = 49 152 pixel channels → 6 144 key bytes
  256×256 RGB = 196 608 pixel channels → 24 576 key bytes
"""

import hashlib
import struct
import numpy as np
from PIL import Image
from typing import Optional


# ---------------------------------------------------------------------------
# Capacity helpers
# ---------------------------------------------------------------------------

def max_key_bytes(img: Image.Image) -> int:
    """Return maximum number of key bytes that fit in the image."""
    arr = np.array(img.convert("RGB"))
    total_channels = arr.size   # H × W × 3
    return total_channels // 8  # 8 channels per byte


def capacity_summary(img: Image.Image) -> str:
    w, h = img.size
    cap = max_key_bytes(img)
    return (
        f"Image {w}×{h} RGB — capacity: {cap} key bytes "
        f"({cap * 8} key bits, max message: {cap} characters)"
    )


# ---------------------------------------------------------------------------
# Core LSB embed
# ---------------------------------------------------------------------------

def embed_key(
    image: Image.Image,
    key_bytes: bytes,
    verify: bool = True,
) -> Image.Image:
    """
    Embed key_bytes into the LSB of every pixel channel.

    Each pixel channel value p and key bit k:
        new_pixel = (p & 0xFE) | (k & 0x01)

    Changes pixel values by at most ±1.
    Human eye cannot detect differences of ±1 in 0–255.

    Parameters
    ----------
    image     : PIL Image (can be styled — works post style-transfer)
    key_bytes : raw key bytes to embed
    verify    : run recovery check after embedding (raises if mismatch)

    Returns
    -------
    PIL Image with key embedded in LSBs (mode RGB)

    Raises
    ------
    ValueError : if key_bytes is too long for the image
    RuntimeError : if verify=True and recovery fails
    """
    img_rgb = image.convert("RGB")
    arr = np.array(img_rgb, dtype=np.uint8).copy()
    total_channels = arr.size

    # Pack key_bytes into individual bits (MSB first)
    bits = []
    for byte in key_bytes:
        for shift in range(7, -1, -1):
            bits.append((byte >> shift) & 1)

    n_bits = len(bits)
    if n_bits > total_channels:
        raise ValueError(
            f"Key too large: {len(key_bytes)} bytes = {n_bits} bits, "
            f"but image only has {total_channels} channels. "
            f"Use a larger image (e.g. 128×128 RGB for up to 6144 bytes)."
        )

    flat = arr.flatten()

    # Embed: clear LSB, set to key bit
    for i, bit in enumerate(bits):
        flat[i] = (flat[i] & 0xFE) | bit

    result_arr = flat.reshape(arr.shape)
    result_img = Image.fromarray(result_arr, mode="RGB")

    if verify:
        recovered = recover_key(result_img, len(key_bytes))
        if recovered != key_bytes:
            mismatches = sum(a != b for a, b in zip(recovered, key_bytes))
            raise RuntimeError(
                f"LSB verification FAILED: {mismatches}/{len(key_bytes)} bytes differ. "
                "This is a critical error — encryption key integrity compromised."
            )

    return result_img


# ---------------------------------------------------------------------------
# Core LSB recover
# ---------------------------------------------------------------------------

def recover_key(image: Image.Image, key_length_bytes: int) -> bytes:
    """
    Read back key bytes from the LSBs of a stego image.

    Parameters
    ----------
    image            : PIL Image with embedded key
    key_length_bytes : exact number of bytes to recover

    Returns
    -------
    Recovered bytes (identical to original if unmodified)
    """
    arr = np.array(image.convert("RGB"), dtype=np.uint8)
    flat = arr.flatten()

    n_bits = key_length_bytes * 8
    if n_bits > len(flat):
        raise ValueError(
            f"Cannot recover {key_length_bytes} bytes from image with "
            f"only {len(flat) // 8} byte capacity."
        )

    lsbs = flat[:n_bits] & 1  # Extract LSBs

    # Pack bits into bytes (MSB first)
    result = bytearray()
    for i in range(0, n_bits, 8):
        byte_bits = lsbs[i:i + 8]
        byte_val = 0
        for bit in byte_bits:
            byte_val = (byte_val << 1) | int(bit)
        result.append(byte_val)

    return bytes(result)


# ---------------------------------------------------------------------------
# Key metadata header
# ---------------------------------------------------------------------------

HEADER_MAGIC   = b"QKEY"
HEADER_VERSION = 1
HEADER_SIZE    = 16  # bytes


def _build_header(key_length: int, job_id: str) -> bytes:
    """
    Build a 16-byte metadata header embedded before the key bytes.

    Format:
      4 bytes  — magic b"QKEY"
      1 byte   — version (1)
      3 bytes  — padding (0x00)
      4 bytes  — key length (uint32 big-endian)
      4 bytes  — CRC32 of job_id[:8]
    """
    import zlib
    crc = zlib.crc32(job_id[:8].encode() if job_id else b"SIMJOBID") & 0xFFFFFFFF
    header = (
        HEADER_MAGIC +
        bytes([HEADER_VERSION, 0, 0, 0]) +
        struct.pack(">I", key_length) +
        struct.pack(">I", crc)
    )
    assert len(header) == HEADER_SIZE
    return header


def _parse_header(header_bytes: bytes) -> dict:
    if header_bytes[:4] != HEADER_MAGIC:
        raise ValueError("Invalid QKEY header magic — image may not contain an embedded key.")
    version     = header_bytes[4]
    key_length  = struct.unpack(">I", header_bytes[8:12])[0]
    header_crc  = struct.unpack(">I", header_bytes[12:16])[0]
    return {"version": version, "key_length": key_length, "crc": header_crc}


def embed_key_with_header(
    image: Image.Image,
    key_bytes: bytes,
    job_id: str = "UNKNOWN",
) -> Image.Image:
    """
    Embed key with a 16-byte header so recovery doesn't need to know key length.
    Total embedded data = HEADER_SIZE + len(key_bytes).
    """
    header = _build_header(len(key_bytes), job_id)
    payload = header + key_bytes
    return embed_key(image, payload, verify=True)


def recover_key_from_header(image: Image.Image) -> dict:
    """
    Recover key from a headered stego image without knowing key length in advance.

    Returns
    -------
    dict:
      key_bytes  : the recovered key
      key_length : int
      version    : int
      valid      : bool
    """
    header_raw = recover_key(image, HEADER_SIZE)
    meta = _parse_header(header_raw)
    key_length = meta["key_length"]

    all_payload = recover_key(image, HEADER_SIZE + key_length)
    key_bytes = all_payload[HEADER_SIZE:]

    return {
        "key_bytes":  key_bytes,
        "key_length": key_length,
        "version":    meta["version"],
        "valid":      True,
    }


# ---------------------------------------------------------------------------
# Difference analysis (for demonstrating invisibility)
# ---------------------------------------------------------------------------

def stego_diff_stats(original: Image.Image, stego: Image.Image) -> dict:
    """
    Compute statistics on pixel changes introduced by LSB embedding.

    Returns
    -------
    dict with max_change, mean_change, changed_pixels_pct, psnr
    """
    orig_arr  = np.array(original.convert("RGB"), dtype=np.int16)
    stego_arr = np.array(stego.convert("RGB"),    dtype=np.int16)
    diff      = np.abs(orig_arr - stego_arr)

    n_pixels = orig_arr.shape[0] * orig_arr.shape[1]
    changed  = np.any(diff > 0, axis=2).sum()

    mse = ((diff.astype(np.float64)) ** 2).mean()
    psnr = 10 * np.log10(255**2 / mse) if mse > 0 else float("inf")

    return {
        "max_change":          int(diff.max()),
        "mean_change":         float(diff.mean()),
        "changed_pixels_pct":  float(changed / n_pixels * 100),
        "psnr_db":             float(psnr),
        "note": (
            "Max change = 1 (invisible). "
            f"PSNR = {psnr:.1f} dB (>40 dB = imperceptible to humans)."
            if diff.max() <= 1 else
            f"Unexpected change > 1: {diff.max()}. Check implementation."
        ),
    }


# ---------------------------------------------------------------------------
# CLI demo + round-trip verification
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from mock_bitstream import generate_mock_bitstream
    from pixel_mapper import map_bits_to_image
    from style_transfer import apply_style

    # Generate quantum noise → noise image
    result      = generate_mock_bitstream(n_bits=64 * 64 * 24)
    noise_img   = map_bits_to_image(result, strategy="direct_rgb", width=64, height=64)
    key_bytes   = result.bytes_data[:512]  # Use first 512 bytes as example key

    print("=== Steganography Round-Trip Test ===")
    print(capacity_summary(noise_img))

    # Apply style transfer first (the hard case)
    styled = apply_style(noise_img, "Cosmic Nebula", mode="colormap")
    print(f"Style applied. Original size: {noise_img.size}, Styled: {styled.size}")

    # Embed key into styled image
    stego = embed_key_with_header(styled, key_bytes, job_id=result.job_id)
    stego.save("gallery/stego_demo.png")

    # Recover
    recovered = recover_key_from_header(stego)
    match = recovered["key_bytes"] == key_bytes
    print(f"Key recovery: {'✓ PASS' if match else '✗ FAIL'}  "
          f"({recovered['key_length']} bytes)")

    # Diff stats
    stats = stego_diff_stats(styled, stego)
    print(f"Max pixel change: {stats['max_change']}  "
          f"Changed pixels: {stats['changed_pixels_pct']:.1f}%  "
          f"PSNR: {stats['psnr_db']:.1f} dB")
    print(f"Note: {stats['note']}")

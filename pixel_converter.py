# ════════════════════════════════════════════════════════════════════
# FILE: pixel_converter.py
# PURPOSE: Pure data-conversion layer — maps raw quantum byte streams
#          to image pixel arrays and back.  Contains NO quantum code;
#          operates entirely on bytes, NumPy arrays, and PIL images.
#          The roundtrip guarantee (bytes → image → bytes ≡ identity)
#          is critical for OTP key recovery in Part 2.
# AUTHOR: Quantum Layer Team — Part 1 of 4
# ════════════════════════════════════════════════════════════════════

from __future__ import annotations

import numpy as np
from PIL import Image

# Channel count lookup for supported colour modes.
_CHANNELS: dict[str, int] = {'L': 1, 'RGB': 3, 'RGBA': 4}


class PixelConverter:
    """Stateless converter between byte streams and image pixel arrays.

    Every method is a classmethod or staticmethod — no instance state.
    The class groups related conversion functions under a single
    namespace for clean imports.
    """

    # ── Bytes → NumPy array ───────────────────────────────────────
    @staticmethod
    def to_array(
        bytes_data: bytes,
        width: int,
        height: int,
        color_mode: str = 'RGB',
    ) -> np.ndarray:
        """Convert raw bytes into a shaped pixel array.

        Args:
            bytes_data: Raw byte sequence (e.g. from BitStreamResult.bytes_data).
            width: Image width in pixels.
            height: Image height in pixels.
            color_mode: 'L' (grayscale), 'RGB', or 'RGBA'.

        Returns:
            NumPy uint8 array shaped (H, W) for L or (H, W, C) for colour.

        Raises:
            ValueError: If *color_mode* is unsupported or bytes are too few.
        """
        if color_mode not in _CHANNELS:
            raise ValueError(
                f"Unsupported color_mode '{color_mode}'. "
                f"Choose from: {', '.join(sorted(_CHANNELS))}"
            )
        channels = _CHANNELS[color_mode]
        needed = width * height * channels
        if len(bytes_data) < needed:
            raise ValueError(
                f"Need {needed} bytes for {width}×{height} {color_mode} image, "
                f"but got only {len(bytes_data)}."
            )
        # Slice to exact length (discard any surplus padding)
        pixel_bytes = bytes_data[:needed]
        arr = np.frombuffer(pixel_bytes, dtype=np.uint8).copy()
        if channels == 1:
            return arr.reshape((height, width))
        return arr.reshape((height, width, channels))

    # ── Bytes → PIL Image ─────────────────────────────────────────
    @staticmethod
    def to_pil_image(
        bytes_data: bytes,
        width: int,
        height: int,
        color_mode: str = 'RGB',
    ) -> Image.Image:
        """Convert raw bytes into a PIL Image.

        Args:
            bytes_data: Raw byte sequence.
            width: Image width.
            height: Image height.
            color_mode: 'L', 'RGB', or 'RGBA'.

        Returns:
            A PIL Image instance in the requested mode.
        """
        arr = PixelConverter.to_array(bytes_data, width, height, color_mode)
        return Image.fromarray(arr, mode=color_mode)

    # ── Bytes → HSV → RGB PIL Image ──────────────────────────────
    @staticmethod
    def to_hsv_image(
        bytes_data: bytes,
        width: int,
        height: int,
    ) -> Image.Image:
        """Map bytes into HSV colour space for vivid art output.

        Splits the byte stream into three equal segments used as
        Hue (0-179 for OpenCV compatibility), Saturation, and Value
        channels.  The resulting HSV array is converted to an RGB PIL
        Image so it can be displayed without an OpenCV dependency.

        Args:
            bytes_data: Raw byte sequence (≥ width×height×3 bytes).
            width: Image width.
            height: Image height.

        Returns:
            RGB PIL Image derived from HSV mapping.
        """
        n_pixels = width * height
        needed = n_pixels * 3
        if len(bytes_data) < needed:
            raise ValueError(
                f"Need {needed} bytes for {width}×{height} HSV image, "
                f"but got only {len(bytes_data)}."
            )

        raw = np.frombuffer(bytes_data[:needed], dtype=np.uint8).copy()
        # Partition into three channels
        h_raw = raw[:n_pixels]
        s_raw = raw[n_pixels : 2 * n_pixels]
        v_raw = raw[2 * n_pixels : 3 * n_pixels]

        # Scale hue to 0-179 (OpenCV convention) — keeps full colour wheel
        h_chan = (h_raw.astype(np.float32) * 179.0 / 255.0).astype(np.uint8)
        s_chan = s_raw
        v_chan = v_raw

        # Stack into (H, W, 3) HSV image
        hsv = np.stack(
            [
                h_chan.reshape(height, width),
                s_chan.reshape(height, width),
                v_chan.reshape(height, width),
            ],
            axis=-1,
        )

        # Manual HSV → RGB conversion (avoids OpenCV dependency)
        h_f = hsv[:, :, 0].astype(np.float32) / 179.0 * 360.0  # degrees
        s_f = hsv[:, :, 1].astype(np.float32) / 255.0
        v_f = hsv[:, :, 2].astype(np.float32) / 255.0

        c = v_f * s_f
        h_prime = h_f / 60.0
        x = c * (1 - np.abs(h_prime % 2 - 1))
        m = v_f - c

        # Sector lookup
        rgb = np.zeros((height, width, 3), dtype=np.float32)
        for sector in range(6):
            mask = (h_prime >= sector) & (h_prime < sector + 1)
            if sector == 0:
                rgb[mask] = np.stack([c[mask], x[mask], np.zeros_like(c[mask])], axis=-1)
            elif sector == 1:
                rgb[mask] = np.stack([x[mask], c[mask], np.zeros_like(c[mask])], axis=-1)
            elif sector == 2:
                rgb[mask] = np.stack([np.zeros_like(c[mask]), c[mask], x[mask]], axis=-1)
            elif sector == 3:
                rgb[mask] = np.stack([np.zeros_like(c[mask]), x[mask], c[mask]], axis=-1)
            elif sector == 4:
                rgb[mask] = np.stack([x[mask], np.zeros_like(c[mask]), c[mask]], axis=-1)
            else:
                rgb[mask] = np.stack([c[mask], np.zeros_like(c[mask]), x[mask]], axis=-1)

        rgb_final = ((rgb + m[:, :, np.newaxis]) * 255).clip(0, 255).astype(np.uint8)
        return Image.fromarray(rgb_final, mode='RGB')

    # ── PIL Image → bytes (key recovery) ─────────────────────────
    @staticmethod
    def from_image(image: Image.Image) -> bytes:
        """Reconstruct the exact byte stream from a PIL Image.

        **CRITICAL** for Part 2 (Cryptography): the decryption side
        must recover the identical OTP key bytes that were used for
        encryption.  This function is the inverse of ``to_pil_image``.

        Args:
            image: A PIL Image previously created by ``to_pil_image``.

        Returns:
            The raw byte sequence recovered from pixel values.
        """
        return np.array(image).flatten().tobytes()

    # ── Roundtrip integrity check ─────────────────────────────────
    @staticmethod
    def verify_roundtrip(
        bytes_data: bytes,
        width: int,
        height: int,
        color_mode: str = 'RGB',
    ) -> bool:
        """Verify that bytes → image → bytes is lossless.

        Args:
            bytes_data: Original byte stream.
            width: Image width.
            height: Image height.
            color_mode: Colour mode string.

        Returns:
            *True* if recovered bytes exactly match the original.
        """
        channels = _CHANNELS.get(color_mode, 3)
        needed = width * height * channels
        # Only compare the bytes that actually become pixels
        original_slice = bytes_data[:needed]
        img = PixelConverter.to_pil_image(bytes_data, width, height, color_mode)
        recovered = PixelConverter.from_image(img)
        return original_slice == recovered

    # ── Channel statistics ────────────────────────────────────────
    @staticmethod
    def get_channel_stats(array: np.ndarray) -> dict:
        """Compute per-channel statistics of a pixel array.

        Args:
            array: NumPy uint8 pixel array from ``to_array``.

        Returns:
            Dict with 'mean', 'std', 'min', 'max', and 'histogram'
            (256-bin count list).
        """
        flat = array.flatten().astype(np.float64)
        histogram, _ = np.histogram(array.flatten(), bins=256, range=(0, 256))
        return {
            'mean': float(np.mean(flat)),
            'std': float(np.std(flat)),
            'min': int(np.min(array)),
            'max': int(np.max(array)),
            'histogram': histogram.tolist(),
        }

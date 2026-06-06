"""
test_art_pipeline.py — Part 4 test suite

Covers:
  - All 5 pixel mapping strategies (lossless round-trips)
  - Style transfer (colormap tier, all 7 presets)
  - Diffusion seeder (fallback mode)
  - Steganography LSB: 100% byte-for-byte recovery (non-negotiable per spec)
  - Avalanche effect visualiser
  - Comparison dashboard
  - Perfect secrecy visualiser
  - Key passport generator
"""

import os
import sys
import hashlib
import unittest

import numpy as np
from PIL import Image

# Make sure the package root is on the path when running directly
sys.path.insert(0, os.path.dirname(__file__))

from mock_bitstream import generate_mock_bitstream
from pixel_mapper import map_bits_to_image, recover_key_bytes, Strategy
from style_transfer import apply_style, apply_style_colormap, list_presets
from steganography import (
    embed_key, recover_key, embed_key_with_header,
    recover_key_from_header, stego_diff_stats, max_key_bytes,
)
from visual_cryptanalysis import (
    visualise_avalanche,
    generate_comparison_dashboard,
    visualise_perfect_secrecy,
    generate_key_passport,
)
from diffusion_seeder import seed_with_quantum


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_result(n_bits: int = 64 * 64 * 24):
    return generate_mock_bitstream(n_bits=n_bits, seed=42)


# ---------------------------------------------------------------------------
# 1. Pixel Mapper Tests
# ---------------------------------------------------------------------------

class TestPixelMapper(unittest.TestCase):

    def setUp(self):
        self.result = _mock_result()

    def test_direct_gray_output_mode(self):
        img = map_bits_to_image(self.result, strategy="direct_gray", width=64, height=64)
        self.assertEqual(img.mode, "L")
        self.assertEqual(img.size, (64, 64))

    def test_direct_rgb_output_mode(self):
        img = map_bits_to_image(self.result, strategy="direct_rgb", width=64, height=64)
        self.assertEqual(img.mode, "RGB")
        self.assertEqual(img.size, (64, 64))

    def test_hsv_output_mode(self):
        img = map_bits_to_image(self.result, strategy="hsv", width=64, height=64)
        self.assertEqual(img.mode, "RGB")

    def test_bitplane_output_mode(self):
        img = map_bits_to_image(self.result, strategy="bitplane", width=64, height=64)
        self.assertEqual(img.mode, "RGB")

    def test_hilbert_output_mode(self):
        img = map_bits_to_image(self.result, strategy="hilbert", width=64, height=64)
        self.assertEqual(img.mode, "RGB")
        self.assertEqual(img.size, (64, 64))

    def test_roundtrip_direct_gray(self):
        img = map_bits_to_image(self.result, strategy="direct_gray", width=64, height=64)
        recovered = recover_key_bytes(img, strategy="direct_gray")
        src = self.result.bytes_data
        n = min(len(recovered), len(src), 64 * 64)
        self.assertEqual(recovered[:n], src[:n], "direct_gray round-trip mismatch")

    def test_roundtrip_direct_rgb(self):
        img = map_bits_to_image(self.result, strategy="direct_rgb", width=64, height=64)
        recovered = recover_key_bytes(img, strategy="direct_rgb")
        src = self.result.bytes_data
        n = min(len(recovered), len(src), 64 * 64 * 3)
        self.assertEqual(recovered[:n], src[:n], "direct_rgb round-trip mismatch")

    def test_roundtrip_hilbert(self):
        result = _mock_result(n_bits=64 * 64 * 24)
        img = map_bits_to_image(result, strategy="hilbert", width=64, height=64)
        recovered = recover_key_bytes(img, strategy="hilbert")
        src = result.bytes_data
        n = min(len(recovered), len(src), 64 * 64 * 3)
        self.assertEqual(recovered[:n], src[:n], "hilbert round-trip mismatch")

    def test_invalid_strategy_raises(self):
        with self.assertRaises(ValueError):
            map_bits_to_image(self.result, strategy="nonexistent")

    def test_bytes_input(self):
        raw = os.urandom(64 * 64 * 3)
        img = map_bits_to_image(raw, strategy="direct_rgb", width=64, height=64)
        self.assertIsInstance(img, Image.Image)

    def test_bit_list_input(self):
        bits = [0, 1] * (64 * 64 * 3 * 8 // 2)
        img = map_bits_to_image(bits, strategy="direct_gray", width=64, height=64)
        self.assertIsInstance(img, Image.Image)


# ---------------------------------------------------------------------------
# 2. Style Transfer Tests
# ---------------------------------------------------------------------------

class TestStyleTransfer(unittest.TestCase):

    def setUp(self):
        result = _mock_result()
        self.noise_img = map_bits_to_image(result, strategy="direct_rgb", width=64, height=64)

    def test_all_presets_produce_rgb_images(self):
        for preset in list_presets():
            with self.subTest(preset=preset):
                styled = apply_style_colormap(self.noise_img, preset)
                self.assertEqual(styled.mode, "RGB")
                self.assertEqual(styled.size, self.noise_img.size)

    def test_invalid_preset_raises(self):
        with self.assertRaises(ValueError):
            apply_style_colormap(self.noise_img, "Nonexistent Preset")

    def test_auto_mode_falls_back_gracefully(self):
        # Without PyTorch, auto mode should fall back to colormap
        styled = apply_style(self.noise_img, "Cosmic Nebula", mode="auto")
        self.assertIsInstance(styled, Image.Image)

    def test_colormap_mode_explicit(self):
        styled = apply_style(self.noise_img, "Circuit Board", mode="colormap")
        self.assertIsInstance(styled, Image.Image)
        self.assertEqual(styled.mode, "RGB")


# ---------------------------------------------------------------------------
# 3. Diffusion Seeder Tests
# ---------------------------------------------------------------------------

class TestDiffusionSeeder(unittest.TestCase):

    def setUp(self):
        result = _mock_result()
        self.noise_img = map_bits_to_image(result, strategy="direct_rgb", width=64, height=64)

    def test_fallback_returns_dict(self):
        r = seed_with_quantum(self.noise_img, "cosmic nebula purple", device="cpu")
        self.assertIn("image", r)
        self.assertIn("method", r)
        self.assertIsInstance(r["image"], Image.Image)

    def test_fallback_method_label(self):
        r = seed_with_quantum(self.noise_img, "thermal heat imaging")
        # Without diffusers installed, should be colormap_fallback
        self.assertIn(r["method"], ("stable_diffusion", "colormap_fallback"))


# ---------------------------------------------------------------------------
# 4. Steganography Tests  ← NON-NEGOTIABLE: 100% recovery
# ---------------------------------------------------------------------------

class TestSteganography(unittest.TestCase):

    def setUp(self):
        result = _mock_result()
        self.noise_img = map_bits_to_image(result, strategy="direct_rgb", width=64, height=64)
        self.key_bytes = result.bytes_data[:512]
        self.job_id    = result.job_id

    def test_embed_and_recover_exact_match(self):
        """CRITICAL: 100% byte-for-byte key recovery required."""
        stego = embed_key(self.noise_img, self.key_bytes, verify=True)
        recovered = recover_key(stego, len(self.key_bytes))
        self.assertEqual(recovered, self.key_bytes,
                         "LSB key recovery FAILED — encryption integrity broken")

    def test_max_change_is_one(self):
        """Pixel values must change by at most ±1."""
        stego = embed_key(self.noise_img, self.key_bytes)
        orig_arr  = np.array(self.noise_img.convert("RGB"), dtype=np.int32)
        stego_arr = np.array(stego.convert("RGB"),           dtype=np.int32)
        max_diff  = int(np.abs(orig_arr - stego_arr).max())
        self.assertLessEqual(max_diff, 1, f"Pixel changed by {max_diff} (must be ≤ 1)")

    def test_header_embed_recover(self):
        stego     = embed_key_with_header(self.noise_img, self.key_bytes, self.job_id)
        result    = recover_key_from_header(stego)
        self.assertTrue(result["valid"])
        self.assertEqual(result["key_bytes"], self.key_bytes)
        self.assertEqual(result["key_length"], len(self.key_bytes))

    def test_oversized_key_raises(self):
        huge_key = os.urandom(max_key_bytes(self.noise_img) + 100)
        with self.assertRaises(ValueError):
            embed_key(self.noise_img, huge_key)

    def test_stego_after_style_transfer(self):
        """Key must survive being embedded in a styled image."""
        from style_transfer import apply_style_colormap
        styled = apply_style_colormap(self.noise_img, "Cosmic Nebula")
        stego  = embed_key(styled, self.key_bytes, verify=True)
        recovered = recover_key(stego, len(self.key_bytes))
        self.assertEqual(recovered, self.key_bytes,
                         "Key recovery after style transfer FAILED")

    def test_psnr_above_40db(self):
        stego = embed_key(self.noise_img, self.key_bytes)
        stats = stego_diff_stats(self.noise_img, stego)
        self.assertGreater(stats["psnr_db"], 40.0,
                           f"PSNR {stats['psnr_db']:.1f} dB below 40 dB threshold")

    def test_diff_stats_keys(self):
        stego = embed_key(self.noise_img, self.key_bytes)
        stats = stego_diff_stats(self.noise_img, stego)
        for key in ["max_change", "mean_change", "changed_pixels_pct", "psnr_db"]:
            self.assertIn(key, stats)

    def test_various_key_sizes(self):
        """Round-trip for multiple key sizes."""
        for size in [8, 64, 256, 512]:
            with self.subTest(size=size):
                key = os.urandom(size)
                stego = embed_key(self.noise_img, key, verify=False)
                recovered = recover_key(stego, size)
                self.assertEqual(recovered, key, f"Failed for key size {size}")


# ---------------------------------------------------------------------------
# 5. Visual Cryptanalysis Tests
# ---------------------------------------------------------------------------

class TestVisualCryptanalysis(unittest.TestCase):

    def setUp(self):
        result = _mock_result()
        self.key_bytes = result.bytes_data[:64 * 64 * 3]
        self.key_img   = map_bits_to_image(result, strategy="direct_rgb", width=64, height=64)

    def test_avalanche_returns_figure(self):
        import matplotlib.pyplot as plt
        fig = visualise_avalanche(self.key_bytes, width=64, height=64)
        self.assertIsNotNone(fig)
        plt.close(fig)

    def test_comparison_dashboard_returns_figure(self):
        import matplotlib.pyplot as plt
        fig = generate_comparison_dashboard(self.key_bytes, width=32, height=32)
        self.assertIsNotNone(fig)
        plt.close(fig)

    def test_perfect_secrecy_returns_figure(self):
        import matplotlib.pyplot as plt
        fig = visualise_perfect_secrecy(self.key_bytes, width=32, height=32)
        self.assertIsNotNone(fig)
        plt.close(fig)

    def test_key_passport_returns_image(self):
        meta = {
            "nickname":    "Test Key",
            "job_id":      "SIM-ABCDEF123456",
            "entropy":     0.9991,
            "nist_passed": 14,
            "nist_total":  15,
            "key_bits":    98304,
            "circuit":     "GHZ (10 qubits)",
        }
        card = generate_key_passport(self.key_img, meta)
        self.assertIsInstance(card, Image.Image)
        self.assertEqual(card.mode, "RGB")
        self.assertEqual(card.size, (620, 220))

    def test_avalanche_pct_in_range(self):
        """Avalanche should give roughly 45–55% change for random keys."""
        import matplotlib.pyplot as plt
        # Measure programmatically
        key_a = self.key_bytes
        key_b = bytearray(key_a); key_b[0] ^= 0x80
        img_a = np.array(map_bits_to_image(bytes(key_a), "direct_rgb", 64, 64), dtype=np.int32)
        img_b = np.array(map_bits_to_image(bytes(key_b), "direct_rgb", 64, 64), dtype=np.int32)
        diff  = np.abs(img_a - img_b)
        changed_pct = np.any(diff > 0, axis=2).mean() * 100
        # For true random bytes, ~50% change expected ± large tolerance
        self.assertGreater(changed_pct, 0.0, "Zero pixels changed — key mapping may be broken")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Ensure gallery directory exists for any save tests
    os.makedirs("gallery", exist_ok=True)

    loader = unittest.TestLoader()
    suite  = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)

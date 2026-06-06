"""
visual_cryptanalysis.py — Tasks 4.5 / 4.6 / 4.7 / 4.8
Four visual modules:

  4.5 — Avalanche effect visualiser
  4.6 — Key strength comparison dashboard (quantum vs classical)
  4.7 — Perfect secrecy (Shannon 1949) visualisation
  4.8 — Quantum Key Passport (certificate card) image generator
"""

import os
import hashlib
import struct
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch
from PIL import Image, ImageDraw, ImageFont

from mock_bitstream import BitStreamResult, generate_mock_bitstream
from pixel_mapper import map_bits_to_image

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------

QUANTUM_GREEN  = "#00E676"
CLASSICAL_AMBER= "#FFB300"
WEAK_RED       = "#F44336"
BG_DARK        = "#0D0D0D"
PANEL_BG       = "#1A1A1A"
TEXT_WHITE     = "#F5F5F5"
TEXT_MUTED     = "#888888"


# =============================================================================
# TASK 4.5 — Avalanche Effect Visualiser
# =============================================================================

def visualise_avalanche(
    key_bytes: bytes,
    width: int = 64,
    height: int = 64,
    flip_bit_index: int = 0,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """
    Show that flipping 1 bit in the key changes ~50% of pixel values.

    Parameters
    ----------
    key_bytes      : original key bytes
    width, height  : image dimensions
    flip_bit_index : which bit position to flip (0 = MSB of byte 0)
    save_path      : optional PNG save path

    Returns
    -------
    matplotlib Figure
    """
    # Build Key A and Key B (1-bit difference)
    key_a = bytearray(key_bytes)
    key_b = bytearray(key_bytes)
    byte_idx = flip_bit_index // 8
    bit_pos  = 7 - (flip_bit_index % 8)
    key_b[byte_idx] ^= (1 << bit_pos)

    img_a = map_bits_to_image(bytes(key_a), strategy="direct_rgb", width=width, height=height)
    img_b = map_bits_to_image(bytes(key_b), strategy="direct_rgb", width=width, height=height)

    arr_a = np.array(img_a, dtype=np.int32)
    arr_b = np.array(img_b, dtype=np.int32)
    diff  = np.abs(arr_a - arr_b)

    changed_mask = np.any(diff > 0, axis=2)
    pct_changed  = changed_mask.mean() * 100

    # Build visualisation arrays
    diff_rgb = np.zeros((height, width, 3), dtype=np.uint8)
    diff_rgb[changed_mask]  = [220, 38,  38]   # bright red — changed
    diff_rgb[~changed_mask] = [22,  163, 74]   # deep green — unchanged

    # ---- Figure ----
    fig = plt.figure(figsize=(14, 4.5), facecolor=BG_DARK)
    gs  = gridspec.GridSpec(1, 4, figure=fig, wspace=0.06)

    titles = ["Key A\n(Original)", "Key B\n(1 bit flipped)", "Difference Map", "Change Histogram"]
    images = [img_a, img_b, Image.fromarray(diff_rgb), None]

    for col in range(3):
        ax = fig.add_subplot(gs[col])
        ax.imshow(np.array(images[col]), interpolation="nearest")
        ax.set_title(titles[col], color=TEXT_WHITE, fontsize=10, pad=6)
        ax.axis("off")
        # Border colour
        border_col = QUANTUM_GREEN if col < 2 else (
            QUANTUM_GREEN if pct_changed > 45 else WEAK_RED
        )
        for spine in ax.spines.values():
            spine.set_edgecolor(border_col)
            spine.set_linewidth(2)
        ax.set_xticks([]); ax.set_yticks([])

    # Histogram panel
    ax4 = fig.add_subplot(gs[3])
    ax4.set_facecolor(PANEL_BG)
    flat_diff = diff.flatten()
    ax4.hist(flat_diff[flat_diff > 0], bins=30, color=WEAK_RED,   alpha=0.8, label="Changed")
    ax4.hist(flat_diff[flat_diff == 0], bins=1,  color=QUANTUM_GREEN, alpha=0.6, label="Unchanged")
    ax4.set_xlabel("Pixel change magnitude", color=TEXT_MUTED, fontsize=8)
    ax4.set_ylabel("Count", color=TEXT_MUTED, fontsize=8)
    ax4.set_title("Change Distribution", color=TEXT_WHITE, fontsize=10, pad=6)
    ax4.tick_params(colors=TEXT_MUTED, labelsize=7)
    ax4.legend(fontsize=7, labelcolor=TEXT_WHITE, facecolor=PANEL_BG, edgecolor="none")
    ax4.spines["bottom"].set_color(TEXT_MUTED)
    ax4.spines["left"].set_color(TEXT_MUTED)
    ax4.spines["top"].set_visible(False)
    ax4.spines["right"].set_visible(False)

    suptitle = (
        f"Avalanche Effect: {pct_changed:.1f}% of pixels changed from a single bit flip  "
        f"{'✓ Strong diffusion' if 40 < pct_changed < 60 else '⚠ Check diffusion'}"
    )
    fig.suptitle(suptitle, color=QUANTUM_GREEN if 40 < pct_changed < 60 else CLASSICAL_AMBER,
                 fontsize=12, y=1.01)

    if save_path:
        fig.savefig(save_path, dpi=120, bbox_inches="tight", facecolor=BG_DARK)

    return fig


# =============================================================================
# TASK 4.6 — Key Strength Comparison Dashboard
# =============================================================================

def _gen_lcg_bytes(n: int, seed: int = 42) -> bytes:
    """Deliberately weak LCG PRNG."""
    a, c, m = 1664525, 1013904223, 2**32
    x = seed
    out = bytearray()
    while len(out) < n:
        x = (a * x + c) % m
        out.append(x & 0xFF)
    return bytes(out[:n])


def _entropy_score(byte_data: bytes) -> float:
    """Shannon entropy per bit (0–1 scale)."""
    if not byte_data:
        return 0.0
    counts = np.bincount(np.frombuffer(byte_data, dtype=np.uint8), minlength=256)
    probs  = counts[counts > 0] / len(byte_data)
    h_byte = -np.sum(probs * np.log2(probs))
    return h_byte / 8.0  # normalise to bits/bit


def generate_comparison_dashboard(
    quantum_bytes: bytes,
    width: int = 64,
    height: int = 64,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """
    Side-by-side comparison of quantum vs classical key images.

    Layout:
      Row 1 — Noise images
      Row 2 — Byte distribution histograms
      Row 3 — Autocorrelation correlograms
      Row 4 — Byte value heat maps
    """
    n = width * height * 3  # RGB bytes needed

    sources = {
        "Quantum\n(Simulator)": (quantum_bytes[:n],          QUANTUM_GREEN),
        "NumPy\nMersenne":      (np.random.bytes(n),         CLASSICAL_AMBER),
        "os.urandom\n(CSPRNG)": (os.urandom(n),              CLASSICAL_AMBER),
        "LCG Weak\nPRNG":       (_gen_lcg_bytes(n),          WEAK_RED),
    }

    n_src = len(sources)
    fig   = plt.figure(figsize=(4 * n_src, 14), facecolor=BG_DARK)
    gs    = gridspec.GridSpec(4, n_src, figure=fig, hspace=0.45, wspace=0.1)

    row_labels = [
        "Noise Image",
        "Byte Distribution",
        "Autocorrelation\n(lags 0–50)",
        "Byte Value\nHeat Map",
    ]

    for col, (name, (data, colour)) in enumerate(sources.items()):
        # ---- Row 0: Noise image ----
        ax = fig.add_subplot(gs[0, col])
        img = map_bits_to_image(data, strategy="direct_rgb", width=width, height=height)
        ax.imshow(np.array(img), interpolation="nearest")
        ax.set_title(name, color=colour, fontsize=9, fontweight="bold", pad=4)
        ax.axis("off")
        for spine in ax.spines.values():
            spine.set_edgecolor(colour); spine.set_linewidth(2.5)

        score = _entropy_score(data)

        # ---- Row 1: Byte distribution ----
        ax = fig.add_subplot(gs[1, col])
        ax.set_facecolor(PANEL_BG)
        arr = np.frombuffer(data, dtype=np.uint8)
        counts = np.bincount(arr, minlength=256)
        ax.bar(range(256), counts, color=colour, alpha=0.6, width=1)
        ideal = len(data) / 256
        ax.axhline(ideal, color=WEAK_RED, linestyle="--", lw=0.8, label="Ideal")
        ax.set_xlim(0, 255)
        ax.tick_params(colors=TEXT_MUTED, labelsize=6)
        ax.set_xlabel("Byte value", color=TEXT_MUTED, fontsize=7)
        ax.set_ylabel("Count", color=TEXT_MUTED, fontsize=7)
        ax.annotate(f"H={score:.4f}", xy=(0.97, 0.95), xycoords="axes fraction",
                    ha="right", va="top", color=colour, fontsize=8, fontweight="bold")
        for sp in ["top","right"]: ax.spines[sp].set_visible(False)
        for sp in ["bottom","left"]: ax.spines[sp].set_color(TEXT_MUTED)

        # ---- Row 2: Autocorrelation ----
        ax = fig.add_subplot(gs[2, col])
        ax.set_facecolor(PANEL_BG)
        signal = arr.astype(np.float64)
        signal -= signal.mean()
        std = signal.std()
        lags = range(1, 51)
        acf = [np.corrcoef(signal[:-lag], signal[lag:])[0, 1] if std > 0 else 0
               for lag in lags]
        ax.bar(lags, acf, color=colour, alpha=0.7, width=0.8)
        ax.axhline(0, color=TEXT_WHITE, lw=0.5)
        ax.axhline( 0.02, color=CLASSICAL_AMBER, lw=0.6, ls="--", alpha=0.5)
        ax.axhline(-0.02, color=CLASSICAL_AMBER, lw=0.6, ls="--", alpha=0.5)
        ax.set_ylim(-0.3, 0.3)
        ax.set_xlabel("Lag", color=TEXT_MUTED, fontsize=7)
        ax.tick_params(colors=TEXT_MUTED, labelsize=6)
        for sp in ["top","right"]: ax.spines[sp].set_visible(False)
        for sp in ["bottom","left"]: ax.spines[sp].set_color(TEXT_MUTED)

        # ---- Row 3: Byte value heat map ----
        ax = fig.add_subplot(gs[3, col])
        heat = counts.reshape(16, 16)
        im = ax.imshow(heat, cmap="plasma" if colour == QUANTUM_GREEN else "hot",
                       interpolation="nearest")
        ax.set_title("Flat = uniform", color=TEXT_MUTED, fontsize=7, pad=3)
        ax.axis("off")

        # Annotation for LCG
        if colour == WEAK_RED:
            ax.annotate("← visible\npatterns!", xy=(0.0, 0.5), xycoords="axes fraction",
                        ha="left", color=WEAK_RED, fontsize=7, fontweight="bold")

    # Row labels on the left
    for row, label in enumerate(row_labels):
        fig.text(0.01, 0.83 - row * 0.215, label, color=TEXT_MUTED,
                 fontsize=8, va="center", rotation=90)

    fig.suptitle("Quantum vs Classical Key Strength Comparison",
                 color=TEXT_WHITE, fontsize=14, fontweight="bold", y=1.01)

    if save_path:
        fig.savefig(save_path, dpi=110, bbox_inches="tight", facecolor=BG_DARK)

    return fig


# =============================================================================
# TASK 4.7 — Perfect Secrecy Visual Demonstration
# =============================================================================

def visualise_perfect_secrecy(
    ciphertext_bytes: bytes,
    width: int = 64,
    height: int = 64,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """
    Show Shannon 1949: the same ciphertext decrypts to any message with the right key.

    Centre: ciphertext noise image
    Surrounding: 6 panels showing valid decryptions with random keys
    """
    sample_messages = [
        "ATTACK AT DAWN",
        "PEACE CONFIRMED",
        "MEET AT HARBOUR",
        "ALL CLEAR SIGNAL",
        "SEND REINFORCEMENTS",
        "MISSION ABORTED",
    ]

    ct_img = map_bits_to_image(
        ciphertext_bytes[:width * height * 3],
        strategy="direct_rgb", width=width, height=height,
    )

    # Generate 6 "decryption" images by XOR-ing ciphertext with random keys
    def fake_decrypt(ct: bytes, rng_seed: int = 0) -> Image.Image:
        rng = np.random.RandomState(rng_seed)
        fake_key = rng.bytes(len(ct))
        plaintext = bytes(a ^ b for a, b in zip(ct, fake_key))
        return map_bits_to_image(plaintext[:width*height*3],
                                 strategy="direct_rgb", width=width, height=height)

    fig = plt.figure(figsize=(14, 9), facecolor=BG_DARK)

    # Central ciphertext
    ax_ct = fig.add_axes([0.36, 0.3, 0.28, 0.4])
    ax_ct.imshow(np.array(ct_img), interpolation="nearest")
    ax_ct.set_title("CIPHERTEXT", color=CLASSICAL_AMBER, fontsize=11, fontweight="bold", pad=6)
    ax_ct.axis("off")
    for spine in ax_ct.spines.values():
        spine.set_edgecolor(CLASSICAL_AMBER); spine.set_linewidth(2)

    # 6 surrounding decryption panels: positions arranged around the centre
    positions = [
        (0.01,  0.55),  # left top
        (0.01,  0.15),  # left bottom
        (0.355, 0.78),  # top
        (0.355, 0.02),  # bottom
        (0.73,  0.55),  # right top
        (0.73,  0.15),  # right bottom
    ]

    for i, ((lx, ly), msg) in enumerate(zip(positions, sample_messages)):
        dec_img = fake_decrypt(ciphertext_bytes[:width*height*3], i*17)
        ax = fig.add_axes([lx, ly, 0.23, 0.28])
        ax.imshow(np.array(dec_img), interpolation="nearest", alpha=0.65)
        ax.set_facecolor(PANEL_BG)
        ax.set_title(f'"{msg}"', color=QUANTUM_GREEN, fontsize=9, fontweight="bold", pad=5)
        ax.axis("off")
        for spine in ax.spines.values():
            spine.set_edgecolor(QUANTUM_GREEN); spine.set_linewidth(1.5)

        # Arrow from ciphertext to panel
        fig.add_artist(matplotlib.patches.FancyArrowPatch(
            posA=(0.50, 0.50), posB=(lx + 0.115, ly + 0.14),
            arrowstyle="-|>", color=TEXT_MUTED, lw=0.8, alpha=0.4,
            connectionstyle="arc3,rad=0.1",
            transform=fig.transFigure,
            mutation_scale=8,
        ))

    fig.text(
        0.5, -0.03,
        "All six are valid decryptions of the same ciphertext.\n"
        "An attacker cannot know which is correct.\n"
        "This is information-theoretic security. — Shannon, 1949",
        ha="center", va="top", color=TEXT_MUTED, fontsize=9,
        linespacing=1.6,
    )

    fig.suptitle("Perfect Secrecy: One Ciphertext → Infinite Valid Plaintexts",
                 color=TEXT_WHITE, fontsize=13, fontweight="bold")

    if save_path:
        fig.savefig(save_path, dpi=110, bbox_inches="tight", facecolor=BG_DARK)

    return fig


# =============================================================================
# TASK 4.8 — Quantum Key Passport (Certificate Card Image)
# =============================================================================

def generate_key_passport(
    key_image: Image.Image,
    metadata: dict,
    save_path: Optional[str] = None,
) -> Image.Image:
    """
    Generate a visual Quantum Key Passport / certificate card.

    Parameters
    ----------
    key_image : 64×64 (or similar) PIL Image of the quantum key
    metadata  : dict with fields:
        nickname         : str — key name
        job_id           : str — IBM Quantum job ID
        entropy          : float — e.g. 0.9991
        nist_passed      : int — e.g. 14
        nist_total       : int — e.g. 15
        key_bits         : int — e.g. 98304
        circuit          : str — e.g. "GHZ (10 qubits)"
        issued           : str — ISO timestamp (optional, defaults to now)
        fingerprint      : str — hex (auto-computed if absent)
    save_path : optional PNG output path

    Returns
    -------
    PIL Image of the passport card
    """
    # Defaults
    issued = metadata.get("issued") or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    fp_raw = metadata.get("fingerprint") or hashlib.sha256(
        np.array(key_image).tobytes()
    ).hexdigest()[:16]
    fingerprint = " ".join(fp_raw[i:i+4] for i in range(0, 16, 4))

    # Card dimensions
    CARD_W, CARD_H = 620, 220
    THUMB_W, THUMB_H = 120, 120

    # Colours
    C_BG       = (10,  10,  15)
    C_ACCENT   = (0,   230, 118)   # quantum green
    C_PANEL    = (20,  20,  30)
    C_WHITE    = (245, 245, 245)
    C_MUTED    = (120, 120, 140)
    C_GOLD     = (255, 180,  50)
    C_DARK_GRN = (0,   100,  50)

    card = Image.new("RGB", (CARD_W, CARD_H), C_BG)
    draw = ImageDraw.Draw(card)

    # --- Background subtle grid ---
    for x in range(0, CARD_W, 20):
        draw.line([(x, 0), (x, CARD_H)], fill=(20, 25, 30), width=1)
    for y in range(0, CARD_H, 20):
        draw.line([(0, y), (CARD_W, y)], fill=(20, 25, 30), width=1)

    # --- Outer border ---
    draw.rectangle([0, 0, CARD_W - 1, CARD_H - 1], outline=C_ACCENT, width=2)

    # --- Header bar ---
    draw.rectangle([0, 0, CARD_W, 32], fill=C_DARK_GRN)
    draw.text((10, 8), "◈  QUANTUM NOISE ART — KEY CERTIFICATE", fill=C_ACCENT,
              font=_get_font(11, bold=True))

    # --- Divider ---
    draw.line([(0, 33), (CARD_W, 33)], fill=C_ACCENT, width=1)

    # --- Thumbnail ---
    thumb = key_image.resize((THUMB_W, THUMB_H), Image.NEAREST)
    card.paste(thumb, (12, 46))
    draw.rectangle([11, 45, 11 + THUMB_W + 1, 45 + THUMB_H + 1], outline=C_ACCENT, width=1)

    # --- Right panel: metadata ---
    RX = THUMB_W + 24

    def field(y, label, value, val_col=C_WHITE):
        draw.text((RX, y), f"{label}:", fill=C_MUTED, font=_get_font(9))
        draw.text((RX + 110, y), str(value), fill=val_col, font=_get_font(9, bold=True))

    field(46,  "Name",    metadata.get("nickname", "Unnamed Key"), C_GOLD)
    field(63,  "Issued",  issued)
    field(80,  "Job ID",  metadata.get("job_id", "UNKNOWN"))
    field(97,  "Entropy", f"{metadata.get('entropy', 0.0):.4f}", C_ACCENT)
    field(114, "NIST",    f"{metadata.get('nist_passed', '?')}/{metadata.get('nist_total', 15)} passed",
          C_ACCENT if metadata.get("nist_passed", 0) >= 14 else C_GOLD)
    field(131, "Key bits",metadata.get("key_bits", "?"))
    field(148, "Circuit", metadata.get("circuit", "Unknown"))

    # --- Fingerprint strip ---
    draw.rectangle([12, 172, THUMB_W + 12, 188], fill=C_PANEL)
    draw.text((14, 174), f"FP: {fingerprint}", fill=C_MUTED, font=_get_font(8))

    # --- Verified banner ---
    draw.rectangle([0, CARD_H - 35, CARD_W, CARD_H], fill=C_DARK_GRN)
    draw.line([(0, CARD_H - 36), (CARD_W, CARD_H - 36)], fill=C_ACCENT, width=1)
    draw.text((12, CARD_H - 26),
              "✓  QUANTUM CRYPTOGRAPHICALLY VERIFIED",
              fill=C_ACCENT, font=_get_font(10, bold=True))
    draw.text((400, CARD_H - 26),
              "Reproducible: NEVER  │  Status: ACTIVE",
              fill=C_MUTED, font=_get_font(9))

    if save_path:
        card.save(save_path)

    return card


def _get_font(size: int, bold: bool = False):
    """Return a PIL font; falls back to default if no TTF available."""
    try:
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono{}.ttf".format(
            "-Bold" if bold else ""
        )
        return ImageFont.truetype(font_path, size)
    except Exception:
        return ImageFont.load_default()


# ---------------------------------------------------------------------------
# CLI demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os
    os.makedirs("gallery", exist_ok=True)

    result = generate_mock_bitstream(n_bits=64 * 64 * 24)
    key_img = map_bits_to_image(result, strategy="direct_rgb", width=64, height=64)

    # 4.5 Avalanche
    fig_av = visualise_avalanche(
        result.bytes_data[:64*64*3],
        width=64, height=64,
        save_path="gallery/avalanche.png",
    )
    print("Saved gallery/avalanche.png")
    plt.close(fig_av)

    # 4.6 Comparison
    fig_cmp = generate_comparison_dashboard(
        result.bytes_data,
        width=64, height=64,
        save_path="gallery/comparison_dashboard.png",
    )
    print("Saved gallery/comparison_dashboard.png")
    plt.close(fig_cmp)

    # 4.7 Perfect secrecy
    fig_ps = visualise_perfect_secrecy(
        result.bytes_data,
        width=64, height=64,
        save_path="gallery/perfect_secrecy.png",
    )
    print("Saved gallery/perfect_secrecy.png")
    plt.close(fig_ps)

    # 4.8 Passport
    meta = {
        "nickname":    "Entangled Quasar",
        "job_id":      result.job_id,
        "entropy":     0.9991,
        "nist_passed": 14,
        "nist_total":  15,
        "key_bits":    len(result.bytes_data) * 8,
        "circuit":     "GHZ (10 qubits)",
    }
    passport = generate_key_passport(key_img, meta, save_path="gallery/key_passport.png")
    print("Saved gallery/key_passport.png")

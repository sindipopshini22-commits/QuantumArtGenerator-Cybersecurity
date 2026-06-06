"""
style_transfer.py — Task 4.2
Neural style transfer pipeline with three tiers:

  Tier 1 (SLOW)  — Full VGG19 optimization-based style transfer (2–5 min, GPU)
  Tier 2 (FAST)  — Pre-trained fast neural style transfer (<5 sec, CPU OK)
  Tier 3 (FALLBACK) — matplotlib colormap enhancement (<1 sec, always works)

Part 4 uses Tier 3 for live demo, Tier 1 for pre-generated gallery.
"""

import os
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from typing import Optional, Literal
from pathlib import Path

# ---------------------------------------------------------------------------
# Style preset definitions
# ---------------------------------------------------------------------------

STYLE_PRESETS = {
    "Cosmic Nebula": {
        "description": "Deep purples and gas cloud textures",
        "colormap": "plasma",
        "hue_shift": 0.75,
        "saturation": 1.6,
        "blur_radius": 1.5,
        "contrast": 1.2,
    },
    "Circuit Board": {
        "description": "Green on black, geometric lines",
        "colormap": None,
        "hue_shift": None,
        "tint": (0, 255, 80),
        "saturation": 2.0,
        "contrast": 1.8,
        "sharpen": True,
    },
    "Van Gogh Starry Night": {
        "description": "Swirling blues, high energy",
        "colormap": "twilight_shifted",
        "hue_shift": 0.6,
        "saturation": 1.8,
        "blur_radius": 0.8,
        "contrast": 1.3,
        "swirl": True,
    },
    "Kandinsky Abstract": {
        "description": "Bold colours, geometric forms",
        "colormap": "hsv",
        "hue_shift": None,
        "saturation": 2.2,
        "contrast": 1.5,
    },
    "Thermal Imaging": {
        "description": "Heat map orange-to-blue gradient",
        "colormap": "inferno",
        "hue_shift": None,
        "saturation": 1.0,
        "contrast": 1.1,
    },
    "Crystalline": {
        "description": "Sharp geometric facets, cool blues",
        "colormap": "cool",
        "hue_shift": 0.55,
        "saturation": 1.4,
        "contrast": 2.0,
        "sharpen": True,
    },
    "Bioluminescent": {
        "description": "Dark background, glowing cyan/green",
        "colormap": "summer",
        "hue_shift": 0.5,
        "saturation": 2.5,
        "contrast": 1.7,
        "darken": 0.6,
    },
}


# ---------------------------------------------------------------------------
# Tier 3 — Colormap Enhancement (FALLBACK, always works, <1 second)
# ---------------------------------------------------------------------------

def _apply_colormap(img_gray: np.ndarray, cmap_name: str) -> np.ndarray:
    """Apply a matplotlib colormap to a grayscale float32 array → uint8 RGB."""
    cmap = cm.get_cmap(cmap_name)
    normalised = img_gray.astype(np.float32) / 255.0
    rgba = cmap(normalised)
    rgb = (rgba[:, :, :3] * 255).astype(np.uint8)
    return rgb


def _tint_green_circuit(arr: np.ndarray) -> np.ndarray:
    """Transform image to classic circuit-board green-on-black."""
    gray = (arr.mean(axis=2) if arr.ndim == 3 else arr).astype(np.float32) / 255.0
    # High contrast threshold
    threshold = 0.5
    result = np.zeros((*gray.shape, 3), dtype=np.uint8)
    bright = gray > threshold
    result[bright] = [0, int(255 * gray[bright].mean() * 1.5), 60]
    glow = gray > 0.3
    result[glow & ~bright, 1] = (gray[glow & ~bright] * 80).astype(np.uint8)
    return result


def _swirl_array(arr: np.ndarray, strength: float = 3.0) -> np.ndarray:
    """Simple swirl distortion approximation using polar coordinate remapping."""
    h, w = arr.shape[:2]
    cx, cy = w / 2, h / 2
    y_coords, x_coords = np.mgrid[0:h, 0:w].astype(np.float32)
    dx = x_coords - cx
    dy = y_coords - cy
    r = np.sqrt(dx**2 + dy**2)
    angle = np.arctan2(dy, dx) + strength * r / max(h, w)
    src_x = np.clip((cx + r * np.cos(angle)).astype(int), 0, w - 1)
    src_y = np.clip((cy + r * np.sin(angle)).astype(int), 0, h - 1)
    return arr[src_y, src_x]


def apply_style_colormap(
    source_image: Image.Image,
    preset_name: str,
) -> Image.Image:
    """
    Tier 3 style application using colormaps and PIL transforms.
    No GPU required. Always works. ~1 second.

    Parameters
    ----------
    source_image : PIL Image (the quantum noise image from pixel_mapper)
    preset_name  : one of STYLE_PRESETS keys

    Returns
    -------
    Styled PIL Image (RGB)
    """
    if preset_name not in STYLE_PRESETS:
        raise ValueError(f"Unknown preset '{preset_name}'. Choose from: {list(STYLE_PRESETS)}")

    preset = STYLE_PRESETS[preset_name]

    # Convert to numpy
    img_rgb = source_image.convert("RGB")
    arr = np.array(img_rgb)
    gray = arr.mean(axis=2).astype(np.uint8)

    # --- Apply colormap ---
    if preset.get("colormap"):
        styled = _apply_colormap(gray, preset["colormap"])
    elif preset.get("tint"):
        styled = _tint_green_circuit(arr)
    else:
        styled = arr.copy()

    # --- Swirl ---
    if preset.get("swirl"):
        styled = _swirl_array(styled, strength=4.0)

    # --- PIL enhancements ---
    pil_styled = Image.fromarray(styled.astype(np.uint8), mode="RGB")

    # Contrast
    if preset.get("contrast", 1.0) != 1.0:
        pil_styled = ImageEnhance.Contrast(pil_styled).enhance(preset["contrast"])

    # Saturation
    if preset.get("saturation", 1.0) != 1.0:
        pil_styled = ImageEnhance.Color(pil_styled).enhance(preset["saturation"])

    # Blur (for nebula/starry softness)
    if preset.get("blur_radius", 0) > 0:
        pil_styled = pil_styled.filter(ImageFilter.GaussianBlur(radius=preset["blur_radius"]))

    # Sharpen
    if preset.get("sharpen"):
        pil_styled = pil_styled.filter(ImageFilter.SHARPEN)
        pil_styled = pil_styled.filter(ImageFilter.SHARPEN)

    # Darken (bioluminescent)
    if preset.get("darken"):
        pil_styled = ImageEnhance.Brightness(pil_styled).enhance(preset["darken"])

    return pil_styled


# ---------------------------------------------------------------------------
# Tier 1 — VGG19 Optimization-Based Style Transfer (full, slow)
# ---------------------------------------------------------------------------

def apply_style_vgg19(
    content_image: Image.Image,
    style_image: Image.Image,
    n_steps: int = 300,
    content_weight: float = 1e4,
    style_weight: float = 1e-2,
    device: str = "auto",
) -> Image.Image:
    """
    Full VGG19 neural style transfer.
    Requires PyTorch + torchvision. GPU strongly recommended.
    Takes 2–5 minutes on GPU, 15–30 minutes on CPU.

    Parameters
    ----------
    content_image : quantum noise image (structure to preserve)
    style_image   : artistic reference
    n_steps       : optimisation iterations (300 = good quality)
    content_weight: higher → preserve quantum structure
    style_weight  : higher → enforce style strongly
    device        : 'cuda', 'cpu', or 'auto'

    Returns
    -------
    Styled PIL Image
    """
    try:
        import torch
        import torch.nn as nn
        import torch.optim as optim
        import torchvision.transforms as T
        import torchvision.models as models
    except ImportError:
        print("PyTorch not available. Falling back to colormap style transfer.")
        # Map style_image description to nearest preset
        return apply_style_colormap(content_image, "Cosmic Nebula")

    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"

    transform = T.Compose([
        T.Resize((256, 256)),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    def load_tensor(pil_img):
        return transform(pil_img.convert("RGB")).unsqueeze(0).to(device)

    content_t = load_tensor(content_image)
    style_t   = load_tensor(style_image)

    # Load VGG19
    vgg = models.vgg19(weights="DEFAULT").features.to(device).eval()
    for p in vgg.parameters():
        p.requires_grad_(False)

    content_layers = {"21"}      # conv4_2
    style_layers   = {"0","5","10","19","28"}  # conv1_1 through conv5_1

    def get_features(x, model):
        features = {}
        for name, layer in model._modules.items():
            x = layer(x)
            if name in content_layers | style_layers:
                features[name] = x
        return features

    def gram_matrix(t):
        b, c, h, w = t.size()
        f = t.view(c, h * w)
        return torch.mm(f, f.t()) / (c * h * w)

    content_features = get_features(content_t, vgg)
    style_features   = get_features(style_t, vgg)
    style_grams      = {k: gram_matrix(v) for k, v in style_features.items()
                        if k in style_layers}

    target = content_t.clone().requires_grad_(True)
    optimizer = optim.LBFGS([target])

    step = [0]
    while step[0] < n_steps:
        def closure():
            target.data.clamp_(0, 1)
            optimizer.zero_grad()
            target_features = get_features(target, vgg)

            c_loss = nn.functional.mse_loss(
                target_features["21"], content_features["21"]
            )
            s_loss = sum(
                nn.functional.mse_loss(gram_matrix(target_features[l]), style_grams[l])
                for l in style_layers if l in target_features
            )
            loss = content_weight * c_loss + style_weight * s_loss
            loss.backward()
            step[0] += 1
            if step[0] % 50 == 0:
                print(f"  Step {step[0]}/{n_steps} — loss {loss.item():.4f}")
            return loss

        optimizer.step(closure)

    # Denormalise and convert back to PIL
    output = target.squeeze(0).cpu().detach()
    mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
    std  = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
    output = output * std + mean
    output = output.clamp(0, 1)

    arr = (output.permute(1, 2, 0).numpy() * 255).astype(np.uint8)
    result = Image.fromarray(arr).resize(content_image.size, Image.LANCZOS)
    return result


# ---------------------------------------------------------------------------
# Unified public API
# ---------------------------------------------------------------------------

def apply_style(
    content_image: Image.Image,
    preset_name: str,
    style_image: Optional[Image.Image] = None,
    mode: Literal["auto", "colormap", "vgg19"] = "auto",
) -> Image.Image:
    """
    Apply a named style preset to a quantum noise image.

    mode='auto'     → try VGG19 if PyTorch available, else colormap
    mode='colormap' → always use fast colormap (live demo)
    mode='vgg19'    → always use VGG19 (gallery pre-generation)

    The styled image preserves quantum structure as content;
    run steganography.embed_key() after to restore LSB key data.
    """
    if mode == "colormap":
        return apply_style_colormap(content_image, preset_name)

    if mode == "vgg19":
        if style_image is None:
            raise ValueError("vgg19 mode requires a style_image")
        return apply_style_vgg19(content_image, style_image)

    # auto: try VGG19, fall back gracefully
    try:
        import torch  # noqa
        if style_image is not None:
            return apply_style_vgg19(content_image, style_image)
    except ImportError:
        pass

    return apply_style_colormap(content_image, preset_name)


def list_presets() -> list:
    return list(STYLE_PRESETS.keys())


def preset_info(name: str) -> dict:
    return STYLE_PRESETS.get(name, {})


# ---------------------------------------------------------------------------
# CLI demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from mock_bitstream import generate_mock_bitstream
    from pixel_mapper import map_bits_to_image
    import os

    result = generate_mock_bitstream(n_bits=64 * 64 * 24)
    noise_img = map_bits_to_image(result, strategy="direct_rgb", width=64, height=64)

    os.makedirs("gallery", exist_ok=True)
    for preset in list_presets():
        styled = apply_style(noise_img, preset, mode="colormap")
        safe_name = preset.replace(" ", "_").lower()
        path = f"gallery/styled_{safe_name}.png"
        # Scale up for visibility
        styled.resize((256, 256), Image.NEAREST).save(path)
        print(f"Saved {path}")

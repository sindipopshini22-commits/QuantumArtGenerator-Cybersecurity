"""
diffusion_seeder.py — Task 4.3
Use quantum noise as the initial latent for Stable Diffusion img2img.

Why this matters:
  SD literally starts from random noise and denoises → image.
  Injecting real quantum noise at step 0 means the diffusion trajectory
  was determined by quantum measurement — not pseudorandom math.

Requires: diffusers, transformers, accelerate, torch (GPU recommended)
Fallback:  colormap enhancement when diffusers unavailable
"""

import numpy as np
from PIL import Image
from typing import Optional
from style_transfer import apply_style_colormap, STYLE_PRESETS


# ---------------------------------------------------------------------------
# Stable Diffusion pipeline (optional dependency)
# ---------------------------------------------------------------------------

def _load_sd_pipeline(device: str = "auto"):
    """Load Stable Diffusion img2img pipeline, or raise ImportError."""
    import torch
    from diffusers import StableDiffusionImg2ImgPipeline

    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"Loading Stable Diffusion on {device}...")
    pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        safety_checker=None,
    )
    pipe = pipe.to(device)

    # Memory optimisations
    if device == "cuda":
        pipe.enable_attention_slicing()

    return pipe, device


_SD_PIPELINE = None  # Module-level cache


def get_sd_pipeline(device: str = "auto"):
    """Return cached SD pipeline, loading on first call."""
    global _SD_PIPELINE
    if _SD_PIPELINE is None:
        _SD_PIPELINE = _load_sd_pipeline(device)
    return _SD_PIPELINE


# ---------------------------------------------------------------------------
# Strength parameter guide
# ---------------------------------------------------------------------------

STRENGTH_GUIDE = {
    "quantum_dominant":  (0.3, 0.5,  "Quantum structure dominates; prompt adds colour only"),
    "balanced":          (0.5, 0.7,  "Balanced — best for most outputs"),
    "prompt_dominant":   (0.7, 0.9,  "Prompt dominates; quantum provides entropy only"),
}


# ---------------------------------------------------------------------------
# Core seeding function
# ---------------------------------------------------------------------------

def seed_with_quantum(
    quantum_noise_image: Image.Image,
    style_prompt: str,
    strength: float = 0.65,
    guidance_scale: float = 7.5,
    n_inference_steps: int = 50,
    device: str = "auto",
    output_size: Optional[tuple] = None,
) -> dict:
    """
    Run Stable Diffusion img2img seeded with a quantum noise image.

    Parameters
    ----------
    quantum_noise_image : PIL Image from pixel_mapper
    style_prompt        : artistic text prompt (from Part 3 LLM translator)
    strength            : 0.0=pure quantum, 1.0=pure prompt, 0.5-0.7=recommended
    guidance_scale      : classifier-free guidance scale
    n_inference_steps   : denoising steps (50 = standard quality)
    device              : 'cuda', 'cpu', or 'auto'
    output_size         : (width, height) for output, or None to keep input size

    Returns
    -------
    dict with:
      image         : PIL Image — the quantum-seeded diffusion output
      method        : 'stable_diffusion' or 'colormap_fallback'
      prompt_used   : str
      strength_used : float
      note          : explanation string
    """
    if output_size:
        seed_img = quantum_noise_image.resize(output_size, Image.LANCZOS).convert("RGB")
    else:
        # SD works best with multiples of 8; scale up small images
        w, h = quantum_noise_image.size
        w = max(512, (w // 8) * 8)
        h = max(512, (h // 8) * 8)
        seed_img = quantum_noise_image.resize((w, h), Image.LANCZOS).convert("RGB")

    # Attempt Stable Diffusion
    try:
        pipe, used_device = get_sd_pipeline(device)

        print(f"Running quantum-seeded diffusion (strength={strength})...")
        result = pipe(
            prompt=style_prompt,
            image=seed_img,
            strength=strength,
            guidance_scale=guidance_scale,
            num_inference_steps=n_inference_steps,
        )
        output_image = result.images[0]

        return {
            "image":         output_image,
            "method":        "stable_diffusion",
            "prompt_used":   style_prompt,
            "strength_used": strength,
            "note": (
                f"Stable Diffusion img2img on {used_device}. "
                f"Quantum noise injected at step 0 (strength={strength}). "
                f"Diffusion trajectory determined by quantum measurement."
            ),
        }

    except (ImportError, Exception) as e:
        print(f"SD unavailable ({e}). Using colormap fallback.")
        return _colormap_fallback(quantum_noise_image, style_prompt, strength)


def _colormap_fallback(
    quantum_noise_image: Image.Image,
    style_prompt: str,
    strength: float,
) -> dict:
    """
    CPU fallback: match the prompt to the nearest style preset and
    apply colormap enhancement. Takes <1 second.
    """
    prompt_lower = style_prompt.lower()

    # Keyword-to-preset matching
    keyword_map = {
        "nebula":        "Cosmic Nebula",
        "cosmic":        "Cosmic Nebula",
        "purple":        "Cosmic Nebula",
        "circuit":       "Circuit Board",
        "tech":          "Circuit Board",
        "electronic":    "Circuit Board",
        "starry":        "Van Gogh Starry Night",
        "van gogh":      "Van Gogh Starry Night",
        "swirl":         "Van Gogh Starry Night",
        "kandinsky":     "Kandinsky Abstract",
        "abstract":      "Kandinsky Abstract",
        "bold":          "Kandinsky Abstract",
        "heat":          "Thermal Imaging",
        "thermal":       "Thermal Imaging",
        "infrared":      "Thermal Imaging",
        "crystal":       "Crystalline",
        "geometric":     "Crystalline",
        "cold":          "Crystalline",
        "bioluminescent":"Bioluminescent",
        "glow":          "Bioluminescent",
        "ocean":         "Bioluminescent",
    }
    preset = "Cosmic Nebula"  # default
    for kw, p in keyword_map.items():
        if kw in prompt_lower:
            preset = p
            break

    styled = apply_style_colormap(quantum_noise_image, preset)

    return {
        "image":         styled,
        "method":        "colormap_fallback",
        "prompt_used":   style_prompt,
        "strength_used": strength,
        "note": (
            f"Colormap fallback (PyTorch/diffusers unavailable). "
            f"Applied preset '{preset}' matched to prompt keywords."
        ),
    }


# ---------------------------------------------------------------------------
# Batch generation for gallery
# ---------------------------------------------------------------------------

def generate_gallery(
    quantum_noise_images: list,
    prompts: list,
    strength: float = 0.65,
    output_dir: str = "gallery",
    mode: str = "auto",
) -> list:
    """
    Generate a batch of styled images for the gallery.

    Parameters
    ----------
    quantum_noise_images : list of PIL Images
    prompts              : list of style prompts (same length)
    strength             : SD strength parameter
    output_dir           : where to save images
    mode                 : 'auto' | 'sd_only' | 'fallback_only'

    Returns
    -------
    List of result dicts (same format as seed_with_quantum)
    """
    import os
    os.makedirs(output_dir, exist_ok=True)

    results = []
    for i, (img, prompt) in enumerate(zip(quantum_noise_images, prompts)):
        print(f"\nGenerating {i+1}/{len(prompts)}: {prompt[:50]}...")
        if mode == "fallback_only":
            r = _colormap_fallback(img, prompt, strength)
        else:
            r = seed_with_quantum(img, prompt, strength=strength)

        # Save to gallery
        safe = prompt[:30].replace(" ", "_").replace("/", "-")
        path = os.path.join(output_dir, f"diffusion_{i:02d}_{safe}.png")
        r["image"].save(path)
        r["saved_path"] = path
        results.append(r)
        print(f"  Saved {path} via {r['method']}")

    return results


# ---------------------------------------------------------------------------
# CLI demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from mock_bitstream import generate_mock_bitstream
    from pixel_mapper import map_bits_to_image

    result = generate_mock_bitstream(n_bits=64 * 64 * 24)
    noise_img = map_bits_to_image(result, strategy="direct_rgb", width=64, height=64)

    prompts_and_presets = [
        ("warm sunset colours with flowing structure",  0.60),
        ("cold precise circuit board geometric",        0.55),
        ("chaotic explosive cosmic nebula purple",      0.70),
        ("bioluminescent ocean glow dark",              0.65),
    ]

    imgs  = [noise_img] * len(prompts_and_presets)
    prompts = [p for p, _ in prompts_and_presets]

    results = generate_gallery(imgs, prompts, output_dir="gallery", mode="fallback_only")
    print(f"\nGenerated {len(results)} images.")

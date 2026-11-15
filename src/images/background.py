"""Soft coloured-blob backgrounds ("mesh gradient" look) with film grain."""

from __future__ import annotations

import datetime as dt
import hashlib

import numpy as np
from PIL import Image

from .seasons import palette_for

SIZE = 1080


def _rng_for(date: dt.date, salt: str = "") -> np.random.Generator:
    digest = hashlib.sha256(f"{date.isoformat()}{salt}".encode()).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], "little"))


def render_background(
    date: dt.date,
    size: int = SIZE,
    n_blobs: int = 7,
    grain: float = 0.035,
    seed_salt: str = "",
) -> Image.Image:
    """Render a seasonal blob background for `date`.

    The palette comes from the date's season; blob layout is seeded from the
    date (plus optional `seed_salt` to reroll a layout you don't like).
    """
    colors, _ = palette_for(date)
    base, blob_colors = colors[0], colors[1:]
    rng = _rng_for(date, seed_salt)

    # Work on a normalised [-0.2, 1.2] grid so blobs can sit partly off-canvas.
    lin = np.linspace(0.0, 1.0, size)
    x, y = np.meshgrid(lin, lin)

    acc = np.zeros((size, size, 3))
    wsum = np.zeros((size, size))

    # Base wash: constant weight so blobs fade into it rather than to black.
    base_w = 0.35
    acc += base_w * base
    wsum += base_w

    for i in range(n_blobs):
        color = blob_colors[i % len(blob_colors)]
        cx, cy = rng.uniform(-0.15, 1.15, 2)
        rx, ry = rng.uniform(0.22, 0.55, 2)
        theta = rng.uniform(0, np.pi)
        strength = rng.uniform(0.7, 1.4)

        dx, dy = x - cx, y - cy
        u = (dx * np.cos(theta) + dy * np.sin(theta)) / rx
        v = (-dx * np.sin(theta) + dy * np.cos(theta)) / ry
        w = strength * np.exp(-(u * u + v * v) * 1.6)

        acc += w[..., None] * color
        wsum += w

    img = acc / wsum[..., None]

    # Film grain (luminance-only, so it doesn't add colour noise).
    if grain > 0:
        noise = rng.normal(0.0, grain, (size, size, 1))
        img = img + noise

    img = np.clip(img, 0.0, 1.0)
    return Image.fromarray((img * 255 + 0.5).astype(np.uint8), "RGB")

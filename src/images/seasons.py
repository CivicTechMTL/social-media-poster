"""Seasonal colour palettes for Montréal, interpolated smoothly across the year.

Each keyframe is anchored to a day of the year and has the same number of
colours: index 0 is the base/background wash, the rest are blob colours.
For any date we find the two surrounding keyframes (wrapping around New Year)
and blend each colour pair in OKLab, which keeps transitions perceptually even
(no muddy greys halfway between red and green).

Palettes are kept mid-toned on purpose so white text stays legible on top.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Keyframe:
    month: int
    day: int
    name: str
    colors: tuple[str, ...]  # hex; [0] = base, [1:] = blobs


# fmt: off
KEYFRAMES: list[Keyframe] = [
    Keyframe(1, 20, "deep winter",   ("#34568B", "#5B8FD0", "#9CC9E8", "#8C7BC4", "#23406E", "#C3D6EA")),
    Keyframe(3, 15, "sugar season",  ("#4F6E8E", "#8FB3CF", "#E0A85A", "#B9744A", "#6E9BB8", "#EBC98F")),
    Keyframe(5,  1, "spring bloom",  ("#5E9E6E", "#9CCB7F", "#E8A3B8", "#B794D6", "#F0D77A", "#4F8A8B")),
    Keyframe(6, 21, "early summer",  ("#2F8F6B", "#6CC3A0", "#F2C94C", "#4AA3D8", "#9BD06A", "#1F6F8B")),
    Keyframe(8,  5, "high summer",   ("#1E8C9A", "#F4A259", "#F07167", "#FFC75F", "#2EC4B6", "#E76F51")),
    Keyframe(9, 25, "early autumn",  ("#7D7A3E", "#B5BE8E", "#E3B04B", "#D9822B", "#9C8F4F", "#C96A2E")),
    Keyframe(10, 20, "peak autumn",  ("#A8322D", "#E8743B", "#F2A24A", "#8C7B3A", "#C9C79A", "#C2412F")),
    Keyframe(11, 22, "late autumn",  ("#7E3528", "#C0602F", "#7A4A6A", "#D9944A", "#A33A36", "#6E6A44")),
    Keyframe(12, 21, "first snow",   ("#2C5A4C", "#A3303F", "#6F9CC4", "#C9D8E4", "#3E7A62", "#C2505C")),
]
# fmt: on


# --- colour space helpers (sRGB <-> OKLab) ---------------------------------

def hex_to_rgb(h: str) -> np.ndarray:
    h = h.lstrip("#")
    return np.array([int(h[i : i + 2], 16) for i in (0, 2, 4)], dtype=float) / 255.0


def _srgb_to_linear(c: np.ndarray) -> np.ndarray:
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _linear_to_srgb(c: np.ndarray) -> np.ndarray:
    c = np.clip(c, 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


_M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929],
                [0.2119034982, 0.6806995451, 0.1073969566],
                [0.0883024619, 0.2817188376, 0.6299787005]])
_M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468],
                [1.9779984951, -2.4285922050, 0.4505937099],
                [0.0259040371, 0.7827717662, -0.8086757660]])


def rgb_to_oklab(rgb: np.ndarray) -> np.ndarray:
    lms = _srgb_to_linear(rgb) @ _M1.T
    return np.cbrt(lms) @ _M2.T


def oklab_to_rgb(lab: np.ndarray) -> np.ndarray:
    lms = (lab @ np.linalg.inv(_M2).T) ** 3
    return _linear_to_srgb(lms @ np.linalg.inv(_M1).T)


# --- palette lookup --------------------------------------------------------

def _anchor(kf: Keyframe, year: int) -> dt.date:
    return dt.date(year, kf.month, kf.day)


def palette_for(date: dt.date) -> tuple[np.ndarray, str]:
    """Return (colors as Nx3 float sRGB array in 0..1, human-readable label)."""
    # Build the keyframe timeline around `date`, including wrap-around neighbours.
    timeline = (
        [(_anchor(KEYFRAMES[-1], date.year - 1), KEYFRAMES[-1])]
        + [(_anchor(k, date.year), k) for k in KEYFRAMES]
        + [(_anchor(KEYFRAMES[0], date.year + 1), KEYFRAMES[0])]
    )
    for (d0, k0), (d1, k1) in zip(timeline, timeline[1:]):
        if d0 <= date <= d1:
            t = (date - d0).days / max((d1 - d0).days, 1)
            break
    # Smoothstep so colours linger near each keyframe and move in between.
    t = t * t * (3 - 2 * t)
    a = rgb_to_oklab(np.stack([hex_to_rgb(c) for c in k0.colors]))
    b = rgb_to_oklab(np.stack([hex_to_rgb(c) for c in k1.colors]))
    colors = oklab_to_rgb(a + (b - a) * t)
    label = k0.name if t < 0.5 else k1.name
    return colors, label

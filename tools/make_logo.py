"""Turn the teal-circle ctMTL logo into white line-art on transparent.

Every pixel is projected onto the teal->white axis: pure teal becomes fully
transparent, pure white fully opaque, and anti-aliased edges get partial alpha.

Usage: python tools/make_logo.py [src] [dst]
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets/logo-teal.png"
DST = ROOT / "assets/logo-white.png"
TEAL = np.array([79, 204, 158], dtype=float)
WHITE = np.array([255, 255, 255], dtype=float)


def main(src: Path = SRC, dst: Path = DST) -> None:
    src_img = Image.open(src).convert("RGBA")
    im = np.asarray(src_img).astype(float)
    rgb = im[..., :3]
    # Erode the circle mask a few px so its anti-aliased rim doesn't leave a ring.
    alpha = np.asarray(src_img.getchannel("A").filter(ImageFilter.MinFilter(7))) / 255.0

    axis = WHITE - TEAL
    t = ((rgb - TEAL) @ axis) / (axis @ axis)
    t = np.clip((t - 0.08) / 0.84, 0.0, 1.0)  # small dead-zone kills teal noise

    out = np.zeros_like(im)
    out[..., :3] = 255
    out[..., 3] = t * alpha * 255
    img = Image.fromarray(out.astype(np.uint8), "RGBA")
    img = img.crop(img.getbbox())
    dst.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst)
    print(f"wrote {dst} {img.size}")


if __name__ == "__main__":
    main(*(Path(a) for a in sys.argv[1:3]))

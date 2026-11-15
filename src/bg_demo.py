"""Generate a year of fortnightly backgrounds into out/bg-demo/ plus a contact sheet.

Usage:  poe bg-demo [--year 2026] [--start 2026-01-06]      (or: python -m src.bg_demo)
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .images.background import render_background
from .images.seasons import palette_for
from .shared import paths

OUT = paths.OUT / "bg-demo"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=dt.date.fromisoformat, default=dt.date(2026, 1, 6))
    ap.add_argument("--count", type=int, default=26)
    ap.add_argument("--every", type=int, default=14, help="days between events")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    dates = [args.start + dt.timedelta(days=args.every * i) for i in range(args.count)]

    thumbs: list[tuple[dt.date, str, Image.Image]] = []
    for i, d in enumerate(dates, 1):
        img = render_background(d)
        _, label = palette_for(d)
        path = OUT / f"{i:02d}_{d.isoformat()}.png"
        img.save(path)
        thumbs.append((d, label, img.resize((240, 240), Image.LANCZOS)))
        print(f"{path.name}  ({label})")

    # Contact sheet: 6 columns, date + season label under each thumbnail.
    cols, tw, th, pad, cap = 6, 240, 240, 16, 44
    rows = -(-len(thumbs) // cols)
    sheet = Image.new("RGB", (cols * (tw + pad) + pad, rows * (th + cap + pad) + pad), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=16)
    for i, (d, label, t) in enumerate(thumbs):
        x = pad + (i % cols) * (tw + pad)
        y = pad + (i // cols) * (th + cap + pad)
        sheet.paste(t, (x, y))
        draw.text((x, y + th + 4), d.strftime("%a %d %b %Y"), fill="#222", font=font)
        draw.text((x, y + th + 23), label, fill="#777", font=font)
    sheet.save(OUT / "_contact-sheet.png")
    print("_contact-sheet.png")


if __name__ == "__main__":
    main()

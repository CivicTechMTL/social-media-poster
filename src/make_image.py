"""Generate the social media image for a meetup.

Images go into the event folder: img-card.jpg / img-open.jpg. The background is read from the
folder's bg.jpg; if that's missing it's generated and saved there first.

Examples (or run directly: python -m src.make_image ...):
  poe render data/100                  # every layout -> data/100/img-card.jpg, img-open.jpg
  poe render data/100 --layout open    # -> data/100/img-open.jpg
  poe render-all                       # every event in data/ (folders with data.json)
  poe render data/100 --reroll 2       # new blob layout (overwrites bg.jpg), same season
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .shared.event import Event
from .shared.paths import DATA, LAYOUTS, display, event_folder, image_path
from .images.render import Renderer, event_background


def is_premade(folder: Path) -> bool:
    """`"premade": true` in data.json: the images were made by hand, so never render over them."""
    return bool(json.loads((folder / "data.json").read_text(encoding="utf-8")).get("premade"))


def all_events() -> list[Path]:
    """Every data/<n> folder with a data.json, in event order (premade ones are skipped)."""
    def key(p: Path):
        try:
            return (0, float(p.name))
        except ValueError:
            return (1, 0.0)
    return sorted((p.parent for p in DATA.glob("*/data.json") if not is_premade(p.parent)), key=key)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("events", nargs="*", type=event_folder, help="event folder(s) containing data.json, e.g. data/100 (data/2 finds data/002)")
    ap.add_argument("--all", action="store_true", help="render every event folder in data/")
    ap.add_argument("--layout", choices=(*LAYOUTS, "all"), default="all", help="which layout to render (default: all)")
    ap.add_argument("--reroll", default="", help="any value: reshuffle the background blobs and overwrite bg.jpg")
    args = ap.parse_args()
    if args.all:
        args.events = all_events()
    elif not args.events:
        ap.error("give one or more event folders, or --all")

    combos = LAYOUTS if args.layout == "all" else [args.layout]
    with Renderer() as r:
        for folder in args.events:
            if is_premade(folder):
                print(f"{folder}: premade image, skipped")
                continue
            ev = Event.load(folder)
            bg = event_background(ev, reroll=str(args.reroll))
            for layout in combos:
                out = image_path(folder, layout)
                scale = r.render(ev, bg, out, layout=layout)
                note = f"  (text shrunk to {scale:.0%} to fit)" if scale < 0.999 else ""
                print(f"{display(out)}{note}")


if __name__ == "__main__":
    main()

"""Render an Event to a 1080x1080 JPEG via a Jinja HTML template + headless Chromium.

Each event folder holds its own images: bg.jpg (the background, generated on first render and
reused after that) and img-<layout>.jpg (the finished images).
"""

from __future__ import annotations

import base64
import io
import mimetypes
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from PIL import Image
from playwright.sync_api import Browser, sync_playwright

from ..shared.event import Event
from ..shared.paths import ASSETS, BG_FILE, TEMPLATES
from .background import render_background

SIZE = 1080  # output is SIZE×SIZE
JPEG_OPTS = {"quality": 95, "subsampling": 0}  # 4:4:4 keeps the soft gradients from banding


def event_background(ev: Event, reroll: str = "", save: bool = True) -> Image.Image:
    """The event's background: read from its bg.jpg, or generated (and saved, if `save`) when
    that file is missing or `reroll` asks for a new blob layout."""
    path = ev.folder / BG_FILE if ev.folder else None
    if path and path.exists() and not reroll:
        img = Image.open(path).convert("RGB")
        if img.size != (SIZE, SIZE):  # fine: the template scales it to cover and centre-crops
            print(f"Info: {path} is {img.width}x{img.height}; it will be scaled/cropped to {SIZE}x{SIZE}.")
        return img
    img = render_background(ev.date, seed_salt=reroll)
    if path and save:
        img.save(path, **JPEG_OPTS)
    return img

_env = Environment(loader=FileSystemLoader(TEMPLATES), undefined=StrictUndefined, autoescape=True)


def _data_uri(data: bytes, mime: str) -> str:
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"


def _file_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    if path.suffix == ".woff2":
        mime = "font/woff2"
    return _data_uri(path.read_bytes(), mime)


def build_html(ev: Event, background: Image.Image, layout: str = "card", preview: bool = False) -> str:
    """`preview=True` makes the page run its own text fitting on load (for viewing in a browser)."""
    bg = background
    buf = io.BytesIO()
    bg.save(buf, "PNG")
    assets = {
        "font": _file_uri(ASSETS / "fonts/InterVariable.woff2"),
        "font_italic": _file_uri(ASSETS / "fonts/InterVariable-Italic.woff2"),
        "logo": _file_uri(ASSETS / "logo-white.png"),
        "background": _data_uri(buf.getvalue(), "image/png"),
        "photos": [_file_uri(s.photo) if s.photo else "" for s in ev.speakers],
    }
    tpl = _env.get_template(f"{layout}.html")
    return tpl.render(ev=ev, assets=assets, preview=preview)


class Renderer:
    """Keeps one Chromium instance alive across many renders."""

    def __enter__(self) -> "Renderer":
        self._pw = sync_playwright().start()
        self._browser: Browser = self._pw.chromium.launch()
        self._page = self._browser.new_page(viewport={"width": 1080, "height": 1080})
        return self

    def __exit__(self, *exc) -> None:
        self._browser.close()
        self._pw.stop()

    def render(self, ev: Event, background: Image.Image, out: Path, layout: str = "card") -> float:
        """Render to `out` (JPEG); returns the text scale the fitter had to apply (1.0 = none)."""
        html = build_html(ev, background, layout=layout)
        self._page.set_content(html, wait_until="load")
        self._page.evaluate("document.fonts.ready")
        scale = self._page.evaluate("window.__fit()")
        out.parent.mkdir(parents=True, exist_ok=True)
        png = self._page.screenshot(clip={"x": 0, "y": 0, "width": 1080, "height": 1080})
        Image.open(io.BytesIO(png)).convert("RGB").save(out, "JPEG", **JPEG_OPTS)
        return scale

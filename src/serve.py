"""Local preview server: view/inspect the image HTML live in a browser.

Usage:  poe serve [--port 8000]      (or: python -m src.serve)
Then open http://localhost:8000

Templates are re-read on every request, so edit templates/*.html and refresh.
(Changes to the Python code in src/ need a server restart.)
"""

from __future__ import annotations

import argparse
import html
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from .shared.event import Event
from .shared.paths import DATA, LAYOUTS
from .images.render import build_html, event_background

EVENT_DIRS = [DATA]


def find_events() -> dict[str, Path]:
    """Map 'data/100' style keys to event folders containing data.json."""
    found = {}
    for base in EVENT_DIRS:
        if not base.is_dir():
            continue
        for d in sorted(base.iterdir(), key=lambda p: _sort_key(p.name)):
            if (d / "data.json").exists():
                found[f"{base.name}/{d.name}"] = d
    return found


def _sort_key(name: str):
    try:
        return (0, float(name), name)
    except ValueError:
        return (1, 0.0, name)


INDEX_STYLE = """
  body { font-family: system-ui, sans-serif; margin: 32px; background: #f4f2ee; color: #222; }
  h1 { font-size: 22px; margin: 0 0 4px; }
  p { color: #666; margin: 0 0 24px; }
  table { border-collapse: collapse; }
  td, th { padding: 6px 14px; text-align: left; border-bottom: 1px solid #ddd; }
  a { color: #0b6e4f; }
"""


def index_page() -> str:
    rows = []
    for key, folder in find_events().items():
        try:
            ev = Event.load(folder)
            label = f"#{ev.number} · {ev.date:%Y-%m-%d} · {html.escape(ev.talk_en)}"
        except Exception as e:  # show broken data.json rather than crash the index
            label = f"<em>error: {html.escape(str(e))}</em>"
        links = " ".join(f'<a href="/{key}/{l}">{l}</a>' for l in LAYOUTS)
        rows.append(f"<tr><td>{html.escape(key)}</td><td>{links}</td><td>{label}</td></tr>")
    return (
        f"<!doctype html><meta charset=utf-8><title>Image preview</title><style>{INDEX_STYLE}</style>"
        "<h1>ctMTL image preview</h1>"
        "<p>Pages are 1080×1080 and re-render from the templates on every refresh.</p>"
        "<p><b>Background reroll:</b> add <code>?reroll=&lt;any text&gt;</code> to an image URL "
        "(e.g. <code>/data/100/card?reroll=banana</code>) to shuffle the blob layout. "
        "The text is a seed combined with the event date, so the same text on the same event always "
        "gives the same background; colours stay tied to the season. Without a reroll, the event's "
        "<code>bg.jpg</code> is used. To keep a reroll (overwrites <code>bg.jpg</code>): "
        "<code>poe render data/100 --reroll banana</code>.</p>"
        f"<table><tr><th>Event</th><th>Layout</th><th></th></tr>{''.join(rows)}</table>"
    )


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        url = urlparse(self.path)
        parts = [unquote(p) for p in url.path.strip("/").split("/") if p]
        try:
            if not parts:
                return self._send(200, index_page())
            if len(parts) == 3 and parts[2] in LAYOUTS:
                folder = find_events().get(f"{parts[0]}/{parts[1]}")
                if folder is None:
                    return self._send(404, "Unknown event")
                reroll = parse_qs(url.query).get("reroll", [""])[0]
                ev = Event.load(folder)
                bg = event_background(ev, reroll=reroll, save=False)  # previews never write bg.jpg
                page = build_html(ev, bg, layout=parts[2], preview=True)
                return self._send(200, page)
            self._send(404, "Not found")
        except Exception:
            self._send(500, f"<pre>{html.escape(traceback.format_exc())}</pre>")

    def _send(self, code: int, body: str) -> None:
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args) -> None:
        print(f"  {self.command} {self.path} -> {args[1] if len(args) > 1 else ''}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Serving image previews at http://localhost:{args.port}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

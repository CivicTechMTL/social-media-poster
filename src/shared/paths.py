"""Where things live: the project folders, and the file names inside each event folder."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # src/shared/paths.py -> project root

TEMPLATES = ROOT / "templates"
ASSETS = ROOT / "assets"
DATA = ROOT / "data"
ENV_FILE = ROOT / ".env"
OUT = ROOT / "out"

# Inside data/<n>/
LAYOUTS = ("card", "open")
BG_FILE = "bg.jpg"


def image_path(folder: Path, layout: str) -> Path:
    """The finished image for one layout: data/<n>/img-<layout>.jpg."""
    return folder / f"img-{layout}.jpg"


def display(path: Path) -> Path:
    """`path` relative to the project root when it's inside it (for tidier output)."""
    path = Path(path).resolve()
    return path.relative_to(ROOT) if path.is_relative_to(ROOT) else path

"""Where things live: the project folders, and the file names inside each event folder."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # src/shared/paths.py -> project root

TEMPLATES = ROOT / "templates"
ASSETS = ROOT / "assets"
DATA = ROOT / "data"
ENV_FILE = ROOT / ".env"
OUT = ROOT / "out"

# Event folders are zero-padded so they sort properly everywhere (e.g. on GitHub):
# data/002, data/010, data/010.5, data/100.
EVENT_DIGITS = 3

# Inside data/<n>/
LAYOUTS = ("card", "open")
BG_FILE = "bg.jpg"


def padded(name: str) -> str:
    """'2' -> '002', '10.5' -> '010.5', '002' -> '002'. Names that aren't numbers are left alone."""
    whole, dot, frac = name.partition(".")
    return f"{int(whole):0{EVENT_DIGITS}d}{dot}{frac}" if whole.isdigit() else name


def event_folder(arg: str | Path) -> Path:
    """Resolve what was typed on the command line to an event folder, so `data/2`, `data/002`
    and a bare `2` all work. An existing path wins; otherwise the last part is zero-padded (and a
    bare number is looked up in data/)."""
    path = Path(arg)
    if path.exists():
        return path
    candidate = path.with_name(padded(path.name))
    if candidate.exists() or path.parent != Path("."):
        return candidate
    return DATA / padded(path.name)


def image_path(folder: Path, layout: str) -> Path:
    """The finished image for one layout: data/<n>/img-<layout>.jpg."""
    return folder / f"img-{layout}.jpg"


def display(path: Path) -> Path:
    """`path` relative to the project root when it's inside it (for tidier output)."""
    path = Path(path).resolve()
    return path.relative_to(ROOT) if path.is_relative_to(ROOT) else path

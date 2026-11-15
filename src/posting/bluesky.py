"""Prepare and publish an event's Bluesky post (text + one image with alt text)."""

from __future__ import annotations

import datetime as dt
import io
import json
from dataclasses import dataclass
from pathlib import Path

from zoneinfo import ZoneInfo

import regex  # for \X (grapheme clusters), which is how Bluesky counts post length
from PIL import Image

# Limits. Post text: 300 graphemes (app.bsky.feed.post lexicon). Alt text: the lexicon sets
# no limit, but the Bluesky app caps it at 2000 characters, so stay under that to be safe.
# Image blobs: 1,000,000 bytes max.
MAX_POST_GRAPHEMES = 300
MAX_ALT_CHARS = 2000
MAX_IMAGE_BYTES = 1_000_000

RECORD_FILE = "bluesky.json"  # written next to data.json after a successful post

# Backfill: "bsky-backfill-date" in data.json backdates the post (its createdAt). A plain date is
# posted as noon Montréal time that day; a full ISO datetime is used as given (local time if it
# has no offset).
BACKFILL_FIELD = "bsky-backfill-date"
LOCAL_TZ = ZoneInfo("America/Montreal")
BACKFILL_DEFAULT_TIME = dt.time(12, 0)


def parse_backfill(value: str) -> dt.datetime:
    """'2025-12-15' -> noon Montréal time that day; '2025-12-15T09:00' -> that local time;
    anything with an offset is kept as is. Returns an aware datetime."""
    if "T" in value or " " in value:
        when = dt.datetime.fromisoformat(value)
    else:
        when = dt.datetime.combine(dt.date.fromisoformat(value), BACKFILL_DEFAULT_TIME)
    return when if when.tzinfo else when.replace(tzinfo=LOCAL_TZ)


def iso_utc(when: dt.datetime) -> str:
    """The form Bluesky uses for createdAt, e.g. 2025-12-15T17:00:00.000Z."""
    return when.astimezone(dt.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def graphemes(text: str) -> int:
    return len(regex.findall(r"\X", text))


@dataclass
class Draft:
    folder: Path
    text: str
    alt: str
    image_path: Path
    backfill: dt.datetime | None = None  # post's createdAt; None = now
    backfill_error: str = ""

    @classmethod
    def load(cls, folder: Path, image_path: Path) -> "Draft":
        read = lambda name: (folder / name).read_text(encoding="utf-8").strip() if (folder / name).exists() else ""
        draft = cls(folder, read("post-bsky.txt"), read("alt.txt"), image_path)
        data_file = folder / "data.json"
        raw = json.loads(data_file.read_text(encoding="utf-8")).get(BACKFILL_FIELD) if data_file.exists() else None
        if raw:
            try:
                draft.backfill = parse_backfill(str(raw))
            except ValueError:
                draft.backfill_error = f'{BACKFILL_FIELD} "{raw}" in data.json is not a date (YYYY-MM-DD) or ISO datetime.'
        return draft

    def problems(self) -> list[str]:
        out = []
        if self.backfill_error:
            out.append(self.backfill_error)
        if self.backfill and self.backfill > dt.datetime.now(dt.timezone.utc):
            out.append(f"{BACKFILL_FIELD} {self.backfill:%Y-%m-%d %H:%M} is in the future; Bluesky can't schedule posts.")
        if not self.text:
            out.append(f"{self.folder / 'post-bsky.txt'} is missing or empty.")
        n = graphemes(self.text)
        if n > MAX_POST_GRAPHEMES:
            out.append(f"post-bsky.txt is {n} characters; Bluesky allows {MAX_POST_GRAPHEMES}.")
        if len(self.alt) > MAX_ALT_CHARS:
            out.append(f"alt.txt is {len(self.alt)} characters; the Bluesky app allows {MAX_ALT_CHARS}.")
        if not self.alt:
            out.append(f"{self.folder / 'alt.txt'} is missing or empty.")
        if not self.image_path.exists():
            out.append(f"Image not found: {self.image_path} (run `poe render` first).")
        return out


def jpeg_under_limit(path: Path) -> tuple[bytes, tuple[int, int]]:
    """Re-encode the image as JPEG, stepping quality down until it fits Bluesky's 1 MB limit."""
    img = Image.open(path).convert("RGB")
    for quality in range(95, 59, -5):
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
        if buf.tell() <= MAX_IMAGE_BYTES:
            return buf.getvalue(), img.size
    raise ValueError(f"Couldn't get {path} under {MAX_IMAGE_BYTES} bytes as JPEG")


def post_url(handle: str, uri: str) -> str:
    """at://did/app.bsky.feed.post/<rkey>  ->  https://bsky.app/profile/<handle>/post/<rkey>"""
    return f"https://bsky.app/profile/{handle}/post/{uri.rsplit('/', 1)[-1]}"


def existing_record(folder: Path) -> dict | None:
    p = folder / RECORD_FILE
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def publish(draft: Draft, handle: str, password: str) -> dict:
    from atproto import Client, models

    image, (w, h) = jpeg_under_limit(draft.image_path)
    client = Client()
    client.login(handle, password)
    # Same steps as client.send_image(), but building the record ourselves so createdAt can be
    # backdated for backfill posts.
    blob = client.upload_blob(image).blob
    embed = models.AppBskyEmbedImages.Main(images=[
        models.AppBskyEmbedImages.Image(
            alt=draft.alt, image=blob, aspect_ratio=models.AppBskyEmbedDefs.AspectRatio(width=w, height=h)
        )
    ])
    created_at = iso_utc(draft.backfill) if draft.backfill else client.get_current_time_iso()
    post = models.AppBskyFeedPost.Record(
        created_at=created_at,
        text=draft.text,
        facets=client.detect_facets(draft.text),  # links, hashtags, and mentions resolved to DIDs
        embed=embed,
        langs=["fr", "en"],
    )
    resp = client.app.bsky.feed.post.create(client.me.did, post)
    record = {
        "uri": resp.uri,
        "cid": resp.cid,
        "url": post_url(handle, resp.uri),
        "handle": handle,
        "image": draft.image_path.name,
        "posted_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "created_at": created_at,  # what Bluesky shows as the post date (differs when backfilled)
    }
    (draft.folder / RECORD_FILE).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record

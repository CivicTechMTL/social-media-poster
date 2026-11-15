"""Post an event's image to Bluesky.

Reads data/<n>/post-bsky.txt (post text) and data/<n>/alt.txt (image alt text), and attaches
data/<n>/img-<layout>.jpg (render it first with `poe render`). Credentials come from .env:

  BLUESKY_HANDLE=civictechmtl.bsky.social
  BLUESKY_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx    # Settings > Privacy and security > App passwords

Examples:
  poe bsky-check data/100                # check lengths/image, post nothing
  poe bsky-post data/100                 # post (asks for confirmation)
  poe bsky-post data/100 --layout open   # (or: python -m src.bsky_post ...)

Backfill: if data.json has "bsky-backfill-date" (e.g. "2025-12-15"), the post is backdated to noon
Montréal time that day (or to the exact time, if it's a full ISO datetime). Bluesky shows such
posts with an "Archived from <date>" label.

After posting, data/<n>/bluesky.json records the post; the script refuses to post the same
event twice unless you pass --force.
"""

from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv

from .posting.bluesky import (
    BACKFILL_FIELD,
    LOCAL_TZ,
    MAX_ALT_CHARS,
    MAX_POST_GRAPHEMES,
    Draft,
    existing_record,
    graphemes,
    jpeg_under_limit,
    publish,
)
from .shared.paths import ENV_FILE, LAYOUTS, display, event_folder, image_path


def main() -> int:
    # Windows consoles default to cp1252, which can't print «», “” or the rules below.
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("event", type=event_folder, help="event folder, e.g. data/100 (data/2 finds data/002)")
    ap.add_argument("--layout", choices=LAYOUTS, default="card")
    ap.add_argument("--dry-run", action="store_true", help="validate and preview only; don't post")
    ap.add_argument("--yes", "-y", action="store_true", help="skip the confirmation prompt")
    ap.add_argument("--force", action="store_true", help="post even if this event was already posted")
    args = ap.parse_args()

    draft = Draft.load(args.event, image_path(args.event, args.layout))

    print("─── Post text " + "─" * 40)
    print(draft.text)
    print(f"─── {graphemes(draft.text)}/{MAX_POST_GRAPHEMES} characters\n")
    print("─── Alt text " + "─" * 41)
    print(draft.alt)
    print(f"─── {len(draft.alt)}/{MAX_ALT_CHARS} characters\n")
    if draft.backfill:
        print(f"Backdated to: {draft.backfill.astimezone(LOCAL_TZ):%a %Y-%m-%d %H:%M %Z} ({BACKFILL_FIELD})")

    problems = draft.problems()
    if not problems:
        jpeg, (w, h) = jpeg_under_limit(draft.image_path)
        print(f"Image: {display(draft.image_path)} -> JPEG {len(jpeg) / 1e6:.2f} MB, {w}×{h}")
    if problems:
        print("\n".join(f"✗ {p}" for p in problems), file=sys.stderr)
        return 1

    prior = existing_record(args.event)
    if prior and not args.force:
        print(f"\nAlready posted on {prior['posted_at']}: {prior['url']}\nUse --force to post again.")
        return 1

    if args.dry_run:
        print("\nDry run: nothing posted.")
        return 0

    load_dotenv(ENV_FILE)
    handle, password = os.getenv("BLUESKY_HANDLE"), os.getenv("BLUESKY_APP_PASSWORD")
    if not handle or not password:
        print("✗ Set BLUESKY_HANDLE and BLUESKY_APP_PASSWORD in .env (see .env.example).", file=sys.stderr)
        return 1

    when = f" backdated to {draft.backfill.astimezone(LOCAL_TZ):%Y-%m-%d %H:%M}" if draft.backfill else ""
    if not args.yes and input(f"\nPost this to Bluesky as @{handle}{when}? [y/N] ").strip().lower() != "y":
        print("Cancelled.")
        return 1

    record = publish(draft, handle, password)
    print(f"\n✓ Posted: {record['url']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

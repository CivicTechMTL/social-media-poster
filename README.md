# Civic Tech Montréal Social Media Poster

**English** | [Français](README.fr.md)

A set of tools for generating 1080×1080 bilingual (FR/EN) promo images for
[Civic Tech Montréal](https://mtl.civictech.ca/) meetups, on a blob-gradient background whose colours
follow Montréal's seasons, and posting them to social media.

You can render the images, preview them in a browser, and post them to Bluesky with their alt text
(including backdated posts for past events). Instagram captions and alt text live alongside them for
posting by hand.

## Setup

Needs Python 3.10+. From the project folder, dot-source the setup script for your shell:

```powershell
. .\setup.ps1        # PowerShell
```

```sh
source setup.sh      # bash/zsh (macOS, Linux, Git Bash)
```

It creates `.venv` if needed, activates it in your current shell, installs the Python packages and
Playwright's Chromium, and copies `.env.example` to `.env` if there isn't one yet. Re-run it any time
to pick up new dependencies or to re-activate the venv in a new terminal. If PowerShell blocks the
script, run `Set-ExecutionPolicy -Scope Process Bypass` first.

## Tasks

Common commands are [Poe the Poet](https://poethepoet.natn.io/) tasks, defined in `pyproject.toml`.
Run `poe` with no arguments to list them. Extra arguments are passed through to the script.

```sh
poe render data/100             # both layouts
poe render-all                  # both layouts for every event in data/
poe serve                       # live preview at http://localhost:8000
poe bsky-check data/100         # validate, post nothing
poe bsky-post data/100          # post (asks first)
poe bg-demo                     # year of backgrounds into out/bg-demo/
poe logo                        # regenerate assets/logo-white.png
```

Every script option works through its task, e.g. `poe render data/100 --reroll 2`. Run
`poe render --help` (or any task with `--help`) to see the options.

## Making an image

### 1. Add the event data

Create `data/<number>/data.json` and drop the speaker photo(s) beside it. Folder names are zero-padded
to three digits so they sort properly (`data/007`, `data/010.5`), but commands accept either form:
`poe render data/7` finds `data/007`.

```json
{
  "number": 100,
  "date": "2031-02-06",
  "time": "18:30",
  "format": "hybrid",
  "speakers": [
    { "name": "Bonhomme de Neige", "photo": "bonhomme.jpg" }
  ],
  "talk": {
    "fr": "Zéro nid-de-poule : une ville réparée par ses citoyens",
    "en": "Pothole Zero: A City Fixed by Its Citizens"
  }
}
```

- `format`: `hybrid` | `in-person` | `online`
- `speakers`: zero (hacknight), one or two. Optional `"photo_position": "50% 30%"` nudges the circular crop.
- Text before a `:` in the talk title is set in bold.
- Optional `"series": "Hacknight"` changes the heading from "Meetup #N".
- Optional `"hide_photos": true` drops the photo circles but keeps the speaker names.

> **TODO:** Add support for 3+ speakers

### 2. Render

```sh
poe render data/100                 # -> data/100/img-card.jpg + img-open.jpg
poe render data/100 --layout card   # -> data/100/img-card.jpg only
poe render data/100 --layout open   # -> data/100/img-open.jpg only
poe render data/100 --reroll 2      # new blob background arrangement (overwrites bg.jpg)

poe render-all                     # every layout for every event in data/
```

The background lives in the event folder as `bg.jpg`: it's generated on the first render and
reused after that, so every layout and re-render shares it. `--reroll` replaces it.

Any `bg.jpg` already in the folder is used as is, so you can drop in your own background (ideally
1080×1080; other sizes are scaled and centre-cropped). It won't be overwritten unless you pass
`--reroll`.

To use a premade image instead (as for meetup 9), save it in the folder as `img-card.jpg` /
`img-open.jpg` and add `"premade": true` to `data.json`; rendering then skips that event (and
`render-all` leaves it out).

Layouts: `card` (frosted panel) or `open` (text straight on the background).
Talk text auto-sizes to fill its space. French and English share the same styling;
French is left-aligned, English right-aligned.

## Previewing images

```sh
poe serve            # http://localhost:8000
```

Lists every event in `data/`, with a link per layout. Pages are the exact
HTML that gets screenshotted, so you can use DevTools to inspect and tweak the CSS. Templates are re-read
on each refresh; restart the server after changing Python code. Pages use the event's `bg.jpg` when
it exists. Add `?reroll=x` to try another background; previews never write `bg.jpg`.

## Posting

### Bluesky

1. Copy `.env.example` to `.env` and fill in the handle and an
   [app password](https://bsky.app/settings/app-passwords) (not the account password).
2. Add `post-bsky.txt` (post text, max 300 characters, URLs become links) beside the event's
   `data.json`. The image alt text comes from the shared `alt.txt` (see below).
3. Render the image, check, then post:

   ```sh
   poe render data/100
   poe bsky-check data/100   # shows text, lengths, image size; posts nothing
   poe bsky-post data/100    # asks before posting
   ```

The image is converted to JPEG to fit Bluesky's 1 MB limit. After posting, `data/<n>/bluesky.json`
records the post URL, and `poe bsky-post` won't post that event again unless you pass `--force`.

**Backfilling past events:** add `"bsky-backfill-date": "2025-12-15"` to `data.json` and the post is
backdated to noon Montréal time that day (or give a full time, e.g. `"2025-12-15T09:30"`).
`bsky-check` shows the date it will use. Bluesky marks backdated posts as archived and sorts them by
that date, so they won't land at the top of followers' feeds.

### Instagram

Instagram is posted by hand. Beside each event's `data.json`, `post-insta.txt` holds the caption
(English, then French, max 2,200 characters) and `alt.txt` holds the image alt text (English, then French), shared with Bluesky. Use the `card`
image.

## Other tools

- `poe bg-demo` - renders a year of fortnightly backgrounds into `out/bg-demo/` with a contact sheet.
- `poe logo` - regenerates `assets/logo-white.png` from the teal logo, `assets/logo-teal.png`.
- `tools/luma-set-cover.js` - paste into the DevTools console on luma.com to set events' cover images
  from `data/<n>/img-open.jpg` (pick the `data` folder, tick the events). See the comments at the top.

## Layout

```
src/            The code; the scripts behind the poe tasks sit at the top level
  shared/       Used by both sides: paths and data.json loading
  images/       Image generation: seasonal backgrounds and HTML → JPEG rendering
  posting/      Posting to social media (Bluesky)
templates/      Jinja HTML templates for each layout
assets/         Fonts and logos, plus account bios (_refs/ is local only, not in git)
data/           One folder per event (zero-padded: 002, 010.5): data.json, post text, alt text, images
tools/          One-off helpers (logo generator, Luma cover uploader)
```

The scripts are run as modules from the project root (e.g. `python -m src.make_image`), which
is what the `poe` tasks do.

"""Event data loading and bilingual (FR/EN) formatting."""

from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass, field
from pathlib import Path

FR_DAYS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
FR_MONTHS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
             "août", "septembre", "octobre", "novembre", "décembre"]
FR_MONTHS_SHORT = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.",
                   "août", "sept.", "oct.", "nov.", "déc."]
FR_TILE = ["JANV", "FÉVR", "MARS", "AVR", "MAI", "JUIN", "JUIL", "AOÛT", "SEPT", "OCT", "NOV", "DÉC"]
EN_TILE = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

FORMATS = {
    "hybrid": ("En personne et en ligne", "In person & online"),
    "in-person": ("En personne", "In person"),
    "online": ("En ligne", "Online"),
}


@dataclass
class Speaker:
    name: str
    photo: Path | None = None
    photo_position: str = "50% 35%"  # CSS object-position, to nudge the crop
    initials_text: str | None = None  # overrides the photo-less circle text, e.g. "?"
    placeholder: bool = False  # "to be announced" speaker: name set in italics

    @property
    def initials(self) -> str:
        if self.initials_text is not None:
            return self.initials_text
        parts = [p for p in self.name.replace("-", " ").split() if p]
        return (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")).upper()


@dataclass
class Title:
    prefix: str  # bold lead-in incl. colon, e.g. "Zéro nid-de-poule :" (may be empty)
    rest: str


@dataclass
class Event:
    number: str  # string so e.g. "10.5" works
    date: dt.date
    time: dt.time
    format: str
    talk_fr: str
    talk_en: str
    speakers: list[Speaker] = field(default_factory=list)
    folder: Path | None = None
    series: str = "Meetup"  # heading word: "Meetup #N" or e.g. "Hacknight #N"
    hide_photos: bool = False  # no photo circles, e.g. when no speaker photo exists

    # ---- loading -----------------------------------------------------------
    @classmethod
    def load(cls, folder: str | Path) -> "Event":
        folder = Path(folder)
        d = json.loads((folder / "data.json").read_text(encoding="utf-8"))
        raw = d.get("speakers")
        if raw is None and "speaker" in d:  # accept the single-speaker shorthand
            raw = [d["speaker"]]
        speakers = []
        for s in raw or []:
            if isinstance(s, str):
                s = {"name": s}
            photo = folder / s["photo"] if s.get("photo") else None
            speakers.append(Speaker(s["name"], photo, s.get("photo_position", "50% 35%"), s.get("initials"), bool(s.get("placeholder"))))
        return cls(
            number=str(d["number"]),
            date=dt.date.fromisoformat(d["date"]),
            time=dt.time.fromisoformat(d["time"]),
            format=d.get("format", "hybrid"),
            talk_fr=d["talk"]["fr"],
            talk_en=d["talk"]["en"],
            speakers=speakers,
            folder=folder,
            series=d.get("series", "Meetup"),
            hide_photos=bool(d.get("hide_photos", False)),
        )

    # ---- titles --------------------------------------------------------------
    @staticmethod
    def _split(title: str) -> Title:
        if ":" in title:
            head, tail = title.split(":", 1)
            # French puts a (non-breaking) space before the colon.
            sep = " :" if head.endswith(" ") else ":"
            return Title(head.rstrip() + sep, tail.strip())
        return Title("", title)

    @property
    def title_fr(self) -> Title:
        return self._split(self.talk_fr)

    @property
    def title_en(self) -> Title:
        return self._split(self.talk_en)

    @property
    def speaker_names(self) -> str:
        names = [s.name for s in self.speakers]
        return " & ".join(names)

    # ---- dates & times -------------------------------------------------------
    @property
    def day_fr(self) -> str:
        n = self.date.day
        return "1er" if n == 1 else str(n)

    @property
    def date_fr(self) -> str:  # jeudi 12 novembre
        return f"{FR_DAYS[self.date.weekday()]} {self.day_fr} {FR_MONTHS[self.date.month - 1]}"

    @property
    def date_en(self) -> str:  # Thursday, November 12
        return f"{self.date:%A}, {self.date:%B} {self.date.day}"

    @property
    def date_fr_short(self) -> str:  # jeu. 12 nov.
        return f"{FR_DAYS[self.date.weekday()][:3]}. {self.day_fr} {FR_MONTHS_SHORT[self.date.month - 1]}"

    @property
    def date_en_short(self) -> str:  # Thu Nov 12
        return f"{self.date:%a} {self.date:%b} {self.date.day}"

    @property
    def time_fr(self) -> str:  # 18 h / 18 h 30
        t = self.time
        return f"{t.hour} h" + (f" {t.minute:02d}" if t.minute else "")

    @property
    def time_en(self) -> str:  # 6 pm / 6:30 pm
        t = self.time
        h = t.hour % 12 or 12
        return f"{h}" + (f":{t.minute:02d}" if t.minute else "") + (" am" if t.hour < 12 else " pm")

    @property
    def tile_month(self) -> str:  # NOV  or  DÉC · DEC
        fr, en = FR_TILE[self.date.month - 1], EN_TILE[self.date.month - 1]
        return fr if fr == en else f"{fr} · {en}"

    @property
    def tile_weekday(self) -> str:  # JEU · THU
        return f"{FR_DAYS[self.date.weekday()][:3].upper()} · {self.date:%a}".upper()

    @property
    def format_fr(self) -> str:
        return FORMATS[self.format][0]

    @property
    def format_en(self) -> str:
        return FORMATS[self.format][1]

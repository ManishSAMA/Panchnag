"""The Laghu booklet prints its festival column entirely in Hindi.

A few registry entries carried only an English name (Ravi Vrat, Karma Nirjara
Vrat, one Mahavir Moksha entry, a "Pushpadant" spelling the translation table
missed), so the Hindi booklet showed English text and emoji. Found reviewing the
2027 Vrindavan booklet for New Delhi.
"""

from __future__ import annotations

import re
from functools import cache

import pytest

from laghu_panchang import build_laghu_year

NOT_HINDI = re.compile(r"[A-Za-z]|[\U0001F300-\U0001FAFF☀-➿️]")


@cache
def _events(profile: str) -> tuple[tuple[str, str], ...]:
    halves = build_laghu_year(year=2027, lat=28.6139, lon=77.2090, tz_name="Asia/Kolkata", profile=profile)
    return tuple((day.date.isoformat(), day.events) for half in halves for day in half.days)


@pytest.mark.parametrize("profile", ["all", "shwetambar_murtipujak_tapagachchha"])
def test_the_festival_column_has_no_english_or_emoji(profile):
    offenders = [(day, part) for day, events in _events(profile) for part in events.split(", ") if NOT_HINDI.search(part)]

    assert offenders == []


def test_the_renamed_vrats_read_in_hindi():
    text = " ".join(events for _, events in _events("all"))

    assert "रवि व्रत" in text
    assert "कर्म निर्जरा व्रत (श्रावण)" in text
    assert "श्री पुष्पदंत (सुविधिनाथ) भगवान गर्भ कल्याणक" in text

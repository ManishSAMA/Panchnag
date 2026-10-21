"""Cell formatting for the Laghu Panchang booklet.

The layout and notation follow the printed "laghu panchang 2027" booklet the
user supplied as the reference (times past midnight run on as 25:47, a Pratipada
cell carries the month as "पौ.शु. 01", Bhadra reads "भ. 25:47 से 14:24 तक").
"""

from __future__ import annotations

import re

import pytest

from laghu_panchang import (
    bhadra_text,
    clock_from_midnight,
    end_time_cell,
    festival_text,
    moon_sign_cell,
    panchak_text,
    shubh_mark,
    tithi_cell,
)

MIDNIGHT = 2461406.5
HOUR = 1.0 / 24.0
MINUTE = 1.0 / 1440.0


def _at(hours: float, minutes: float = 0.0) -> float:
    return MIDNIGHT + hours * HOUR + minutes * MINUTE


# ── clock ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "hours, minutes, expected",
    [(7, 19, "07:19"), (13, 10, "13:10"), (25, 47, "25:47"), (0, 0, "00:00"), (30, 5, "30:05")],
)
def test_clock_counts_hours_from_the_civil_days_midnight(hours, minutes, expected):
    assert clock_from_midnight(_at(hours, minutes), MIDNIGHT) == expected


def test_clock_drops_the_seconds_like_the_apps_other_outputs():
    """The exports, PDFs and Drik Panchang all drop seconds: 03:54:59 reads 03:54."""
    assert clock_from_midnight(_at(9, 59.7), MIDNIGHT) == "09:59"
    assert clock_from_midnight(_at(3, 54.98), MIDNIGHT) == "03:54"


def test_clock_is_not_thrown_by_floating_point_just_below_the_minute():
    assert clock_from_midnight(_at(7, 19) - 1e-9, MIDNIGHT) == "07:19"


def test_an_element_outlasting_the_next_sunrise_is_ahoratra():
    next_sunrise = _at(31, 19)

    assert end_time_cell(_at(31, 30), midnight_jd=MIDNIGHT, next_sunrise_jd=next_sunrise) == "अहोरात्र"
    assert end_time_cell(_at(25, 47), midnight_jd=MIDNIGHT, next_sunrise_jd=next_sunrise) == "25:47"


# ── tithi ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "index, expected",
    [(9, "9"), (15, "15"), (24, "9"), (29, "14"), (30, "30")],
)
def test_tithi_is_numbered_within_its_paksha_with_amavasya_as_30(index, expected):
    assert tithi_cell(index, month_name="Pausha") == expected


@pytest.mark.parametrize(
    "index, month, expected",
    [(1, "Pausha", "पौ.शु. 01"), (16, "Magha", "मा.कृ. 01"), (1, "Chaitra", "चै.शु. 01")],
)
def test_pratipada_carries_the_month_and_paksha(index, month, expected):
    assert tithi_cell(index, month_name=month) == expected


def test_a_kshaya_tithi_is_shown_beside_the_prevailing_one():
    assert tithi_cell(3, month_name="Pausha", kshaya_index=4) == "3-4"


def test_an_adhika_month_is_marked_on_pratipada():
    assert tithi_cell(1, month_name="Adhika Jyeshtha") == "अ.ज्ये.शु. 01"


# ── shubh ────────────────────────────────────────────────────────────────

SUNRISE = _at(7, 19)


def _yoga(*, nature="shubh", severity="highly_auspicious", start=SUNRISE, end=_at(20), **extra):
    return {"name": "X", "nature": nature, "severity": severity, "start_jd": start, "end_jd": end, **extra}


def _day(**lists):
    return {"yogas": [], "aanandadi_yogas": [], "ravi_yogas": [], "special_yogas": [], **lists}


@pytest.mark.parametrize("kind", ["yogas", "aanandadi_yogas", "ravi_yogas", "special_yogas"])
def test_a_highly_auspicious_yoga_at_sunrise_marks_the_day_shubh(kind):
    assert shubh_mark(_day(**{kind: [_yoga()]}), SUNRISE) == "卍"


@pytest.mark.parametrize(
    "yoga",
    [
        _yoga(severity="auspicious"),
        _yoga(nature="ashubh"),
        _yoga(start=_at(10)),
        _yoga(end=SUNRISE),
        _yoga(is_nullified=True),
        _yoga(cancelled=True),
    ],
    ids=["merely-auspicious", "ashubh", "starts-after-sunrise", "ends-at-sunrise", "nullified", "cancelled"],
)
def test_other_days_are_not_shubh(yoga):
    assert shubh_mark(_day(aanandadi_yogas=[yoga]), SUNRISE) == "-"


# ── moon sign ────────────────────────────────────────────────────────────

def test_the_moon_sign_is_named_in_full_when_it_holds_all_day():
    assert moon_sign_cell(6, None, None, midnight_jd=MIDNIGHT) == "तुला"


def test_a_sign_entry_shows_the_new_sign_abbreviated_with_its_time():
    assert moon_sign_cell(0, 1, _at(28, 21), midnight_jd=MIDNIGHT) == "वृ.-28:21"


# ── bhadra / panchak ─────────────────────────────────────────────────────

def _window(start, end, *, clipped_start=False, clipped_end=False):
    return {"start_jd": start, "end_jd": end, "clipped_start": clipped_start, "clipped_end": clipped_end}


def test_bhadra_inside_the_day_shows_both_ends():
    assert bhadra_text([_window(_at(16, 31), _at(29, 18))], midnight_jd=MIDNIGHT) == "भ. 16:31 से 29:18 तक"


def test_bhadra_running_into_or_out_of_the_day_shows_one_end():
    assert bhadra_text([_window(_at(25, 47), _at(31, 19), clipped_end=True)], midnight_jd=MIDNIGHT) == "भ. 25:47 से"
    assert bhadra_text([_window(_at(7, 19), _at(14, 24), clipped_start=True)], midnight_jd=MIDNIGHT) == "भ. 14:24 तक"


def test_bhadra_split_at_a_moon_sign_change_reads_as_one_window():
    windows = [_window(_at(10), _at(12, 30)), _window(_at(12, 30), _at(22, 28))]

    assert bhadra_text(windows, midnight_jd=MIDNIGHT) == "भ. 10:00 से 22:28 तक"


def test_no_bhadra_is_empty():
    assert bhadra_text([], midnight_jd=MIDNIGHT) == ""


def test_panchak_shows_its_start_or_end_but_not_days_wholly_inside_it():
    assert panchak_text([_window(_at(28, 34), _at(31, 19), clipped_end=True)], midnight_jd=MIDNIGHT) == "पंचक 28:34 से"
    assert panchak_text([_window(_at(7, 19), _at(23, 51), clipped_start=True)], midnight_jd=MIDNIGHT) == "पंचक 23:51 तक"
    whole_day = _window(_at(7, 19), _at(31, 19), clipped_start=True, clipped_end=True)
    assert panchak_text([whole_day], midnight_jd=MIDNIGHT) == ""
    assert panchak_text([], midnight_jd=MIDNIGHT) == ""


# ── festivals ────────────────────────────────────────────────────────────

def test_festivals_are_listed_once_each_in_hindi_without_school_tags():
    festivals = [
        {"name": "Shitalnath Omniscience", "name_hindi": "श्री शीतलनाथ ज्ञान कल्याणक", "sources": ["Vrindavan"]},
        {"name": "Shitalnath Omniscience", "name_hindi": "श्री शीतलनाथ ज्ञान कल्याणक", "sources": ["Ashadhara"]},
        {"name": "Paush Dashami", "name_hindi": "पौष दशमी"},
    ]

    text = festival_text(festivals)

    assert text == "श्री शीतलनाथ ज्ञान कल्याणक, पौष दशमी"
    assert not re.search(r"\(\d", text)


def test_a_kalyanaks_native_tithi_tag_is_shown_in_hindi():
    """festival_service prefixes "[Ekadashi] " when a Kalyanak sits on a civil date of another tithi."""
    festivals = [{"name": "[Ekadashi] Shri Ajitnath Ji - Omniscience Kalyanak", "name_hindi": "[Ekadashi] Shri Ajitnath Ji - Omniscience Kalyanak"}]

    assert festival_text(festivals).startswith("[एकादशी] ")


def test_a_multi_day_marker_already_in_the_name_is_not_repeated():
    festivals = [{"name": "Solah Karan Vrat", "name_hindi": "सोलह कारण व्रत प्रारम्भ (प्रारंभ)", "_tag": "प्रारंभ"}]

    assert festival_text(festivals) == "सोलह कारण व्रत प्रारम्भ (प्रारंभ)"

"""Kshaya (skipped) Tithi rendering.

A Tithi that begins and ends between two consecutive Jain day-starts never
prevails at any 6-ghati mark, so it appears on no civil day and the printed
sequence jumps -- 13 straight to 15, or Navami straight to Ekadashi. Readers
reasonably conclude the calendar is broken.

Where that happens, the preceding day carries both: "13/14",
"कृष्ण त्रयोदशी/चतुर्दशी". 2026 has 18 such days.
"""

from datetime import date

import pytest

from hindi_calendar_pdf import build_month_rows, format_tithi_pair
from panchang import kshaya_tithi_between


LAT, LON, TZ_OFFSET, AYANAMSA = 26.9124, 75.7873, 5.5, "Lahiri"


# ── Detection ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("current,following,skipped", [
    (13, 15, 14),   # Krishna/Shukla Trayodashi -> Purnima, Chaturdashi lost
    (10, 12, 11),   # Dashami -> Dwadashi, Ekadashi lost
    (28, 30, 29),   # Krishna 13 -> Amavasya (2026-03-17)
    (9, 11, 10),    # 2026-03-27
    (30, 2, 1),     # Amavasya -> Shukla Dwitiya, Pratipada lost (2026-06-15)
    (29, 1, 30),    # Chaturdashi -> Shukla Pratipada, Amavasya lost
])
def test_a_one_tithi_gap_is_reported_as_kshaya(current, following, skipped):
    assert kshaya_tithi_between(current, following) == skipped


@pytest.mark.parametrize("current,following", [
    (13, 14),   # ordinary progression
    (30, 1),    # ordinary month rollover
    (15, 16),   # Purnima -> Krishna Pratipada
    (13, 13),   # vriddhi: the same Tithi holds two day-starts
    (1, 1),
])
def test_ordinary_and_repeated_progressions_are_not_kshaya(current, following):
    assert kshaya_tithi_between(current, following) is None


def test_a_gap_of_more_than_one_is_not_treated_as_kshaya():
    """Two Tithis cannot both vanish between consecutive day-starts.

    A jump that large means something else is wrong -- a missing day, a bad
    sunrise -- and silently printing "13/14" would hide it.
    """
    assert kshaya_tithi_between(13, 16) is None
    assert kshaya_tithi_between(9, 12) is None


# ── Rendering ────────────────────────────────────────────────────────────────

def test_a_normal_day_renders_the_single_tithi():
    assert format_tithi_pair(13, None) == "शुक्ल त्रयोदशी (तेरस)"


def test_a_kshaya_day_renders_both_names_slash_separated():
    assert format_tithi_pair(13, 14) == "शुक्ल त्रयोदशी (तेरस)/चतुर्दशी (चौदस)"


def test_the_paksha_is_not_repeated_when_both_share_one():
    rendered = format_tithi_pair(10, 11)
    assert rendered.count("शुक्ल") == 1
    assert rendered == "शुक्ल दशमी/एकादशी (ग्यारस)"


def test_a_kshaya_crossing_the_paksha_boundary_names_both_pakshas():
    """30 -> 2 loses Shukla Pratipada, which sits in the next paksha."""
    assert format_tithi_pair(30, 1) == "कृष्ण अमावस्या/शुक्ल प्रथमा (एकम)"


def test_purnima_and_amavasya_keep_their_names_in_a_pair():
    assert format_tithi_pair(14, 15) == "शुक्ल चतुर्दशी (चौदस)/पूर्णिमा"
    assert format_tithi_pair(29, 30) == "कृष्ण चतुर्दशी (चौदस)/अमावस्या"


# ── Integration with the PDF rows ────────────────────────────────────────────

def _rows(year, month):
    return build_month_rows(
        year, month, lat=LAT, lon=LON, tz_offset=TZ_OFFSET,
        ayanamsa=AYANAMSA, date_to_fests={},
    )


def test_the_known_kshaya_day_renders_a_pair_in_the_pdf_rows():
    """2026-03-17 is Krishna 13 with Chaturdashi lost before Amavasya."""
    row = next(r for r in _rows(2026, 3) if r["day_num"] == 17)
    assert "/" in row["jain_tithi"]
    assert row["jain_tithi"].startswith("कृष्ण त्रयोदशी")


def test_days_either_side_of_a_kshaya_are_untouched():
    rows = {r["day_num"]: r for r in _rows(2026, 3)}
    assert "/" not in rows[16]["jain_tithi"]
    assert "/" not in rows[18]["jain_tithi"]


def test_march_2026_has_exactly_the_expected_kshaya_days():
    """17 and 27 March -- verified against the ephemeris sweep for 2026."""
    flagged = [r["day_num"] for r in _rows(2026, 3) if "/" in r["jain_tithi"]]
    assert flagged == [17, 27]


def test_the_hindu_tithi_column_is_left_alone():
    """Detection is defined on the Jain Tithi; the sunrise column is untouched."""
    rows = _rows(2026, 3)
    assert not any("/" in r["hindu_tithi"] for r in rows)


def test_a_kshaya_row_still_carries_every_column():
    row = next(r for r in _rows(2026, 3) if r["day_num"] == 17)
    for field in ("date_str", "vara", "h_month", "hindu_tithi", "jain_tithi",
                  "sunrise", "sunset", "festivals"):
        assert field in row


# ── English naming, for the web views ────────────────────────────────────────

from panchang import format_tithi_pair_name  # noqa: E402


def test_english_pair_states_the_paksha_once():
    assert format_tithi_pair_name(10, 11) == "Shukla Dashami/Ekadashi"


def test_english_single_tithi_is_unchanged():
    assert format_tithi_pair_name(10, None) == "Shukla Dashami"


def test_english_pair_keeps_both_names_when_the_paksha_changes():
    assert format_tithi_pair_name(30, 1) == "Amavasya/Shukla Pratipada"
    assert format_tithi_pair_name(14, 15) == "Shukla Chaturdashi/Purnima"
    assert format_tithi_pair_name(29, 30) == "Krishna Chaturdashi/Amavasya"


# ── Month overview API ───────────────────────────────────────────────────────

def test_month_overview_marks_the_kshaya_day():
    """The calendar grid is where a broken-looking sequence is most visible."""
    from app import create_app

    client = create_app().test_client()
    payload = client.get(
        f"/month-overview?year=2026&month=3&lat={LAT}&lon={LON}"
    ).get_json()

    by_day = {d["date"]: d for d in payload["days"]}
    seventeenth = by_day["2026-03-17"]

    assert seventeenth["kshaya_tithi"] == 29
    assert "/" in seventeenth["tithi_name"]

    assert by_day["2026-03-16"]["kshaya_tithi"] is None
    assert "/" not in by_day["2026-03-16"]["tithi_name"]

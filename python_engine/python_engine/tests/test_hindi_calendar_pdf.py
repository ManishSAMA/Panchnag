"""Hindi calendar PDF: column schema, month convention and school tags.

The three generate_hindi_calendar_pdf*.py scripts were near-identical copies
with no testable seam -- running one wrote a whole multi-month PDF to disk. The
logic now lives in hindi_calendar_pdf.py as plain functions, which is what these
tests exercise.

Three behaviours are pinned here:

* the table carries BOTH tithis -- Hindu at plain sunrise, Jain at sunrise +
  6 ghati -- where it previously carried only one column (which was already the
  Jain one, confusingly labelled "पक्ष एवं तिथि");
* the month column follows the Purnimanta convention, matching the printed
  North Indian panchang and the web app's default;
* festival names carry a school-consensus tag, 1 = Vrindavan,
  2 = Uttarapurana, 3 = Ashadhara.
"""

from datetime import date

import pytest

from hindi_calendar_pdf import (
    SCHOOLS,
    build_month_rows,
    hindi_greg_month,
    merge_day_festivals,
    school_tag,
)


LAT, LON, TZ_OFFSET, AYANAMSA = 26.9124, 75.7873, 5.5, "Lahiri"  # Jaipur


# ── School consensus tags ────────────────────────────────────────────────────

def test_schools_are_numbered_in_the_documented_order():
    assert SCHOOLS == ("Vrindavan", "Uttarapurana", "Ashadhara")


@pytest.mark.parametrize("sources,expected", [
    (["Vrindavan", "Uttarapurana", "Ashadhara"], "(1, 2, 3)"),
    (["Uttarapurana", "Ashadhara"],              "(2, 3)"),
    (["Vrindavan", "Ashadhara"],                 "(1, 3)"),
    (["Vrindavan"],                              "(1)"),
    (["Ashadhara"],                              "(3)"),
])
def test_recognised_schools_produce_an_ascending_tag(sources, expected):
    assert school_tag(sources) == expected


@pytest.mark.parametrize("sources", [
    ["Jain Traditions"],
    ["Pt. Jaini Jiyalal Panchang"],
    ["Vrat Vidhi Sangrah", "Panchang Traditions"],
    [],
    None,
])
def test_festivals_with_no_recognised_school_get_no_bracket(sources):
    """74 of 209 registry entries are ordinary observances, not Kalyanaks."""
    assert school_tag(sources) == ""


def test_tag_matching_ignores_case_and_surrounding_text():
    assert school_tag(["uttarapurana commentary", "ASHADHARA"]) == "(2, 3)"


def test_tag_order_does_not_follow_the_source_list_order():
    assert school_tag(["Ashadhara", "Vrindavan"]) == "(1, 3)"


# ── Same-day merging ─────────────────────────────────────────────────────────

def test_two_entries_for_one_festival_on_one_day_merge_to_a_union_tag():
    """Schools disagreeing on a Kalyanak's tithi can still land on one date.

    2026-03-18 has exactly this for Anantnath Liberation: a (1, 3) entry and a
    (2,) entry. The reader must see one line, not two.
    """
    merged = merge_day_festivals([
        {"name": "Shri Anantnath Ji - Liberation Kalyanak", "sources": ["Vrindavan", "Ashadhara"]},
        {"name": "Shri Anantnath Ji - Liberation Kalyanak", "sources": ["Uttarapurana"]},
    ])

    assert len(merged) == 1
    assert merged[0]["sources_tag"] == "(1, 2, 3)"


def test_merging_keeps_distinct_festivals_apart():
    merged = merge_day_festivals([
        {"name": "Festival A", "sources": ["Vrindavan"]},
        {"name": "Festival B", "sources": ["Uttarapurana"]},
    ])
    assert [m["name"] for m in merged] == ["Festival A", "Festival B"]


def test_merging_preserves_first_seen_order():
    merged = merge_day_festivals([
        {"name": "Zeta", "sources": ["Vrindavan"]},
        {"name": "Alpha", "sources": ["Vrindavan"]},
        {"name": "Zeta", "sources": ["Ashadhara"]},
    ])
    assert [m["name"] for m in merged] == ["Zeta", "Alpha"]
    assert merged[0]["sources_tag"] == "(1, 3)"


# ── Gregorian month names, computed rather than tabulated ────────────────────

@pytest.mark.parametrize("year,month,expected", [
    (2026, 3, "मार्च 2026"),
    (2027, 1, "जनवरी 2027"),
    (2029, 5, "मई 2029"),      # beyond any previously hardcoded table
    (2031, 12, "दिसंबर 2031"),
])
def test_gregorian_month_names_work_for_any_year(year, month, expected):
    assert hindi_greg_month(year, month) == expected


# ── Row schema ───────────────────────────────────────────────────────────────

def _rows(year, month, calendar_system="purnimanta"):
    return build_month_rows(
        year, month, lat=LAT, lon=LON, tz_offset=TZ_OFFSET,
        ayanamsa=AYANAMSA, date_to_fests={}, calendar_system=calendar_system,
    )


def test_every_row_carries_the_eight_column_fields():
    row = _rows(2026, 4)[0]
    for field in ("date_str", "vara", "h_month", "hindu_tithi", "jain_tithi",
                  "sunrise", "sunset", "festivals"):
        assert field in row, f"row is missing '{field}'"


def test_moon_columns_are_gone_from_the_schema():
    """The requested schema is eight columns; moonrise/moonset are dropped."""
    row = _rows(2026, 4)[0]
    assert "moonrise" not in row and "moonset" not in row


def test_the_two_tithi_columns_are_not_the_same_column_twice():
    """Across a month the sunrise tithi and the 6-ghati tithi must diverge."""
    rows = _rows(2026, 4)
    differing = [r for r in rows if r["hindu_tithi"] != r["jain_tithi"]]
    assert differing, "no day in April 2026 distinguishes the two tithis"


def test_month_column_uses_purnimanta_by_default():
    """2 Apr 2026 is Krishna 1 -- Vaishakh in the book, Chaitra under amanta."""
    rows = _rows(2026, 4)
    second = next(r for r in rows if r["day_num"] == 2)
    assert second["h_month"] == "वैशाख"


def test_amanta_remains_selectable():
    rows = _rows(2026, 4, calendar_system="amanta")
    second = next(r for r in rows if r["day_num"] == 2)
    assert second["h_month"] == "चैत्र"


def test_adhika_month_is_marked_in_hindi():
    """May 2026 opens in Pratham (Adhik) Jyeshtha under Purnimanta."""
    rows = _rows(2026, 5)
    second = next(r for r in rows if r["day_num"] == 2)
    assert second["h_month"] == "अधिक ज्येष्ठ"


def test_sunday_flag_drives_row_shading():
    rows = _rows(2026, 4)
    sundays = [r for r in rows if r["is_sunday"]]
    assert sundays
    assert all(date(2026, 4, r["day_num"]).weekday() == 6 for r in sundays)

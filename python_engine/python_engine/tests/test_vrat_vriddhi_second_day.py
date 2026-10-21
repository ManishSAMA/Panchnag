"""Vrats take the second day of a tithi vriddhi: वृद्धौ कार्या तथोत्तरा.

User decision, 2026-10-20 (plans/vrat-vriddhi-second-day.md): when a tithi holds
the Jain day-start (sunrise + 6 ghati) on two consecutive days, a vrat is kept on
the second. The maxim treats the first day as the preceding tithi, so vrat rules
see that day relabelled as the previous tithi. Kalyanaks (first day, book-
verified), parva tithis (both days), Karma Nirjara (first day, 2026-08-30
directive), the Ashtahnika span and the Sunday-bound Ravi vrats are unchanged.
"""

from __future__ import annotations

from datetime import date, timedelta

from jain_observances.festival_service import vrat_view_of_snapshots


def _snap(day: date, index: int, month: str = "ASHVIN") -> dict:
    paksha = "Shukla" if index <= 15 else "Krishna"
    in_paksha = index if index <= 15 else index - 15
    return {
        "date": day,
        "tithi": index, "jain_tithi": index,
        "paksha": paksha, "tithi_in_paksha": in_paksha,
        "jain_paksha": paksha, "jain_tithi_in_paksha": in_paksha,
        "hindu_month": month, "is_adhika": False,
        "purnimanta_month": month, "purnimanta_is_adhika": False,
        "_sunrise_tithi": index, "evening_tithi": index,
    }


def _days(*indices: int, start: date = date(2026, 10, 16), month: str = "ASHVIN") -> list[dict]:
    return [_snap(start + timedelta(days=n), index, month) for n, index in enumerate(indices)]


def _jain_tithis(snaps: list[dict]) -> list[int]:
    return [s["jain_tithi"] for s in snaps]


def test_the_first_day_of_a_vriddhi_reads_as_the_previous_tithi():
    snaps = _days(6, 7, 8, 8, 9)  # Ashtami on the 18th and 19th

    view = vrat_view_of_snapshots(snaps)

    assert _jain_tithis(view) == [6, 7, 7, 8, 9]
    assert (view[2]["tithi_in_paksha"], view[2]["jain_tithi_in_paksha"], view[2]["tithi"]) == (7, 7, 7)


def test_days_without_vriddhi_are_untouched():
    snaps = _days(6, 7, 8, 9, 10)

    assert vrat_view_of_snapshots(snaps) == snaps


def test_a_kshaya_is_not_mistaken_for_a_vriddhi():
    snaps = _days(6, 8, 9, 10)  # Saptami lost

    assert vrat_view_of_snapshots(snaps) == snaps


def test_the_originals_are_not_mutated():
    snaps = _days(7, 8, 8, 9)
    before = [dict(s) for s in snaps]

    vrat_view_of_snapshots(snaps)

    assert snaps == before


def test_a_pratipada_vriddhi_belongs_to_the_previous_pakshas_last_tithi():
    snaps = _days(14, 15, 16, 16, 17)  # Purnima, then Krishna Pratipada twice

    view = vrat_view_of_snapshots(snaps)

    assert _jain_tithis(view) == [14, 15, 15, 16, 17]
    assert view[2]["jain_paksha"] == "Shukla"
    assert view[2]["purnimanta_month"] == view[1]["purnimanta_month"]


def test_the_sunrise_and_evening_tithis_used_elsewhere_are_kept():
    snaps = _days(7, 8, 8, 9)

    view = vrat_view_of_snapshots(snaps)

    assert (view[1]["_sunrise_tithi"], view[1]["evening_tithi"]) == (8, 8)


# ── the festival engine, New Delhi 2026-2027 ────────────────────────────

from functools import cache

import pytest

from jain_observances.festival_service import generate_jain_festivals

DELHI = (28.6139, 77.2090)
PROFILE = "shwetambar_murtipujak_tapagachchha"


@cache
def _festivals(year: int) -> tuple:
    return tuple(generate_jain_festivals(year, *DELHI, "Lahiri", PROFILE)["festivals"])


def _dates(year: int, *, name: str | None = None, fid: str | None = None) -> set[str]:
    return {
        f["start_date"] for f in _festivals(year)
        if (name is None or f["name"] == name) and (fid is None or f["id"].startswith(fid))
    }


@pytest.mark.parametrize(
    "first, second",
    [("2026-01-10", "2026-01-11"), ("2026-08-26", "2026-08-27"), ("2026-10-18", "2026-10-19"),
     ("2027-05-28", "2027-05-29"), ("2027-08-15", "2027-08-16")],
)
def test_bhaktamar_vrat_moves_to_the_second_day_of_the_vriddhi(first, second):
    dates = _dates(int(first[:4]), name="Bhaktambar Vrat")

    assert second in dates
    assert first not in dates


def test_jeev_daya_ashtami_moves_to_the_second_ashtami():
    assert "2026-10-19" in _dates(2026, fid="jeev_daya_ashtami")
    assert "2026-10-18" not in _dates(2026, fid="jeev_daya_ashtami")


def test_bhadrapada_dashlakshan_starts_the_day_after_samvatsari():
    [dashlakshan] = [f for f in _festivals(2026) if f["id"] == "daslakshan_Bhadrapada_2026"]
    samvatsari = _dates(2026, fid="samvatsari_tapagachchha")

    assert samvatsari == {"2026-09-15"}
    assert dashlakshan["start_date"] == "2026-09-16"


def test_pushpanjali_runs_panchami_to_navami_from_the_second_panchami():
    days = sorted(f["start_date"] for f in _festivals(2026) if f["id"].startswith("pushpanjali_vrat_monsoon_2026"))

    assert days == ["2026-09-16", "2026-09-17", "2026-09-18", "2026-09-19", "2026-09-20"]


# Unchanged, by earlier reference-checked decisions.

def test_kalyanaks_keep_the_book_verified_first_day():
    assert "2026-10-18" in _dates(2026, fid="shri_sheetalnath_ji___liberation_kalyanak")
    assert "2026-07-01" in _dates(2026, fid="shri_rishabhdev_ji___conception_kalyanak")


def test_parva_tithis_still_show_on_both_days():
    assert {"2026-08-26", "2026-08-27"} <= _dates(2026, fid="pakhi_chaudas_shukla")


def test_karma_nirjara_keeps_the_first_day():
    assert _dates(2026, fid="karma_nirjara_vrat_shravana") == {"2026-08-26"}


def test_the_sunday_ravi_vrat_stays_on_sunday():
    assert "2027-08-15" in _dates(2027, fid="ravi_vrat")


def test_chaitra_navpad_oli_and_ratnatraya_close_on_the_second_purnima():
    """2 Apr 2026 is Purnima at sunrise; the Pratipada vriddhi (2-3 Apr) makes it the second Purnima."""
    assert _dates(2026, fid="navapad_oli_vrat_purna_chaitra_2026") == {"2026-04-02"}
    assert _dates(2026, fid="ratnatraya_vrat_purna_chaitra_2026") == {"2026-04-02"}
    assert _dates(2026, fid="navapad_oli_vrat_prarambh_chaitra_2026") == {"2026-03-25"}

"""Parity fixtures: the Python engine's answers, exported for the Dart engine's tests.

Design: plans/mobile-phase1-fixtures.md.
"""

from __future__ import annotations

import json
from datetime import date
from zoneinfo import ZoneInfo

import pytest

from location_service import get_timezone_name
from panchang import JAIN_TITHI_OFFSET_DAYS
from panchang_service import generate_location_panchang
from parity_fixtures import DEFAULT_LOCATIONS, custom_location, day_row, random_locations

INDIA_LAT = (8.0, 35.0)
INDIA_LON = (68.0, 97.0)
CHOGHADIYA_NAMES = {"Udveg", "Char", "Labh", "Amrit", "Kaal", "Shubh", "Rog"}


def a_location(name: str = "Delhi"):
    return next(loc for loc in DEFAULT_LOCATIONS if loc.name == name)


def a_row(*, location: str = "Delhi", on: date = date(2026, 10, 21), rule: str = "modern") -> dict:
    return day_row(a_location(location), on, sunrise_rule=rule)


class TestDefaultLocations:
    def test_cover_the_launch_cities_and_two_foreign_edge_cases(self):
        names = {loc.name for loc in DEFAULT_LOCATIONS}

        assert names == {
            "Delhi", "Ahmedabad", "Mumbai", "Surat", "Palitana", "Jaipur",
            "Udaipur", "Indore", "Kolkata", "Bengaluru", "Chennai",
            "London", "New York",
        }

    def test_slugs_are_unique_so_fixture_paths_never_collide(self):
        slugs = [loc.slug for loc in DEFAULT_LOCATIONS]

        assert len(slugs) == len(set(slugs))

    def test_timezones_agree_with_the_engines_own_lookup(self, subtests):
        for loc in DEFAULT_LOCATIONS:
            with subtests.test(loc.name):
                assert loc.timezone == get_timezone_name(loc.lat, loc.lon)


class TestCustomLocation:
    def test_resolves_timezone_from_coordinates(self):
        loc = custom_location(name="Kathmandu", lat=27.7172, lon=85.3240)

        assert loc.timezone == "Asia/Kathmandu"

    def test_slug_is_path_safe(self):
        loc = custom_location(name="Shri Mahavirji (Raj.)", lat=26.68, lon=76.93)

        assert loc.slug == "shri-mahavirji-raj"

    def test_rejects_impossible_coordinates(self):
        with pytest.raises(ValueError):
            custom_location(name="Nowhere", lat=95.0, lon=10.0)


class TestRandomLocations:
    def test_same_seed_gives_the_same_locations(self):
        assert random_locations(count=6, seed=7) == random_locations(count=6, seed=7)

    def test_different_seeds_give_different_locations(self):
        assert random_locations(count=6, seed=7) != random_locations(count=6, seed=8)

    def test_returns_the_requested_count_with_unique_slugs(self):
        locs = random_locations(count=8, seed=1)

        assert len(locs) == 8
        assert len({loc.slug for loc in locs}) == 8

    def test_first_half_inside_india_rest_spread_worldwide(self):
        locs = random_locations(count=200, seed=3)

        def in_india(loc) -> bool:
            return INDIA_LAT[0] <= loc.lat <= INDIA_LAT[1] and INDIA_LON[0] <= loc.lon <= INDIA_LON[1]

        assert all(in_india(loc) for loc in locs[:100])
        # Worldwide draws land outside India's box almost always; a handful inside is fine.
        assert sum(not in_india(loc) for loc in locs[100:]) >= 90

    def test_every_location_has_a_daily_sunrise_and_a_valid_timezone(self):
        locs = random_locations(count=200, seed=3)

        assert all(abs(loc.lat) <= 60.0 for loc in locs)
        assert max(abs(loc.lat) for loc in locs) > 55.0
        for loc in locs:
            ZoneInfo(loc.timezone)


class TestDayRow:
    def test_is_plain_json_keyed_by_the_civil_date(self):
        row = a_row(on=date(2026, 10, 21))

        assert row["date"] == "2026-10-21"
        assert json.loads(json.dumps(row)) == row

    def test_day_events_are_in_order(self):
        row = a_row()

        assert row["sunrise"] < row["sunset"] < row["next_sunrise"]

    def test_tithis_cover_the_day_in_order(self):
        row = a_row()
        ends = [t["ends"] for t in row["tithi"]]

        assert all(1 <= t["index"] <= 30 for t in row["tithi"])
        assert ends[-1] is None
        assert ends[:-1] == sorted(ends[:-1])
        assert all(row["sunrise"] < end < row["next_sunrise"] for end in ends[:-1])

    def test_consecutive_days_chain_without_gaps(self):
        # The tithi running at one day's end is the one at the next sunrise, so a
        # Kshaya (skipped) tithi can only appear in the middle of a day's list.
        rows = [a_row(on=date(2026, 8, d)) for d in range(1, 31)]

        for today, tomorrow in zip(rows, rows[1:]):
            assert today["tithi"][-1]["index"] == tomorrow["tithi"][0]["index"]
            assert today["next_sunrise"] == pytest.approx(tomorrow["sunrise"], abs=1e-6)

    def test_jain_tithi_is_read_two_hours_twenty_four_minutes_after_sunrise(self):
        row = a_row()

        assert row["jain_tithi"]["reference"] == pytest.approx(
            row["sunrise"] + JAIN_TITHI_OFFSET_DAYS, abs=2 / 86400
        )
        assert 1 <= row["jain_tithi"]["index"] <= 30

    def test_month_and_samvats_are_present(self):
        row = a_row()

        assert 1 <= row["month"]["index"] <= 12
        assert isinstance(row["month"]["is_adhika"], bool)
        assert row["vira_nirvana_samvat"] - row["vikram_samvat"] in (469, 470)

    def test_choghadiya_has_sixteen_named_slots(self):
        row = a_row()

        assert len(row["choghadiya"]) == 16
        assert set(row["choghadiya"]) <= CHOGHADIYA_NAMES

    def test_sunday_choghadiya_follows_the_classical_table(self):
        # Classical Choghadiya table: a Sunday day opens with Udveg, its night with Shubh.
        row = a_row(on=date(2026, 10, 25))

        assert row["vara"] == 0
        assert row["choghadiya"] == [
            "Udveg", "Char", "Labh", "Amrit", "Kaal", "Shubh", "Rog", "Udveg",
            "Shubh", "Amrit", "Char", "Rog", "Kaal", "Labh", "Udveg", "Shubh",
        ]

    def test_reports_the_2026_adhik_jyeshtha_in_purnimanta_reckoning(self):
        # Pt. Jaini Jiyalal Panchang (see plans/adhik_maas_purnimanta_fix.md): purnimanta
        # Adhik Jyeshtha spans Krishna 2-16 May and Shukla 17-31 May 2026; Nija Jyeshtha
        # Krishna follows in June.
        adhik = a_row(on=date(2026, 5, 20))
        nija = a_row(on=date(2026, 6, 5))

        assert (adhik["month"]["name"], adhik["month"]["is_adhika"]) == ("Adhika Jyeshtha", True)
        assert (nija["month"]["name"], nija["month"]["is_adhika"]) == ("Jyeshtha", False)

    def test_matches_what_the_engine_reports_for_that_day(self):
        loc = a_location("Ahmedabad")
        on = date(2026, 3, 15)
        engine = generate_location_panchang(on, lat=loc.lat, lon=loc.lon, sunrise_rule="traditional")

        row = day_row(loc, on, sunrise_rule="traditional")

        assert row["sunrise"] == engine["events"]["sunrise"]["jd"]
        assert [t["index"] for t in row["tithi"]] == [t["index"] for t in engine["panchang"]["tithi"]]
        assert [t["ends"] for t in row["tithi"][:-1]] == [
            t["ends"]["jd"] for t in engine["panchang"]["tithi"][:-1]
        ]
        assert row["jain_tithi"]["index"] == engine["panchang"]["jain_tithi"]["index"]
        assert row["jain_tithi"]["ends"] == engine["panchang"]["jain_tithi"]["ends"]["jd"]
        assert row["nakshatra"]["index"] == engine["panchang"]["nakshatra"]["index"]
        assert row["nakshatra"]["ends"] == engine["panchang"]["nakshatra"]["ends"]["jd"]
        assert row["month"]["name"] == engine["panchang"]["hindu_month"]["name"]
        assert row["vara"] == engine["panchang"]["vara"]["index"]

    def test_traditional_sunrise_is_later_than_modern(self):
        # Disc centre with no refraction rises after the refracted upper limb.
        modern = a_row(rule="modern")
        traditional = a_row(rule="traditional")

        assert traditional["sunrise"] > modern["sunrise"]

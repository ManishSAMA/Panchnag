"""Parity fixtures: the Python engine's answers, exported for the Dart engine's tests.

Design: plans/mobile-phase1-fixtures.md.
"""

from __future__ import annotations

import gzip
import json
from datetime import date, timedelta
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

from location_service import get_timezone_name
from panchang import JAIN_TITHI_OFFSET_DAYS
from panchang_service import generate_location_panchang
from jain_observances.festival_service import generate_jain_festivals
from parity_fixtures import (
    CORE_SHORT_RANGE,
    DEFAULT_LOCATIONS,
    FULL_RANGE,
    PROFILES,
    FixturePlan,
    PlanEntry,
    SCHEMA_VERSION,
    custom_location,
    day_row,
    festival_rows,
    parse_plan,
    random_locations,
    read_fixture,
    run_plan,
    write_days,
    write_festivals,
    write_manifest,
)

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


class TestWriteDays:
    def test_writes_one_file_per_location_and_rule(self, tmp_path):
        path = write_days(
            a_location("Surat"), start=date(2026, 1, 1), end=date(2026, 1, 2),
            sunrise_rule="traditional", out_dir=tmp_path,
        )

        assert path == tmp_path / "surat" / "traditional" / "days.json.gz"

    def test_holds_every_date_once_in_order_across_a_month_end(self, tmp_path):
        start, end = date(2026, 1, 30), date(2026, 2, 2)

        fixture = read_fixture(write_days(
            a_location(), start=start, end=end, sunrise_rule="modern", out_dir=tmp_path,
        ))

        assert [d["date"] for d in fixture["days"]] == [
            (start + timedelta(days=i)).isoformat() for i in range((end - start).days + 1)
        ]

    def test_rows_are_the_day_rows_and_the_header_names_location_and_rule(self, tmp_path):
        loc = a_location("Chennai")

        fixture = read_fixture(write_days(
            loc, start=date(2026, 7, 4), end=date(2026, 7, 4), sunrise_rule="modern", out_dir=tmp_path,
        ))

        assert fixture["days"] == [day_row(loc, date(2026, 7, 4), sunrise_rule="modern")]
        assert fixture["location"] == {
            "slug": loc.slug, "name": loc.name, "lat": loc.lat, "lon": loc.lon, "timezone": loc.timezone,
        }
        assert fixture["sunrise_rule"] == "modern"
        assert fixture["schema_version"] == SCHEMA_VERSION

    def test_rewriting_unchanged_data_at_a_later_time_is_byte_identical(self, tmp_path, monkeypatch):
        def write_at(epoch: float, sub: str) -> bytes:
            monkeypatch.setattr(gzip, "time", SimpleNamespace(time=lambda: epoch))
            return write_days(
                a_location(), start=date(2026, 1, 1), end=date(2026, 1, 2),
                sunrise_rule="modern", out_dir=tmp_path / sub,
            ).read_bytes()

        assert write_at(1_000_000_000.0, "a") == write_at(2_000_000_000.0, "b")

    def test_keys_are_sorted_so_reordering_code_never_churns_fixtures(self, tmp_path):
        path = write_days(
            a_location(), start=date(2026, 1, 1), end=date(2026, 1, 1),
            sunrise_rule="modern", out_dir=tmp_path,
        )
        fixture = json.loads(gzip.decompress(path.read_bytes()), object_pairs_hook=list)
        day = dict(fixture)["days"][0]

        assert [k for k, _ in fixture] == sorted(k for k, _ in fixture)
        assert [k for k, _ in day] == sorted(k for k, _ in day)

    def test_rejects_a_range_that_ends_before_it_starts(self, tmp_path):
        with pytest.raises(ValueError):
            write_days(
                a_location(), start=date(2026, 1, 2), end=date(2026, 1, 1),
                sunrise_rule="modern", out_dir=tmp_path,
            )

    def test_rejects_an_unknown_sunrise_rule(self, tmp_path):
        with pytest.raises(ValueError):
            write_days(
                a_location(), start=date(2026, 1, 1), end=date(2026, 1, 1),
                sunrise_rule="vedic", out_dir=tmp_path,
            )


def a_plan(*entries: tuple[str, date, date], rules=("modern", "traditional"), profiles=None) -> FixturePlan:
    return FixturePlan(
        entries=tuple(PlanEntry(a_location(name), start, end) for name, start, end in entries),
        sunrise_rules=rules,
        profiles=profiles or PROFILES,
    )


class TestManifest:
    def a_manifest(self, tmp_path) -> dict:
        plan = a_plan(
            ("London", date(2026, 1, 1), date(2027, 12, 31)),
            ("Delhi", date(2016, 1, 1), date(2040, 12, 31)),
        )
        return json.loads(write_manifest(out_dir=tmp_path, plan=plan).read_text(encoding="utf-8"))

    def test_describes_what_the_set_contains(self, tmp_path):
        manifest = self.a_manifest(tmp_path)

        assert manifest["schema_version"] == SCHEMA_VERSION
        assert manifest["sunrise_rules"] == ["modern", "traditional"]
        assert manifest["profiles"] == list(PROFILES)
        assert [loc["slug"] for loc in manifest["locations"]] == ["london", "delhi"]
        assert manifest["locations"][0]["timezone"] == "Europe/London"

    def test_records_each_locations_own_range(self, tmp_path):
        london, delhi = self.a_manifest(tmp_path)["locations"]

        assert (london["start"], london["end"]) == ("2026-01-01", "2027-12-31")
        assert (delhi["start"], delhi["end"]) == ("2016-01-01", "2040-12-31")

    def test_records_the_reference_engine_version(self, tmp_path):
        import swisseph

        assert self.a_manifest(tmp_path)["swisseph_version"] == swisseph.version

    def test_rewriting_is_byte_identical(self, tmp_path):
        self.a_manifest(tmp_path / "a")
        self.a_manifest(tmp_path / "b")

        assert (tmp_path / "a" / "manifest.json").read_bytes() == (tmp_path / "b" / "manifest.json").read_bytes()


TAPAGACHCHHA = "shwetambar_murtipujak_tapagachchha"
STHANAKVASI = "shwetambar_sthanakvasi"


class TestFestivalRows:
    def test_are_the_engines_occurrences_for_that_year(self):
        loc = a_location()
        engine = generate_jain_festivals(2026, loc.lat, loc.lon, profile=STHANAKVASI)["festivals"]

        rows = festival_rows(loc, 2026, profile=STHANAKVASI, sunrise_rule="modern")

        assert sorted((r["occurrence_id"], r["start_date"], r["end_date"]) for r in rows) == sorted(
            (f["occurrence_id"], f["start_date"], f["end_date"]) for f in engine
        )
        assert all(r["start_date"].startswith("2026") for r in rows)

    def test_carry_ids_dates_and_status_as_plain_json(self):
        rows = festival_rows(a_location(), 2026, profile=TAPAGACHCHHA, sunrise_rule="modern")

        assert set(rows[0]) == {"id", "occurrence_id", "start_date", "end_date", "status"}
        assert json.loads(json.dumps(rows)) == rows

    def test_are_in_a_stable_order(self):
        rows = festival_rows(a_location(), 2026, profile=TAPAGACHCHHA, sunrise_rule="modern")

        keys = [(r["start_date"], r["occurrence_id"]) for r in rows]
        assert keys == sorted(keys)

    def test_depend_on_the_profile(self):
        # registry.py: the Sthanakvasi Samvatsari applies to Sthanakvasi and Terapanthi only.
        def ids(profile: str) -> set[str]:
            return {r["id"] for r in festival_rows(a_location(), 2026, profile=profile, sunrise_rule="modern")}

        assert "samvatsari_sthanakvasi" in ids(STHANAKVASI)
        assert "samvatsari_sthanakvasi" not in ids(TAPAGACHCHHA)

    def test_depend_on_the_sunrise_rule(self):
        # Rohini Vrat follows the nakshatra at sunrise; in Delhi 2026 the later
        # traditional sunrise moves one occurrence by a day.
        def dates(rule: str) -> set[tuple[str, str]]:
            return {(r["id"], r["start_date"]) for r in festival_rows(a_location(), 2026, profile=TAPAGACHCHHA, sunrise_rule=rule)}

        assert dates("modern") != dates("traditional")

    def test_reject_an_unknown_profile_the_engine_would_silently_accept(self):
        with pytest.raises(ValueError):
            festival_rows(a_location(), 2026, profile="digambar_x", sunrise_rule="modern")


class TestWriteFestivals:
    def test_writes_one_file_per_profile_grouped_by_year(self, tmp_path):
        path = write_festivals(
            a_location(), start_year=2026, end_year=2027,
            profile=STHANAKVASI, sunrise_rule="traditional", out_dir=tmp_path,
        )

        fixture = read_fixture(path)
        assert path == tmp_path / "delhi" / "traditional" / f"festivals.{STHANAKVASI}.json.gz"
        assert sorted(fixture["years"]) == ["2026", "2027"]
        assert fixture["years"]["2027"] == festival_rows(
            a_location(), 2027, profile=STHANAKVASI, sunrise_rule="traditional"
        )
        assert (fixture["profile"], fixture["sunrise_rule"], fixture["schema_version"]) == (
            STHANAKVASI, "traditional", SCHEMA_VERSION,
        )
        assert fixture["location"]["slug"] == "delhi"

    def test_a_single_year_is_a_valid_range(self, tmp_path):
        path = write_festivals(
            a_location(), start_year=2026, end_year=2026,
            profile=STHANAKVASI, sunrise_rule="modern", out_dir=tmp_path,
        )

        assert list(read_fixture(path)["years"]) == ["2026"]

    def test_rejects_a_range_that_ends_before_it_starts(self, tmp_path):
        with pytest.raises(ValueError):
            write_festivals(
                a_location(), start_year=2027, end_year=2026,
                profile=STHANAKVASI, sunrise_rule="modern", out_dir=tmp_path,
            )

    def test_profiles_are_the_three_the_app_offers(self):
        assert PROFILES == (TAPAGACHCHHA, STHANAKVASI, "shwetambar_terapanthi")


class TestPlanJobs:
    def test_cover_days_once_per_location_and_rule_and_festivals_once_per_profile(self):
        plan = a_plan(
            ("Delhi", date(2026, 1, 1), date(2026, 1, 2)),
            ("Surat", date(2026, 1, 1), date(2026, 1, 2)),
        )
        days = [(j.location.slug, j.sunrise_rule) for j in plan.jobs if j.profile is None]
        festivals = [(j.location.slug, j.sunrise_rule, j.profile) for j in plan.jobs if j.profile]

        assert sorted(days) == sorted(
            (slug, rule) for slug in ("delhi", "surat") for rule in ("modern", "traditional")
        )
        assert sorted(festivals) == sorted(
            (slug, rule, profile)
            for slug in ("delhi", "surat") for rule in ("modern", "traditional") for profile in PROFILES
        )

    def test_carry_each_locations_range(self):
        plan = a_plan(("Delhi", date(2016, 3, 1), date(2018, 2, 1)))

        assert {(j.start, j.end) for j in plan.jobs} == {(date(2016, 3, 1), date(2018, 2, 1))}


class TestParsePlan:
    def test_core_set_is_three_cities_in_full_and_the_rest_for_two_years(self):
        plan = parse_plan(["--set", "core"])
        ranges = {e.location.name: (e.start, e.end) for e in plan.entries}

        assert {n for n, r in ranges.items() if r == FULL_RANGE} == {"Delhi", "Ahmedabad", "Mumbai"}
        assert {n for n, r in ranges.items() if r == CORE_SHORT_RANGE} >= {
            loc.name for loc in DEFAULT_LOCATIONS if loc.name not in {"Delhi", "Ahmedabad", "Mumbai"}
        }
        assert sum(n.startswith("random") for n in ranges) == 4
        assert plan.sunrise_rules == ("modern", "traditional")
        assert plan.profiles == PROFILES

    def test_full_set_is_every_default_and_eight_random_over_the_whole_range(self):
        plan = parse_plan(["--set", "full"])

        assert {e.location.name for e in plan.entries} >= {loc.name for loc in DEFAULT_LOCATIONS}
        assert sum(e.location.name.startswith("random") for e in plan.entries) == 8
        assert {(e.start, e.end) for e in plan.entries} == {FULL_RANGE}

    def test_random_sample_can_be_resized_and_reseeded(self):
        plan = parse_plan(["--set", "full", "--random", "2", "--seed", "99"])

        assert [e.location for e in plan.entries if e.location.name.startswith("random")] == list(
            random_locations(count=2, seed=99)
        )

    def test_custom_set_is_any_place_and_range_you_name(self):
        plan = parse_plan([
            "--set", "custom", "--name", "Shikharji", "--lat", "23.9616", "--lon", "86.1331",
            "--start", "2030-01-01", "--end", "2030-12-31", "--rule", "traditional",
        ])

        (entry,) = plan.entries
        assert (entry.location.name, entry.location.timezone) == ("Shikharji", "Asia/Kolkata")
        assert (entry.start, entry.end) == (date(2030, 1, 1), date(2030, 12, 31))
        assert plan.sunrise_rules == ("traditional",)

    def test_custom_set_defaults_to_the_apps_whole_range_and_both_rules(self):
        plan = parse_plan(["--set", "custom", "--lat", "21.52", "--lon", "71.82"])

        (entry,) = plan.entries
        assert (entry.start, entry.end) == FULL_RANGE
        assert plan.sunrise_rules == ("modern", "traditional")

    def test_custom_set_needs_coordinates(self):
        with pytest.raises(SystemExit):
            parse_plan(["--set", "custom", "--name", "Nowhere"])


class TestRunPlan:
    def test_parallel_output_is_identical_to_serial_and_complete(self, tmp_path):
        plan = a_plan(
            ("Delhi", date(2026, 1, 1), date(2026, 1, 2)),
            ("London", date(2026, 1, 1), date(2026, 1, 2)),
            rules=("modern",), profiles=(STHANAKVASI,),
        )

        run_plan(plan, out_dir=tmp_path / "serial", workers=1)
        run_plan(plan, out_dir=tmp_path / "parallel", workers=2)

        def files(root):
            return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}

        serial = files(tmp_path / "serial")
        assert serial == files(tmp_path / "parallel")
        assert set(serial) == {
            "manifest.json",
            "delhi/modern/days.json.gz",
            f"delhi/modern/festivals.{STHANAKVASI}.json.gz",
            "london/modern/days.json.gz",
            f"london/modern/festivals.{STHANAKVASI}.json.gz",
        }

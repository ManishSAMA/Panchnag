"""The clock setting: standard time all year, or the wall clock with DST.

Printed panchangs for DST countries often keep standard time all year -- the
New Jersey reference (PanchangReport_2654.pdf, 40°50'N 74°06'W, 2027) prints
EST through the summer, with no jump on 14 March. "daylight" follows the wall
clock instead.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from astronomy import clock_timezone, jd_to_zoned_datetime, local_date_anchor_jd, utc_offset_hours

NEW_YORK = "America/New_York"
SYDNEY = "Australia/Sydney"
KOLKATA = "Asia/Kolkata"


@pytest.mark.parametrize(
    "tz_name, day, standard, daylight",
    [
        (NEW_YORK, date(2027, 7, 1), -5.0, -4.0),
        (NEW_YORK, date(2027, 1, 15), -5.0, -5.0),
        (SYDNEY, date(2027, 1, 15), 10.0, 11.0),   # southern summer
        (SYDNEY, date(2027, 7, 1), 10.0, 10.0),
        (KOLKATA, date(2027, 7, 1), 5.5, 5.5),
    ],
)
def test_standard_time_ignores_dst_and_daylight_follows_the_wall_clock(tz_name, day, standard, daylight):
    assert utc_offset_hours(tz_name, day, clock="standard") == standard
    assert utc_offset_hours(tz_name, day, clock="daylight") == daylight


def test_the_dst_change_day_uses_the_offset_in_force_at_local_noon():
    """14 Mar 2027 is the US spring-forward day; the clocks change at 02:00."""
    assert utc_offset_hours(NEW_YORK, date(2027, 3, 14), clock="daylight") == -4.0
    assert utc_offset_hours(NEW_YORK, date(2027, 3, 13), clock="daylight") == -5.0


def test_standard_time_is_labelled_with_the_standard_abbreviation_even_in_summer():
    july = date(2027, 7, 1)

    assert clock_timezone(NEW_YORK, july, clock="standard").tzname(None) == "EST"
    assert clock_timezone(NEW_YORK, july, clock="daylight").tzname(datetime(2027, 7, 1, 12)) == "EDT"
    assert clock_timezone(SYDNEY, date(2027, 1, 15), clock="standard").tzname(None) == "AEST"


def test_a_local_anchor_and_its_display_round_trip_under_either_clock():
    july = date(2027, 7, 1)
    for clock in ("standard", "daylight"):
        jd = local_date_anchor_jd(july, NEW_YORK, hour=6, clock=clock)
        shown = jd_to_zoned_datetime(jd, NEW_YORK, clock=clock) + timedelta(seconds=30)  # JD round-off
        assert (shown.date(), shown.hour, shown.minute) == (july, 6, 0), clock


def test_standard_and_daylight_anchors_differ_by_the_dst_hour_in_summer():
    july = date(2027, 7, 1)

    standard = local_date_anchor_jd(july, NEW_YORK, hour=6, clock="standard")
    daylight = local_date_anchor_jd(july, NEW_YORK, hour=6, clock="daylight")

    assert round((standard - daylight) * 24, 6) == 1.0


def test_an_invalid_clock_is_rejected():
    with pytest.raises(ValueError, match="clock"):
        utc_offset_hours(NEW_YORK, date(2027, 7, 1), clock="summer")


def test_standard_time_shown_in_summer_reads_one_hour_behind_the_wall_clock():
    noon_utc_jd = 2461587.5 + 16.5 / 24  # 2027-07-01 16:30 UTC

    standard = jd_to_zoned_datetime(noon_utc_jd, NEW_YORK, clock="standard")
    daylight = jd_to_zoned_datetime(noon_utc_jd, NEW_YORK, clock="daylight")

    assert (standard.hour, daylight.hour) == (11, 12)
    assert standard.astimezone(timezone.utc) == daylight.astimezone(timezone.utc)

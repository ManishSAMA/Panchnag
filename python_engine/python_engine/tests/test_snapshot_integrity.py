"""Festival snapshots must be complete, or fail loudly.

The festival engine resolves every rule against a contiguous list of daily
snapshots. A missing day is not a degraded result -- it silently removes a
candidate date, so a festival can vanish from the calendar with no error
anywhere. These tests pin the contract: every day in the window is present,
and an astronomical failure surfaces instead of thinning the list.
"""

from datetime import date

import pytest

from jain_observances import festival_service
from jain_observances.festival_service import _build_snapshots


LAT, LON = 23.0225, 72.5714  # Ahmedabad
TZ = "Asia/Kolkata"


def test_snapshot_window_covers_every_day_with_no_gaps():
    snapshots = _build_snapshots(2026, LAT, LON, "Lahiri", TZ)

    dates = [s["date"] for s in snapshots]

    assert dates[0] == date(2025, 12, 1)
    assert dates[-1] == date(2027, 1, 31)
    assert dates == sorted(dates), "snapshots must be chronological"
    assert len(dates) == len(set(dates)), "snapshots must not repeat a date"

    expected_span = (dates[-1] - dates[0]).days + 1
    assert len(dates) == expected_span, (
        f"snapshot list has {expected_span - len(dates)} missing day(s) -- "
        "a hole here silently drops festival candidates"
    )


def test_astronomical_failure_surfaces_instead_of_dropping_a_day(monkeypatch):
    """A failing day must raise, not disappear from the snapshot list."""
    real_get_sunrise = festival_service.get_sunrise
    doomed = date(2026, 6, 15)

    def exploding_get_sunrise(day_start_jd, lat, lon):
        from astronomy import jd_to_zoned_datetime

        moment = jd_to_zoned_datetime(day_start_jd, TZ)
        if moment is not None and moment.date() == doomed:
            raise RuntimeError("ephemeris unavailable")
        return real_get_sunrise(day_start_jd, lat, lon)

    monkeypatch.setattr(festival_service, "get_sunrise", exploding_get_sunrise)

    with pytest.raises(RuntimeError, match="ephemeris unavailable"):
        _build_snapshots(2026, LAT, LON, "Lahiri", TZ)

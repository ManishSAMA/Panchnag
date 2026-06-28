import pytest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import swisseph as swe

from sun_tracker.calculator import run_calculation, get_ayanamsa_dm

def test_get_ayanamsa_dm():
    # JD for Jan 1, 2026 00:00:00 IST (= Dec 31, 2025 18:30 UTC)
    jd = swe.julday(2025, 12, 31, 18.5)
    ayan_str = get_ayanamsa_dm(jd)
    
    # Calibrated Lahiri Ayanamsa on Jan 1, 2026 00:00 IST is 24° 13' 13.10"
    assert ayan_str == '24° 13\' 13.10"'

def test_run_calculation():
    # Run calculation for a single year (e.g. 2026) for Delhi
    # To keep the test fast, we will calculate the transits.
    # Note: run_calculation takes about 7 seconds to process a full year.
    rows = run_calculation(2026, "Delhi")
    
    # Check that we found crossing moments (should be around 21,580 rows)
    assert 21500 <= len(rows) <= 21700
    
    # Verify the structure of the first row
    first_row = rows[0]
    assert "Date" in first_row
    assert "Time" in first_row
    assert "Rashi" in first_row
    assert "Ansha" in first_row
    assert "Kala" in first_row
    assert "Vikala" in first_row
    assert "Ayanamsa_DM" in first_row
    
    # Verify value ranges
    assert first_row["Rashi"] in [
        "Mesh", "Vrishabh", "Mithun", "Kark", "Simha", "Kanya",
        "Tula", "Vrishchik", "Dhanu", "Makar", "Kumbh", "Meen"
    ]
    assert 0 <= first_row["Ansha"] < 30
    assert 0 <= first_row["Kala"] < 60
    assert first_row["Vikala"] == 0
    assert "24°" in first_row["Ayanamsa_DM"]

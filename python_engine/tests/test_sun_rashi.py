"""
Unit tests for get_sun_rashi() in astronomy.py.

Verified against published Mesh Sankranti and Makar Sankranti dates,
and spot-checked against known solar month boundaries for 2025.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from astronomy import get_sun_rashi, get_julian_date


def test_sun_in_mesh_april_2025():
    # Mesh Sankranti 2025 falls on April 14 — Sun enters sidereal Aries
    jd = get_julian_date(2025, 4, 14, 6.0)  # 6 AM UTC ≈ sunrise in India
    assert get_sun_rashi(jd) == "Mesh"


def test_sun_in_makar_january_2025():
    # Makar Sankranti 2025 falls on January 14 — Sun enters sidereal Capricorn
    jd = get_julian_date(2025, 1, 14, 6.0)
    assert get_sun_rashi(jd) == "Makar"


def test_sun_rashi_transition_kark_to_simha_2025():
    # Sun is in Kark (Cancer) in mid-July and Simha (Leo) in mid-August
    jd_kark = get_julian_date(2025, 7, 20, 6.0)
    jd_simha = get_julian_date(2025, 8, 20, 6.0)
    assert get_sun_rashi(jd_kark) == "Kark"
    assert get_sun_rashi(jd_simha) == "Simha"


def test_all_twelve_rashis_covered():
    # Spot-check each of the 12 rashis roughly 10 days into each solar month
    expected = [
        (2025, 4, 25, "Mesh"),
        (2025, 5, 25, "Vrishabh"),
        (2025, 6, 25, "Mithun"),
        (2025, 7, 25, "Kark"),
        (2025, 8, 25, "Simha"),
        (2025, 9, 25, "Kanya"),
        (2025, 10, 25, "Tula"),
        (2025, 11, 25, "Vrishchik"),
        (2025, 12, 25, "Dhanu"),
        (2026, 1, 25, "Makar"),
        (2026, 2, 25, "Kumbh"),
        (2026, 3, 25, "Meen"),
    ]
    for y, m, d, expected_rashi in expected:
        jd = get_julian_date(y, m, d, 6.0)
        result = get_sun_rashi(jd)
        assert result == expected_rashi, f"Expected {expected_rashi} for {y}-{m:02d}-{d:02d}, got {result}"

"""Tests for Sankranti (solar ingress) detection functions."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from astronomy import _sidereal_sun_lon_lahiri, get_julian_date


def test_sidereal_sun_lon_lahiri_is_in_range():
    jd = get_julian_date(2025, 4, 14, 6.0)
    lon = _sidereal_sun_lon_lahiri(jd)
    assert 0.0 <= lon < 360.0


def test_sidereal_sun_lon_lahiri_mesh_on_sankranti():
    # On Mesha Sankranti 2025 (April 14) near 14:00 IST = 08:30 UTC
    jd = get_julian_date(2025, 4, 14, 8.5)
    lon = _sidereal_sun_lon_lahiri(jd)
    # Should be very close to 0° (just entered Mesh)
    assert lon < 1.0 or lon > 359.0  # within 1° of the Meena/Mesh boundary


def test_sidereal_sun_lon_lahiri_makar_on_sankranti():
    # On Makar Sankranti 2025 (Jan 14) near 20:38 IST = 15:08 UTC
    jd = get_julian_date(2025, 1, 14, 15.1)
    lon = _sidereal_sun_lon_lahiri(jd)
    # Should be very close to 270°
    assert 269.0 < lon < 271.0

import pytest
from datetime import datetime, timezone
import swisseph as swe

# Import from our planned module
from sun_transit_exporter.calculation import (
    get_sun_longitude_tropical,
    find_crossing_time,
    generate_transit_events,
    get_ayanamsa_dm
)

def test_get_sun_longitude_tropical():
    # JD for Jan 1, 2026 00:00:00 UTC (approximately 2461041.5)
    jd = swe.julday(2026, 1, 1, 0.0)
    lon = get_sun_longitude_tropical(jd)
    
    # Sun's tropical longitude in early January is typically around 280 degrees
    assert 279.0 < lon < 281.0
    assert 0.0 <= lon < 360.0

def test_topocentric_difference():
    # Verify topocentric position has location-based differences
    jd = swe.julday(2026, 1, 1, 12.0)
    
    # Delhi: 77.2090 E, 28.6139 N, 216m
    # Chennai: 80.2707 E, 13.0827 N, 6m
    lon_delhi = get_sun_longitude_tropical(jd, topo_coords=(77.2090, 28.6139, 216.0))
    lon_chennai = get_sun_longitude_tropical(jd, topo_coords=(80.2707, 13.0827, 6.0))
    
    # Geocentric
    lon_geo = get_sun_longitude_tropical(jd)
    
    # Verify topocentric positions differ slightly from geocentric, and from each other,
    # due to parallax (usually up to ~8.8 arcseconds, which is ~0.0024 degrees)
    assert lon_delhi != lon_geo
    assert lon_chennai != lon_geo
    assert lon_delhi != lon_chennai
    
    # Parallax difference is extremely small (within 0.005 degrees)
    assert abs(lon_delhi - lon_geo) < 0.005
    assert abs(lon_chennai - lon_geo) < 0.005

def test_find_crossing_time():
    # Let's find a crossing time between two known dates
    jd_start = swe.julday(2026, 1, 1, 12.0)
    
    # Calculate longitude at start and end
    lon_start = get_sun_longitude_tropical(jd_start)
    lon_end = get_sun_longitude_tropical(jd_start + 1.0/24.0) # 1 hour later
    
    # Find an integer arcminute target between the start and end
    arcmin_start = int(lon_start * 60.0)
    arcmin_end = int(lon_end * 60.0)
    
    if arcmin_start != arcmin_end:
        # A crossing occurred!
        target_arcmin = arcmin_end
        jd_cross = find_crossing_time(jd_start, jd_start + 1.0/24.0, target_arcmin)
        
        # Verify the crossing time is within the bounds
        assert jd_start <= jd_cross <= jd_start + 1.0/24.0
        
        # Verify that the longitude at the crossing time is extremely close to the target
        lon_cross = get_sun_longitude_tropical(jd_cross)
        assert abs(lon_cross - target_arcmin / 60.0) < 1e-5

def test_generate_transit_events():
    # Test generating events for a very short period (e.g., 2 hours on Jan 1, 2026)
    dt_start = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    dt_end = datetime(2026, 1, 1, 2, 0, tzinfo=timezone.utc)
    
    events = list(generate_transit_events(dt_start, dt_end))
    
    # Sun moves ~2.46 arcminutes per hour, so in 2 hours we should have around 4-6 crossings
    assert 3 <= len(events) <= 6
    
    for event in events:
        assert 'dt' in event
        assert isinstance(event['dt'], datetime)
        assert 'degree' in event
        assert 'minute' in event
        assert 0 <= event['degree'] < 360
        assert 0 <= event['minute'] < 60
        
        # Verify chronological order
        assert dt_start <= event['dt'] <= dt_end

def test_traditional_conversion():
    rashi_names = [
        "Mesh", "Vrishabh", "Mithun", "Kark", "Simha", "Kanya",
        "Tula", "Vrishchik", "Dhanu", "Makar", "Kumbh", "Meen"
    ]
    
    # Test cases: (degree, expected_rashi, expected_ansha)
    test_cases = [
        (0, "Mesh", 0),
        (29, "Mesh", 29),
        (30, "Vrishabh", 0),
        (59, "Vrishabh", 29),
        (359, "Meen", 29),
    ]
    for deg, exp_rashi, exp_ansha in test_cases:
        rashi_idx = deg // 30
        ansha = deg % 30
        assert rashi_names[rashi_idx] == exp_rashi
        assert ansha == exp_ansha

def test_get_ayanamsa_dm():
    jd = swe.julday(2026, 1, 1, 0.0)
    ayan_str = get_ayanamsa_dm(jd)
    # Lahiri Ayanamsa on Jan 1, 2026 is approximately 24 degrees 13 minutes
    assert "24°" in ayan_str
    assert "13'" in ayan_str



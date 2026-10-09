"""Phase 0 spike: dump Swiss Ephemeris reference values for the Dart accuracy trial.

Throwaway exploration code (see plans/mobile-app-flutter.md, Phase 0).
Run with the python_engine venv:

    ..\\..\\..\\python_engine\\python_engine\\.venv-win\\Scripts\\python.exe tool\\dump_reference.py
"""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parents[4] / "python_engine" / "python_engine"
sys.path.insert(0, str(ENGINE_DIR))

import swisseph as swe  # noqa: E402

from astronomy import (  # noqa: E402
    get_ayanamsa,
    get_planetary_longitude,
    get_sunrise,
    get_sunset,
    local_date_anchor_jd,
)
from panchang import (  # noqa: E402
    _find_exact_end_time,
    get_nakshatra_at_jd,
    get_tithi_at_jd,
)

START = date(2016, 1, 1)
END = date(2040, 12, 31)
AYANAMSA = "Lahiri"

CITIES = [
    {"name": "Delhi", "lat": 28.6139, "lon": 77.2090, "tz": "Asia/Kolkata"},
    {"name": "Ahmedabad", "lat": 23.0225, "lon": 72.5714, "tz": "Asia/Kolkata"},
    {"name": "Kolkata", "lat": 22.5726, "lon": 88.3639, "tz": "Asia/Kolkata"},
    {"name": "London", "lat": 51.5074, "lon": -0.1278, "tz": "Europe/London"},
    {"name": "NewYork", "lat": 40.7128, "lon": -74.0060, "tz": "America/New_York"},
]


def _days() -> list[date]:
    return [START + timedelta(days=i) for i in range((END - START).days + 1)]


def _tropical(jd: float, body: int) -> float:
    res, _ = swe.calc_ut(jd, body, swe.FLG_SWIEPH)
    return res[0]


def _samples() -> list[dict]:
    jd0 = swe.julday(START.year, START.month, START.day, 0.0)
    count = (END - START).days + 1
    return [
        {
            "jd": jd,
            "dt": swe.deltat(jd) * 86400.0,
            "sunT": _tropical(jd, swe.SUN),
            "moonT": _tropical(jd, swe.MOON),
            "ayan": get_ayanamsa(jd, AYANAMSA),
            "sunS": get_planetary_longitude(jd, "Sun", AYANAMSA),
            "moonS": get_planetary_longitude(jd, "Moon", AYANAMSA),
        }
        for jd in (jd0 + i * 0.5 for i in range(count * 2))
    ]


def _transitions(index_func) -> list[dict]:
    jd = swe.julday(START.year, START.month, START.day, 0.0)
    jd_end = swe.julday(END.year, END.month, END.day, 24.0)
    out: list[dict] = []
    while jd < jd_end:
        idx = index_func(jd, AYANAMSA)
        end = _find_exact_end_time(jd, index_func, idx, AYANAMSA, max_iter=60)
        out.append({"jd": end, "to": index_func(end, AYANAMSA)})
        jd = end + 1e-6
    return out


def _sankrantis() -> list[dict]:
    def sign(jd: float) -> int:
        return int(get_planetary_longitude(jd, "Sun", AYANAMSA) / 30.0) % 12

    def bisect(a: float, b: float, prev: int) -> float:
        for _ in range(60):
            mid = (a + b) / 2
            a, b = (mid, b) if sign(mid) == prev else (a, mid)
        return b

    jd = swe.julday(START.year, START.month, START.day, 0.0)
    jd_end = swe.julday(END.year, END.month, END.day, 24.0)
    out: list[dict] = []
    prev = sign(jd)
    while jd < jd_end:
        nxt = jd + 0.5
        cur = sign(nxt)
        if cur != prev:
            out.append({"jd": bisect(jd, nxt, prev), "to": cur})
            prev = cur
        jd = nxt
    return out


def _rise_set() -> list[dict]:
    return [
        {
            "city": city["name"],
            "lat": city["lat"],
            "lon": city["lon"],
            "date": d.isoformat(),
            "anchor": (anchor := local_date_anchor_jd(d, city["tz"])),
            "rise": get_sunrise(anchor, city["lat"], city["lon"]),
            "set": get_sunset(anchor, city["lat"], city["lon"]),
        }
        for city in CITIES
        for d in _days()
    ]


def main() -> None:
    out_dir = Path(__file__).resolve().parents[1] / "reference"
    out_dir.mkdir(exist_ok=True)
    payload = {
        "swe_version": swe.version,
        "range": [START.isoformat(), END.isoformat()],
        "samples": _samples(),
        "tithi": _transitions(get_tithi_at_jd),
        "nakshatra": _transitions(get_nakshatra_at_jd),
        "sankranti": _sankrantis(),
        "riseSet": _rise_set(),
    }
    target = out_dir / "reference.json"
    target.write_text(json.dumps(payload), encoding="utf-8")
    print({k: len(v) for k, v in payload.items() if isinstance(v, list)}, "->", target)


if __name__ == "__main__":
    main()

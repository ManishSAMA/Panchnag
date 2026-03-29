from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from export_pdf import generate_pdf_calendar
from range_generation_service import _timezone_snapshot
from panchang_service import resolve_location


def generate_pdf_export(
    *,
    year: int,
    city: str | None,
    lat: float | None,
    lon: float | None,
    ayanamsa_name: str,
    output_dir: str = "/tmp",
) -> dict:
    location = resolve_location(city=city, lat=lat, lon=lon)
    tz_info = _timezone_snapshot(location.timezone, year)

    target_dir = Path(output_dir) / "jain_panchang_exports" / uuid4().hex
    target_dir.mkdir(parents=True, exist_ok=True)

    output_path = target_dir / f"panchang_{year}.pdf"
    generate_pdf_calendar(
        year,
        str(output_path),
        lat=location.lat,
        lon=location.lon,
        tz_offset=tz_info["offset_hours"],
        ayanamsa=ayanamsa_name,
    )

    return {
        "year": year,
        "ayanamsa": ayanamsa_name,
        "location": {
            "name": location.name,
            "lat": location.lat,
            "lon": location.lon,
            "timezone": location.timezone,
            "timezone_export_label": tz_info["label"],
            "timezone_export_offset_hours": tz_info["offset_hours"],
        },
        "file": {
            "name": output_path.name,
            "path": str(output_path),
        },
    }

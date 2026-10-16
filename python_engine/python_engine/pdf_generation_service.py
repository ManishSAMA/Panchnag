from __future__ import annotations

import tempfile
from pathlib import Path
from uuid import uuid4

import hindi_calendar_pdf
from export_pdf import generate_pdf_calendar
from laghu_panchang import build_laghu_year
from laghu_panchang_render import write_excel, write_pdf
from range_generation_service import _timezone_snapshot
from panchang_service import resolve_location


def generate_pdf_export(
    *,
    year: int,
    city: str | None,
    lat: float | None,
    lon: float | None,
    ayanamsa_name: str,
    output_dir: str | None = None,
) -> dict:
    location = resolve_location(city=city, lat=lat, lon=lon)
    tz_info = _timezone_snapshot(location.timezone, year)

    target_dir = Path(output_dir or tempfile.gettempdir()) / "jain_panchang_exports" / uuid4().hex
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


def generate_hindi_pdf_export(
    *,
    start_year: int,
    start_month: int,
    month_count: int,
    city: str | None,
    lat: float | None,
    lon: float | None,
    ayanamsa_name: str,
    calendar_system: str,
    output_dir: str | None = None,
) -> dict:
    """Write the Hindi calendar; the file is HTML when no PDF renderer exists."""
    location = resolve_location(city=city, lat=lat, lon=lon)
    tz_info = _timezone_snapshot(location.timezone, start_year)

    target_dir = (
        Path(output_dir or tempfile.gettempdir()) / "jain_panchang_exports" / uuid4().hex
    )
    target_dir.mkdir(parents=True, exist_ok=True)

    last_year, last_month = hindi_calendar_pdf.month_sequence(
        start_year, start_month, month_count
    )[-1]
    requested_path = target_dir / (
        f"Jain_Vedic_Panchang_{start_year}_{start_month:02d}"
        f"_{last_year}_{last_month:02d}_Hindi.pdf"
    )
    written_path = Path(hindi_calendar_pdf.generate_hindi_pdf_calendar(
        str(requested_path),
        start_year=start_year,
        start_month=start_month,
        month_count=month_count,
        lat=location.lat,
        lon=location.lon,
        tz_offset=tz_info["offset_hours"],
        ayanamsa=ayanamsa_name,
        calendar_system=calendar_system,
    ))

    return {
        "ayanamsa": ayanamsa_name,
        "location": {
            "name": location.name,
            "lat": location.lat,
            "lon": location.lon,
            "timezone": location.timezone,
        },
        "file": {
            "name": written_path.name,
            "path": str(written_path),
            "format": written_path.suffix.lstrip("."),
        },
    }


def generate_laghu_panchang_export(
    *,
    year: int,
    city: str | None,
    lat: float | None,
    lon: float | None,
    ayanamsa_name: str,
    profile: str,
    output_format: str,
    output_dir: str | None = None,
) -> dict:
    """Write the yearly Laghu Panchang as PDF, Excel or both.

    The PDF falls back to HTML when no headless browser is available to print it.
    """
    location = resolve_location(city=city, lat=lat, lon=lon)
    halves = build_laghu_year(
        year=year, lat=location.lat, lon=location.lon, tz_name=location.timezone,
        ayanamsa=ayanamsa_name, profile=profile,
    )

    target_dir = (
        Path(output_dir) if output_dir
        else Path(tempfile.gettempdir()) / "jain_panchang_exports" / uuid4().hex
    )
    target_dir.mkdir(parents=True, exist_ok=True)
    place = "".join(ch for ch in (city or location.name) if ch.isalnum()) or "Location"
    stem = target_dir / f"Laghu_Panchang_{year}_{place}"
    title = f"लघु पंचांग {year}"

    writers = {
        "pdf": lambda: write_pdf(halves, stem.with_suffix(".pdf"), title=title, location_name=location.name),
        "excel": lambda: write_excel(halves, stem.with_suffix(".xlsx"), title=title, location_name=location.name),
    }
    formats = ("pdf", "excel") if output_format == "both" else (output_format,)
    written = [Path(writers[fmt]()) for fmt in formats]

    return {
        "year": year,
        "ayanamsa": ayanamsa_name,
        "profile": profile,
        "location": {
            "name": location.name,
            "lat": location.lat,
            "lon": location.lon,
            "timezone": location.timezone,
        },
        "files": [
            {"name": path.name, "path": str(path), "format": path.suffix.lstrip(".")}
            for path in written
        ],
    }

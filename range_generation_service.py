from __future__ import annotations

from dataclasses import dataclass
import calendar
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

from export import apply_element_continuity_formatting, export_data
from main import _dates_in_range, run_generation
from panchang_service import resolve_location


@dataclass(frozen=True)
class GeneratedFile:
    name: str
    path: str


def _build_festival_date_index(
    start_year: int,
    end_year: int,
    lat: float,
    lon: float,
    ayanamsa_name: str,
    profile: str,
) -> dict[str, dict]:
    from jain_festival_service import generate_jain_festivals
    index: dict[str, dict] = {}
    for year in range(start_year, end_year + 1):
        fest_data = generate_jain_festivals(year, lat, lon, ayanamsa_name, profile)
        for f in fest_data.get("festivals", []):
            start_d = datetime.strptime(f["start_date"], "%Y-%m-%d").date()
            end_d = datetime.strptime(f["end_date"], "%Y-%m-%d").date()
            curr = start_d
            while curr <= end_d:
                d_str = curr.isoformat()
                if d_str not in index:
                    index[d_str] = {"festivals": [], "parva_tithis": []}
                entry = {"name": f["name"], "category": f["category"], "occurrence_id": f["occurrence_id"]}
                if f["category"] == "parva":
                    if not any(x["occurrence_id"] == f["occurrence_id"] for x in index[d_str]["parva_tithis"]):
                        index[d_str]["parva_tithis"].append(entry)
                else:
                    if not any(x["occurrence_id"] == f["occurrence_id"] for x in index[d_str]["festivals"]):
                        index[d_str]["festivals"].append(entry)
                curr += timedelta(days=1)
    return index


def generate_year_range_exports(
    *,
    start_year: int,
    end_year: int,
    city: str | None,
    lat: float | None,
    lon: float | None,
    ayanamsa_name: str,
    output_format: str,
    monthly: bool,
    workers: int,
    profile: str = "shwetambar_murtipujak_tapagachchha",
    output_dir: str = "/tmp",
) -> dict:
    location = resolve_location(city=city, lat=lat, lon=lon)
    tz_info = _timezone_snapshot(location.timezone, start_year)
    festival_index = _build_festival_date_index(
        start_year, end_year, location.lat, location.lon, ayanamsa_name, profile
    )
    config = {
        "lat": location.lat,
        "lon": location.lon,
        "tz_offset": tz_info["offset_hours"],
        "tz_label": tz_info["label"],
        "ayanamsa": ayanamsa_name,
        "festival_index": festival_index,
        "festival_profile": profile,
    }

    target_dir = Path(output_dir) / "jain_panchang_exports" / uuid4().hex
    target_dir.mkdir(parents=True, exist_ok=True)

    start_date = datetime(start_year, 1, 1).date()
    end_date = datetime(end_year, 12, 31).date()
    all_dates = list(_dates_in_range(start_date, end_date))
    rows = run_generation(config, all_dates, workers)
    formatted_rows = apply_element_continuity_formatting(rows, tz_offset=tz_info["offset_hours"])
    rows_generated = 0
    if monthly:
        for year in range(start_year, end_year + 1):
            for month in range(1, 13):
                month_start = datetime(year, month, 1).date()
                _, last_day = calendar.monthrange(year, month)
                month_end = datetime(year, month, last_day).date()

                scoped_start = max(month_start, start_date)
                scoped_end = min(month_end, end_date)
                if scoped_start > scoped_end:
                    continue

                month_rows = [
                    row for row in formatted_rows
                    if scoped_start <= datetime.fromisoformat(row["Date"]).date() <= scoped_end
                ]
                rows_generated += len(month_rows)

                base_name = target_dir / f"panchang_{year}_{month:02d}_{calendar.month_abbr[month]}"
                export_data(month_rows, str(base_name), output_format)
    else:
        rows_generated = len(formatted_rows)
        base_name = target_dir / f"panchang_{start_year}_{end_year}"
        export_data(formatted_rows, str(base_name), output_format)

    generated_paths = sorted(path for path in target_dir.iterdir() if path.is_file())

    return {
        "location": {
            "name": location.name,
            "lat": location.lat,
            "lon": location.lon,
            "timezone": location.timezone,
            "timezone_export_label": tz_info["label"],
            "timezone_export_offset_hours": tz_info["offset_hours"],
        },
        "start_year": start_year,
        "end_year": end_year,
        "format": output_format,
        "monthly": monthly,
        "workers": workers,
        "rows_generated": rows_generated,
        "files": [
            GeneratedFile(name=path.name, path=str(path))
            for path in generated_paths
        ],
    }


def _timezone_snapshot(tz_name: str, start_year: int) -> dict:
    tz = ZoneInfo(tz_name)
    sample_dt = datetime(start_year, 1, 1, 12, tzinfo=tz)
    offset = sample_dt.utcoffset()
    offset_hours = 0.0 if offset is None else offset.total_seconds() / 3600.0
    label = sample_dt.tzname() or tz_name
    return {
        "label": label,
        "offset_hours": offset_hours,
    }

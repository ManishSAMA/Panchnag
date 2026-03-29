from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PanchangRequest:
    input_date: str
    city: str | None
    lat: float | None
    lon: float | None
    ayanamsa_name: str


@dataclass(frozen=True)
class RangeGenerationRequest:
    start_year: int
    end_year: int
    city: str | None
    lat: float | None
    lon: float | None
    ayanamsa_name: str
    output_format: str
    monthly: bool
    workers: int


@dataclass(frozen=True)
class PdfGenerationRequest:
    year: int
    city: str | None
    lat: float | None
    lon: float | None
    ayanamsa_name: str


def parse_panchang_request(payload: dict | None) -> PanchangRequest:
    payload = payload or {}

    input_date = payload.get("date")
    if not input_date:
        raise ValueError("Missing required field: date")

    city = payload.get("city")
    if isinstance(city, str):
        city = city.strip() or None

    lat = _parse_optional_float(payload.get("lat"), "Latitude")
    lon = _parse_optional_float(payload.get("lon"), "Longitude")

    if (lat is None) ^ (lon is None):
        raise ValueError("Latitude and longitude must be provided together.")
    if city is None and lat is None and lon is None:
        raise ValueError("Provide either a city name or both latitude and longitude.")

    ayanamsa_name = payload.get("ayanamsa", "Lahiri")
    return PanchangRequest(
        input_date=input_date,
        city=city,
        lat=lat,
        lon=lon,
        ayanamsa_name=ayanamsa_name,
    )


def parse_range_generation_request(payload: dict | None) -> RangeGenerationRequest:
    payload = payload or {}

    start_year = _parse_required_int(payload.get("start_year"), "start_year")
    end_year = _parse_required_int(payload.get("end_year"), "end_year")
    if start_year > end_year:
        raise ValueError("start_year must be less than or equal to end_year.")

    city = payload.get("city")
    if isinstance(city, str):
        city = city.strip() or None

    lat = _parse_optional_float(payload.get("lat"), "Latitude")
    lon = _parse_optional_float(payload.get("lon"), "Longitude")

    if (lat is None) ^ (lon is None):
        raise ValueError("Latitude and longitude must be provided together.")
    if city is None and lat is None and lon is None:
        raise ValueError("Provide either a city name or both latitude and longitude.")

    ayanamsa_name = payload.get("ayanamsa", "Lahiri")
    output_format = payload.get("format", "csv")
    if output_format not in {"csv", "excel", "json", "all"}:
        raise ValueError("format must be one of: csv, excel, json, all.")

    workers = _parse_optional_int(payload.get("workers"), "workers")
    if workers is None:
        workers = 1
    if workers < 1:
        raise ValueError("workers must be at least 1.")

    return RangeGenerationRequest(
        start_year=start_year,
        end_year=end_year,
        city=city,
        lat=lat,
        lon=lon,
        ayanamsa_name=ayanamsa_name,
        output_format=output_format,
        monthly=bool(payload.get("monthly", False)),
        workers=workers,
    )


def parse_pdf_generation_request(payload: dict | None) -> PdfGenerationRequest:
    payload = payload or {}

    year = _parse_required_int(payload.get("year"), "year")

    city = payload.get("city")
    if isinstance(city, str):
        city = city.strip() or None

    lat = _parse_optional_float(payload.get("lat"), "Latitude")
    lon = _parse_optional_float(payload.get("lon"), "Longitude")

    if (lat is None) ^ (lon is None):
        raise ValueError("Latitude and longitude must be provided together.")
    if city is None and lat is None and lon is None:
        raise ValueError("Provide either a city name or both latitude and longitude.")

    ayanamsa_name = payload.get("ayanamsa", "Lahiri")

    return PdfGenerationRequest(
        year=year,
        city=city,
        lat=lat,
        lon=lon,
        ayanamsa_name=ayanamsa_name,
    )


def _parse_optional_float(value: object, field_name: str) -> float | None:
    if value in (None, ""):
        return None

    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric.") from exc


def _parse_optional_int(value: object, field_name: str) -> int | None:
    if value in (None, ""):
        return None

    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer.") from exc


def _parse_required_int(value: object, field_name: str) -> int:
    parsed = _parse_optional_int(value, field_name)
    if parsed is None:
        raise ValueError(f"Missing required field: {field_name}")
    return parsed

from __future__ import annotations

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Request dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PanchangRequest:
    input_date: str
    city: str | None
    lat: float | None
    lon: float | None
    ayanamsa_name: str
    calendar_system: str


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
    profile: str
    language: str = "en"


@dataclass(frozen=True)
class PdfGenerationRequest:
    year: int
    city: str | None
    lat: float | None
    lon: float | None
    ayanamsa_name: str


@dataclass(frozen=True)
class HindiPdfRequest:
    start_year: int
    start_month: int
    month_count: int
    city: str | None
    lat: float | None
    lon: float | None
    ayanamsa_name: str
    calendar_system: str


# ---------------------------------------------------------------------------
# Public parsers
# ---------------------------------------------------------------------------

def parse_panchang_request(payload: dict | None) -> PanchangRequest:
    payload = payload or {}

    input_date = payload.get("date")
    if not input_date:
        raise ValueError("Missing required field: date")

    city, lat, lon = _parse_location_fields(payload)
    ayanamsa_name = payload.get("ayanamsa", "Lahiri")

    return PanchangRequest(
        input_date=input_date,
        city=city,
        lat=lat,
        lon=lon,
        ayanamsa_name=ayanamsa_name,
        calendar_system=parse_calendar_system(payload.get("calendar_system")),
    )


def parse_range_generation_request(payload: dict | None) -> RangeGenerationRequest:
    payload = payload or {}

    start_year = _parse_required_int(payload.get("start_year"), "start_year")
    end_year = _parse_required_int(payload.get("end_year"), "end_year")
    if start_year > end_year:
        raise ValueError("start_year must be less than or equal to end_year.")

    city, lat, lon = _parse_location_fields(payload)
    ayanamsa_name = payload.get("ayanamsa", "Lahiri")

    output_format = payload.get("format", "csv")
    if output_format not in {"csv", "excel", "json", "all"}:
        raise ValueError("format must be one of: csv, excel, json, all.")

    language = payload.get("language", "en")
    if language not in {"en", "hi"}:
        raise ValueError("language must be one of: en, hi.")

    workers = _parse_optional_int(payload.get("workers"), "workers") or 1
    if workers < 1:
        raise ValueError("workers must be at least 1.")

    valid_profiles = {
        "shwetambar_murtipujak_tapagachchha",
        "shwetambar_sthanakvasi",
        "shwetambar_terapanthi",
    }
    profile = payload.get("profile", "shwetambar_murtipujak_tapagachchha")
    if profile not in valid_profiles:
        raise ValueError("Invalid profile. Must be one of: " + ", ".join(sorted(valid_profiles)))

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
        profile=profile,
        language=language,
    )


def parse_pdf_generation_request(payload: dict | None) -> PdfGenerationRequest:
    payload = payload or {}

    year = _parse_required_int(payload.get("year"), "year")
    city, lat, lon = _parse_location_fields(payload)
    ayanamsa_name = payload.get("ayanamsa", "Lahiri")

    return PdfGenerationRequest(
        year=year,
        city=city,
        lat=lat,
        lon=lon,
        ayanamsa_name=ayanamsa_name,
    )


def parse_hindi_pdf_request(payload: dict | None) -> HindiPdfRequest:
    payload = payload or {}

    start_year = _parse_required_int(payload.get("start_year"), "start_year")

    # Chaitra-to-Chaitra (March + 13 months) is the edition printed each year.
    start_month = _parse_optional_int(payload.get("start_month"), "start_month")
    start_month = 3 if start_month is None else start_month
    if not 1 <= start_month <= 12:
        raise ValueError("start_month must be between 1 and 12.")

    month_count = _parse_optional_int(payload.get("months"), "months")
    month_count = 13 if month_count is None else month_count
    if not 1 <= month_count <= 24:
        raise ValueError("months must be between 1 and 24.")

    city, lat, lon = _parse_location_fields(payload)

    return HindiPdfRequest(
        start_year=start_year,
        start_month=start_month,
        month_count=month_count,
        city=city,
        lat=lat,
        lon=lon,
        ayanamsa_name=payload.get("ayanamsa", "Lahiri"),
        calendar_system=parse_calendar_system(payload.get("calendar_system")),
    )


# ---------------------------------------------------------------------------
# Shared field parsers (private)
# ---------------------------------------------------------------------------

def parse_calendar_system(value: object) -> str:
    """Validate the Amanta/Purnimanta selector, defaulting to Purnimanta."""
    from panchang_service import CALENDAR_SYSTEMS, DEFAULT_CALENDAR_SYSTEM

    if value in (None, ""):
        return DEFAULT_CALENDAR_SYSTEM
    normalized = str(value).strip().lower()
    if normalized not in CALENDAR_SYSTEMS:
        raise ValueError(
            "calendar_system must be one of: " + ", ".join(CALENDAR_SYSTEMS)
        )
    return normalized


def _parse_location_fields(payload: dict) -> tuple[str | None, float | None, float | None]:
    """Extract and validate city, lat, lon from a payload dict.

    Returns (city, lat, lon). Raises ValueError for invalid combinations.
    """
    city = payload.get("city")
    if isinstance(city, str):
        city = city.strip() or None

    lat = _parse_optional_float(payload.get("lat"), "Latitude")
    lon = _parse_optional_float(payload.get("lon"), "Longitude")

    if (lat is None) ^ (lon is None):
        raise ValueError("Latitude and longitude must be provided together.")
    if city is None and lat is None and lon is None:
        raise ValueError("Provide either a city name or both latitude and longitude.")

    return city, lat, lon


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


@dataclass(frozen=True)
class JainFestivalsRequest:
    year: int
    city: str | None
    lat: float | None
    lon: float | None
    ayanamsa_name: str
    profile: str


def parse_jain_festivals_request(payload: dict | None) -> JainFestivalsRequest:
    payload = payload or {}

    year = _parse_required_int(payload.get("year"), "year")
    if not (1900 <= year <= 2200):
        raise ValueError("year must be between 1900 and 2200.")

    city, lat, lon = _parse_location_fields(payload)
    ayanamsa_name = payload.get("ayanamsa", "Lahiri")
    
    profile = payload.get("profile", "shwetambar_murtipujak_tapagachchha")
    valid_profiles = {
        "shwetambar_murtipujak_tapagachchha",
        "shwetambar_sthanakvasi",
        "shwetambar_terapanthi"
    }
    if profile not in valid_profiles:
        raise ValueError("Invalid profile. Must be one of: shwetambar_murtipujak_tapagachchha, shwetambar_sthanakvasi, shwetambar_terapanthi")

    return JainFestivalsRequest(
        year=year,
        city=city,
        lat=lat,
        lon=lon,
        ayanamsa_name=ayanamsa_name,
        profile=profile,
    )


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
    clock: str = "standard"
    sunrise_rule: str = "modern"


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
    clock: str = "standard"
    sunrise_rule: str = "modern"


@dataclass(frozen=True)
class PdfGenerationRequest:
    year: int
    city: str | None
    lat: float | None
    lon: float | None
    ayanamsa_name: str
    clock: str = "standard"
    sunrise_rule: str = "modern"


VALID_PROFILES = (
    "shwetambar_murtipujak_tapagachchha",
    "shwetambar_sthanakvasi",
    "shwetambar_terapanthi",
)
DEFAULT_PROFILE = VALID_PROFILES[0]
LAGHU_FORMATS = ("pdf", "excel", "both")


@dataclass(frozen=True)
class LaghuPanchangRequest:
    year: int
    city: str | None
    lat: float | None
    lon: float | None
    ayanamsa_name: str
    profile: str
    output_format: str
    clock: str = "standard"
    sunrise_rule: str = "modern"
    school: str = "all"


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
    clock: str = "standard"
    sunrise_rule: str = "modern"


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
        clock=parse_clock(payload.get("clock")),
        sunrise_rule=parse_sunrise_rule(payload.get("sunrise")),
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

    profile = _parse_profile(payload)

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
        clock=parse_clock(payload.get("clock")),
        sunrise_rule=parse_sunrise_rule(payload.get("sunrise")),
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
        clock=parse_clock(payload.get("clock")),
        sunrise_rule=parse_sunrise_rule(payload.get("sunrise")),
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
        clock=parse_clock(payload.get("clock")),
        sunrise_rule=parse_sunrise_rule(payload.get("sunrise")),
    )


def parse_laghu_panchang_request(payload: dict | None) -> LaghuPanchangRequest:
    payload = payload or {}

    year = _parse_required_int(payload.get("year"), "year")
    if not 1900 <= year <= 2100:
        raise ValueError("year must be between 1900 and 2100.")

    output_format = payload.get("format", "pdf")
    if output_format not in LAGHU_FORMATS:
        raise ValueError("format must be one of: " + ", ".join(LAGHU_FORMATS))

    city, lat, lon = _parse_location_fields(payload)

    return LaghuPanchangRequest(
        year=year,
        city=city,
        lat=lat,
        lon=lon,
        ayanamsa_name=payload.get("ayanamsa", "Lahiri"),
        profile=_parse_profile(payload),
        output_format=output_format,
        clock=parse_clock(payload.get("clock")),
        sunrise_rule=parse_sunrise_rule(payload.get("sunrise")),
        school=parse_school(payload.get("school")),
    )


# ---------------------------------------------------------------------------
# Shared field parsers (private)
# ---------------------------------------------------------------------------

def _parse_profile(payload: dict) -> str:
    profile = payload.get("profile", DEFAULT_PROFILE)
    if profile not in VALID_PROFILES:
        raise ValueError("Invalid profile. Must be one of: " + ", ".join(VALID_PROFILES))
    return profile



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


def _parse_choice(value: object, *, choices: tuple[str, ...], field: str) -> str:
    """Case-insensitive choice; None or "" gives the first (default) choice."""
    if value in (None, ""):
        return choices[0]
    normalized = str(value).strip().lower()
    if normalized not in choices:
        raise ValueError(f"{field} must be one of: " + ", ".join(choices))
    return normalized


def parse_clock(value: object) -> str:
    """Validate the clock setting, defaulting to standard time all year."""
    from astronomy import CLOCK_MODES

    return _parse_choice(value, choices=CLOCK_MODES, field="clock")


def parse_sunrise_rule(value: object) -> str:
    """Validate the sunrise rule ("sunrise" in requests), defaulting to modern."""
    from astronomy import SUNRISE_RULES

    return _parse_choice(value, choices=SUNRISE_RULES, field="sunrise")


def parse_school(value: object) -> str:
    """Validate the kalyanak school, defaulting to all schools."""
    from hindi_calendar_pdf import SCHOOL_CHOICES

    return _parse_choice(value, choices=SCHOOL_CHOICES, field="school")


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
    sunrise_rule: str = "modern"


def parse_jain_festivals_request(payload: dict | None) -> JainFestivalsRequest:
    payload = payload or {}

    year = _parse_required_int(payload.get("year"), "year")
    if not (1900 <= year <= 2200):
        raise ValueError("year must be between 1900 and 2200.")

    city, lat, lon = _parse_location_fields(payload)
    ayanamsa_name = payload.get("ayanamsa", "Lahiri")
    profile = _parse_profile(payload)

    return JainFestivalsRequest(
        year=year,
        city=city,
        lat=lat,
        lon=lon,
        ayanamsa_name=ayanamsa_name,
        profile=profile,
        sunrise_rule=parse_sunrise_rule(payload.get("sunrise")),
    )


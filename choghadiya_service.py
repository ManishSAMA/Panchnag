from __future__ import annotations

from datetime import date, datetime, timezone

from astronomy import jd_to_zoned_datetime

_DAY_CHOGHADIYA_ORDER = ["Udveg", "Char", "Labh", "Amrit", "Kaal", "Shubh", "Rog"]
_NIGHT_CHOGHADIYA_ORDER = ["Shubh", "Amrit", "Char", "Rog", "Kaal", "Labh", "Udveg"]

_CHOGHADIYA_MEANINGS = {
    "Udveg": "Tension", "Amrit": "Nectar", "Rog": "Illness",
    "Labh": "Gain", "Shubh": "Auspicious", "Char": "Movement", "Kaal": "Loss",
}
_CHOGHADIYA_NATURE = {
    "Udveg": "inauspicious", "Amrit": "auspicious", "Rog": "inauspicious",
    "Labh": "auspicious", "Shubh": "auspicious", "Char": "neutral", "Kaal": "inauspicious",
}

# Vara index: Sun=0 ... Sat=6 -> starting index in the day/night Choghadiya order
_DAY_START_IDX = [0, 3, 6, 2, 5, 1, 4]
_NIGHT_START_IDX = [0, 2, 4, 6, 5, 3, 1]


def calculate_choghadiya_slots(
    sunrise_jd: float,
    sunset_jd: float,
    next_sunrise_jd: float,
    weekday_index: int,
    tz_name: str,
    reference_date: date,
) -> list[dict]:
    """Return 16 choghadiya slots (8 day + 8 night) for a given day.

    Args:
        sunrise_jd: Julian day of sunrise.
        sunset_jd: Julian day of sunset.
        next_sunrise_jd: Julian day of the following day's sunrise.
        weekday_index: 0=Sunday … 6=Saturday (Vara convention).
        tz_name: IANA timezone name for formatting local times.
        reference_date: Civil date used for labelling (determines date suffix on slots).

    Returns:
        List of 16 slot dicts with keys: name, meaning, nature, start_time, end_time,
        start_local, end_local, start_utc, end_utc, start_label, end_label,
        duration_minutes, period.
    """
    day_start = _DAY_START_IDX[weekday_index]
    night_start = _NIGHT_START_IDX[weekday_index]

    def _label(local_dt: datetime | None) -> str:
        if local_dt is None:
            return ""
        time_label = local_dt.strftime("%I:%M %p").lstrip("0")
        if local_dt.date() == reference_date:
            return time_label
        return f"{time_label}, {local_dt.strftime('%B')} {local_dt.day}"

    def _make_slots(
        start_jd: float,
        end_jd: float,
        choghadiya_order: list[str],
        start_idx: int,
        period: str,
    ) -> list[dict]:
        slot_duration = (end_jd - start_jd) / 8
        slot_duration_minutes = slot_duration * 1440
        slots = []
        for i in range(8):
            name = choghadiya_order[(start_idx + i) % 7]
            slot_start = start_jd + i * slot_duration
            slot_end = start_jd + (i + 1) * slot_duration
            start_dt = jd_to_zoned_datetime(slot_start, tz_name)
            end_dt = jd_to_zoned_datetime(slot_end, tz_name)
            start_utc = start_dt.astimezone(timezone.utc) if start_dt else None
            end_utc = end_dt.astimezone(timezone.utc) if end_dt else None
            slots.append({
                "name": name,
                "meaning": _CHOGHADIYA_MEANINGS[name],
                "nature": _CHOGHADIYA_NATURE[name],
                "start_time": start_dt.strftime("%H:%M") if start_dt else "",
                "end_time": end_dt.strftime("%H:%M") if end_dt else "",
                "start_local": start_dt.isoformat(timespec="seconds") if start_dt else "",
                "end_local": end_dt.isoformat(timespec="seconds") if end_dt else "",
                "start_utc": start_utc.isoformat(timespec="seconds") if start_utc else "",
                "end_utc": end_utc.isoformat(timespec="seconds") if end_utc else "",
                "start_label": _label(start_dt),
                "end_label": _label(end_dt),
                "duration_minutes": round(slot_duration_minutes, 3),
                "period": period,
            })
        return slots

    return (
        _make_slots(sunrise_jd, sunset_jd, _DAY_CHOGHADIYA_ORDER, day_start, "day")
        + _make_slots(sunset_jd, next_sunrise_jd, _NIGHT_CHOGHADIYA_ORDER, night_start, "night")
    )

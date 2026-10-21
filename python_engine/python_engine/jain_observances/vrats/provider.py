import datetime
from astronomy import (
    local_date_anchor_jd,
    get_sunrise,
    jd_to_zoned_datetime,
    get_planetary_longitude,
)
from panchang import get_tithi
from location_service import get_timezone_name

# Providers hand vrat algorithms naive local times and read them back through a
# local-midnight anchor. Standard time keeps every day 24 h long, so that round
# trip is exact; the wall clock would be an hour off on a DST-change day.
_ENGINE_CLOCK = "standard"


class SwissEphTithiProvider:
    """
    Timezone-aware Tithi provider for Jain Vrat algorithms.
    Computes local sunrise from local date anchor (midnight local time)
    to guarantee exact astronomical date-to-Tithi accuracy.
    """
    def __init__(self, ayanamsa: str = "Lahiri", sunrise_rule: str = "modern", vriddhi: str = "first_day"):
        self.ayanamsa = ayanamsa
        self.sunrise_rule = sunrise_rule
        # "second_day": on a vriddhi the first day reads as the previous tithi
        # (वृद्धौ कार्या तथोत्तरा); see jain_day_tithi below.
        self.vriddhi = vriddhi
        self._tz_cache: dict[tuple[float, float], str] = {}

    def _get_tz(self, lat: float, lon: float) -> str:
        key = (float(lat), float(lon))
        if key not in self._tz_cache:
            self._tz_cache[key] = get_timezone_name(lat, lon)
        return self._tz_cache[key]

    def get_sunrise(self, date_obj: datetime.date, lat: float, lon: float) -> datetime.datetime:
        tz_name = self._get_tz(lat, lon)
        anchor_jd = local_date_anchor_jd(date_obj, tz_name, clock=_ENGINE_CLOCK)
        sunrise_jd = get_sunrise(anchor_jd, lat, lon, self.sunrise_rule)
        sunrise_dt = jd_to_zoned_datetime(sunrise_jd, tz_name, clock=_ENGINE_CLOCK)
        return sunrise_dt.replace(tzinfo=None)

    def get_tithi_at_time(self, time_obj: datetime.datetime, lat: float, lon: float) -> int:
        tz_name = self._get_tz(lat, lon)
        anchor_jd = local_date_anchor_jd(time_obj.date(), tz_name, clock=_ENGINE_CLOCK)
        time_offset_hours = time_obj.hour + time_obj.minute / 60.0 + time_obj.second / 3600.0
        jd = anchor_jd + (time_offset_hours / 24.0)
        sun_lon = get_planetary_longitude(jd, 'Sun', self.ayanamsa)
        moon_lon = get_planetary_longitude(jd, 'Moon', self.ayanamsa)
        return get_tithi(sun_lon, moon_lon)

    def is_adhik_month(self, date_obj: datetime.date, lat: float, lon: float) -> bool:
        from panchang import get_hindu_month, JAIN_TITHI_OFFSET_DAYS
        tz_name = self._get_tz(lat, lon)
        anchor_jd = local_date_anchor_jd(date_obj, tz_name, clock=_ENGINE_CLOCK)
        sunrise_jd = get_sunrise(anchor_jd, lat, lon, self.sunrise_rule)
        _, _, is_adhika = get_hindu_month(sunrise_jd + JAIN_TITHI_OFFSET_DAYS, self.ayanamsa)
        return is_adhika

    def get_hindu_month_name(self, date_obj: datetime.date, lat: float, lon: float) -> str:
        from panchang import get_hindu_month, JAIN_TITHI_OFFSET_DAYS
        tz_name = self._get_tz(lat, lon)
        anchor_jd = local_date_anchor_jd(date_obj, tz_name, clock=_ENGINE_CLOCK)
        sunrise_jd = get_sunrise(anchor_jd, lat, lon, self.sunrise_rule)
        m_name, _, _ = get_hindu_month(sunrise_jd + JAIN_TITHI_OFFSET_DAYS, self.ayanamsa)
        return m_name.removeprefix("Adhika ")


def jain_day_tithi(provider, day: datetime.date, lat: float, lon: float) -> int:
    """The tithi owning `day` at the Jain day-start (sunrise + 144 min).

    With provider.vriddhi == "second_day", the first of two days sharing that
    tithi reads as the previous tithi, so a vrat lands on the second day.
    Works with any provider exposing get_sunrise / get_tithi_at_time.
    """
    from jain_observances.vriddhi import previous_tithi

    def at_day_start(d: datetime.date) -> int:
        return provider.get_tithi_at_time(provider.get_sunrise(d, lat, lon) + datetime.timedelta(minutes=144), lat, lon)

    tithi = at_day_start(day)
    if getattr(provider, "vriddhi", "first_day") != "second_day":
        return tithi
    return previous_tithi(tithi) if at_day_start(day + datetime.timedelta(days=1)) == tithi else tithi

import datetime
from astronomy import (
    local_date_anchor_jd,
    get_sunrise,
    jd_to_zoned_datetime,
    get_planetary_longitude,
)
from panchang import get_tithi
from location_service import get_timezone_name


class SwissEphTithiProvider:
    """
    Timezone-aware Tithi provider for Jain Vrat algorithms.
    Computes local sunrise from local date anchor (midnight local time)
    to guarantee exact astronomical date-to-Tithi accuracy.
    """
    def __init__(self, ayanamsa: str = "Lahiri"):
        self.ayanamsa = ayanamsa
        self._tz_cache: dict[tuple[float, float], str] = {}

    def _get_tz(self, lat: float, lon: float) -> str:
        key = (float(lat), float(lon))
        if key not in self._tz_cache:
            self._tz_cache[key] = get_timezone_name(lat, lon)
        return self._tz_cache[key]

    def get_sunrise(self, date_obj: datetime.date, lat: float, lon: float) -> datetime.datetime:
        tz_name = self._get_tz(lat, lon)
        anchor_jd = local_date_anchor_jd(date_obj, tz_name)
        sunrise_jd = get_sunrise(anchor_jd, lat, lon)
        sunrise_dt = jd_to_zoned_datetime(sunrise_jd, tz_name)
        return sunrise_dt.replace(tzinfo=None)

    def get_tithi_at_time(self, time_obj: datetime.datetime, lat: float, lon: float) -> int:
        tz_name = self._get_tz(lat, lon)
        anchor_jd = local_date_anchor_jd(time_obj.date(), tz_name)
        time_offset_hours = time_obj.hour + time_obj.minute / 60.0 + time_obj.second / 3600.0
        jd = anchor_jd + (time_offset_hours / 24.0)
        sun_lon = get_planetary_longitude(jd, 'Sun', self.ayanamsa)
        moon_lon = get_planetary_longitude(jd, 'Moon', self.ayanamsa)
        return get_tithi(sun_lon, moon_lon)

    def is_adhik_month(self, date_obj: datetime.date, lat: float, lon: float) -> bool:
        from panchang import get_hindu_month
        tz_name = self._get_tz(lat, lon)
        anchor_jd = local_date_anchor_jd(date_obj, tz_name)
        sunrise_jd = get_sunrise(anchor_jd, lat, lon)
        _, _, is_adhika = get_hindu_month(sunrise_jd, self.ayanamsa)
        return is_adhika

    def get_hindu_month_name(self, date_obj: datetime.date, lat: float, lon: float) -> str:
        from panchang import get_hindu_month
        tz_name = self._get_tz(lat, lon)
        anchor_jd = local_date_anchor_jd(date_obj, tz_name)
        sunrise_jd = get_sunrise(anchor_jd, lat, lon)
        m_name, _, _ = get_hindu_month(sunrise_jd, self.ayanamsa)
        return m_name.removeprefix("Adhika ")

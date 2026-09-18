import sys
from datetime import date, timedelta
from panchang_service import resolve_location, _calculate_daily_events
from yoga_service import detect_all_yogas_for_day

def run():
    start = date(2025, 1, 1)
    for i in range(365):
        d = start + timedelta(days=i)
        loc = resolve_location(city="New Delhi")
        ev = _calculate_daily_events(d, loc)
        yogas = detect_all_yogas_for_day(
            date_obj=d,
            sunrise_jd=ev.sunrise_jd,
            next_sunrise_jd=ev.next_sunrise_jd,
            tz_name=loc.timezone,
            ayanamsa="Lahiri"
        )
        if yogas.get("ravi_yogas"):
            print(f"Date: {d}")
            for r in yogas["ravi_yogas"]:
                print(f"  {r['start_time']} - {r['end_time']}  (dist: {r.get('trigger_detail')})")

if __name__ == "__main__":
    run()

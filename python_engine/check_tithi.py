
from astronomy import local_date_anchor_jd, get_tithi, get_planetary_longitude, get_sunrise
from datetime import date
jd1 = local_date_anchor_jd(date(2026, 3, 21), 'Asia/Kolkata', 0)
sr1 = get_sunrise(jd1, 28.6139, 77.2090)
jd2 = local_date_anchor_jd(date(2026, 3, 24), 'Asia/Kolkata', 0)
sr2 = get_sunrise(jd2, 28.6139, 77.2090)
steps = 30
dt = (sr2-sr1)/steps
for i in range(steps+1):
    t = sr1 + i*dt
    sl = get_planetary_longitude(t, 'Sun', 'Lahiri')
    ml = get_planetary_longitude(t, 'Moon', 'Lahiri')
    print(f'{t:.3f}: tithi {get_tithi(sl, ml)}')


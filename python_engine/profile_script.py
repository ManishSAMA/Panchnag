import sys, time
from unittest.mock import MagicMock
sys.modules['timezonefinder'] = MagicMock()
sys.modules['timezonefinder'].TimezoneFinder.return_value.timezone_at.return_value = 'Asia/Kolkata'

from jain_observances.festival_service import generate_jain_festivals

start = time.time()
res = generate_jain_festivals(year=2026, lat=28.61, lon=77.2, profile='all')
print(f'Time taken: {time.time() - start:.2f}s, festivals: {len(res.get("festivals", []))}')

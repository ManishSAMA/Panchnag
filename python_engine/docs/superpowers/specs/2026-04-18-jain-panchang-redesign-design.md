# Jain Panchang Frontend Redesign — Design Spec
**Date:** 2026-04-18  
**Status:** Approved

---

## Context

The existing app is a functional Flask + Swiss Ephemeris panchang calculator with a working calendar/day-panel SPA. The frontend looks utilitarian. Goal: completely redesign the frontend to match the Drik Panchang aesthetic — warm traditional Indian feel, deep red headers, golden-yellow cards, olive date banners — while adding a Choghadiya Muhurta feature with a live countdown timer.

---

## Architecture

**SPA with hash-based routing.** Three frontend files replaced entirely; all backend code untouched except one new endpoint.

### Files Changed

| File | Action |
|------|--------|
| `templates/index.html` | Replace — new SPA shell with all page templates |
| `static/app.js` | Replace — hash router + page controllers |
| `static/app.css` | Replace — new design system |
| `app.py` | Add only: `POST /choghadiya` endpoint |

### Hash Routes

| Hash | Page |
|------|------|
| `#home` | Home (default) |
| `#calendar` | Hindu Calendar |
| `#panchang` | Dainika Panchang (reads `?date=YYYY-MM-DD`) |
| `#muhurta` | Dainika Muhurta |
| `#choghadiya` | Choghadiya Muhurta (reads `?date=YYYY-MM-DD`) |
| `#location` | Change Location |
| `#settings` | Settings (export tools + language + ayanamsa) |

### Persistent State (localStorage key: `jain_panchang_v2`)

```json
{
  "lat": 26.9124,
  "lon": 75.7873,
  "locationName": "Jaipur, Rajasthan, India",
  "ayanamsa": "Lahiri",
  "lang": "en",
  "timeFormat": "12h"
}
```

---

## Design System

```css
--red:        #8B1A1A   /* navbar, header backgrounds */
--gold:       #F5D080   /* card backgrounds, page bg */
--gold-dark:  #F0C040   /* card borders, accents */
--olive:      #6B6B00   /* date banner background */
--white:      #FFFFFF
--text-red:   #8B1A1A   /* labels on light backgrounds */
--text-black: #1A1A1A   /* values on light backgrounds */
--green-slot: #2E7D32   /* auspicious Choghadiya */
--red-slot:   #B71C1C   /* inauspicious Choghadiya */
--gray-slot:  #757575   /* neutral Choghadiya */
```

**Mobile-first.** Max width 480px centered on desktop. Touch-friendly padding (min 44px tap targets).

---

## Shared Components

### Navbar
- Red background, white text
- **Home:** hamburger (left) | "Jain Panchang" (center) | search + ⋮ (right)
- **Inner pages:** ← (left) | page title (center)
- Hamburger opens left-side drawer with links to all pages

### Date Banner
- Olive background, white text
- Left: moon phase emoji based on tithi index
- Right: Gregorian date (large)
- Below: Vikram Samvat | Hindu month | Tithi | Location name

---

## Page Designs

### 1. Home Page (`#home`)

1. Navbar (hamburger variant)
2. Date banner — fetches `/generate-panchang` for today on load
3. 2-column card grid:
   - 🗓️ Hindu Calendar → `#calendar`
   - 📜 Dainika Panchang → `#panchang?date=today`
   - 🕐 Dainika Muhurta → `#muhurta`
   - 🌙 Nakshatra → `#panchang?date=today` (shows nakshatra section)
   - 📍 Change Location → `#location`
   - ⚙️ Settings → `#settings`

Card style: golden-yellow bg, subtle border, emoji icon, bold red title, small description text.

### 2. Calendar Page (`#calendar`)

1. Navbar (back arrow, "Hindu Calendar")
2. Olive banner: selected month/year + Vikram Samvat
3. Horizontal scrollable toolbar: Vertical | Purnimanta | Date | Today | Calendar
4. Month nav row: `< April 2026 >`
5. 7-column calendar grid (Sun–Sat headers)
6. Day cells:
   - Top-left: Gregorian date (bold red if today)
   - Top-right: tithi number (small)
   - Bottom-left: sunrise HH:MM (small gray)
   - Bottom-right: sunset HH:MM (small gray)
   - Below: nakshatra name (small)
   - Today: olive/green highlight
7. Tap day → `#panchang?date=YYYY-MM-DD`

**Data:** single call to `/month-overview` GET (already batches all days). Sunrise/sunset per cell pulled from `/generate-panchang` per day — lazy-loaded as user scrolls (or fetched month-batch via Promise.all with concurrency limit of 5).

### 3. Dainika Panchang Page (`#panchang`)

1. Navbar (back arrow, "Dainika Panchang")
2. Olive date banner
3. Time format toggle: `[12 Hour] [24 Hour]` — stored in localStorage
4. Golden-yellow info card:
   - Sunrise 🌅 | Sunset 🌇 (side-by-side)
   - Moonrise 🌕 | Moonset (side-by-side)
   - Labeled rows: Tithi (+ "upto HH:MM"), Nakshatra, Yoga, Karana, Weekday
   - If field has 2 values (tithi crosses midnight), show both lines
5. Red label text, black value text

**Data:** `/generate-panchang` POST with date from hash + stored location.

### 4. Dainika Muhurta Page (`#muhurta`)

1. Navbar (back arrow, "Dainika Muhurta")
2. 2-column card grid:
   - 🪔 Choghadiya Muhurta → `#choghadiya`
   - ⏰ Hora Muhurta → placeholder alert "Coming soon"
   - ✨ Lagna Muhurta → placeholder alert
   - 🌙 Chandrabalam → placeholder alert
   - ⭐ Tarabalam → placeholder alert

### 5. Choghadiya Page (`#choghadiya`)

1. Navbar (back arrow, "Choghadiya Muhurta")
2. Top banner (golden-yellow):
   - Left: current slot time range
   - Right: dark green box with slot name + quality (e.g. "🪔 Amrit – Best")
   - Below: live countdown `HH:MM:SS` + today's date
3. Time format toggle: `[12 Hour] [24 Hour] [24 Plus]`
4. Date nav row: `< Sat, April 18, 2026 >` + weekday tab strip (Sun–Sat, current highlighted olive)
5. Day section header: "☀️ Day" | "🌅 Sunrise – HH:MM" (golden-yellow bg)
6. 8 day Choghadiya rows:
   - Left cell (~40% width): name + meaning, colored bg (red/green/gray), white text, 🪔 right
   - Right cell: time range, light golden bg; icon: ❌ inauspicious | ⏳ current | ✓ auspicious
7. Night section header: "🌙 Night" | "🌇 Sunset – HH:MM"
8. 8 night Choghadiya rows (same format)

**Countdown timer:** `setInterval(1000)` recalculates remaining seconds each tick. On slot boundary, refetches data and re-renders.

**Date navigation:** changing date refetches `/choghadiya` and rerenders. Weekday tabs are shortcuts within the current week.

### 6. Location Page (`#location`)

Reuses existing city search autocomplete + manual lat/lon fields. Saves to localStorage `jain_panchang_v2`. On save, refreshes current page data.

### 7. Settings Page (`#settings`)

- Language toggle: EN / हि
- Ayanamsa selector: Lahiri / Raman / Krishnamurti
- Time format default: 12h / 24h
- Export section (from existing app): PDF year, CSV/Excel range

---

## Backend: New `/choghadiya` Endpoint

**Location in `app.py`:** add after existing endpoints, following same validation pattern as other POSTs.

```python
POST /choghadiya
Body: { "date": "YYYY-MM-DD", "lat": float, "lon": float }
```

**Constants:**
```python
CHOGHADIYA_ORDER = ['Udveg','Amrit','Rog','Labh','Shubh','Char','Kaal']
CHOGHADIYA_MEANINGS = {
    'Udveg':'Tension','Amrit':'Nectar','Rog':'Illness',
    'Labh':'Gain','Shubh':'Auspicious','Char':'Movement','Kaal':'Loss'
}
CHOGHADIYA_NATURE = {
    'Udveg':'inauspicious','Amrit':'auspicious','Rog':'inauspicious',
    'Labh':'auspicious','Shubh':'auspicious','Char':'neutral','Kaal':'inauspicious'
}
# Python weekday(): Mon=0, Tue=1, Wed=2, Thu=3, Fri=4, Sat=5, Sun=6
# Index into CHOGHADIYA_ORDER for first slot of day/night
DAY_START_IDX   = [1,2,3,4,5,6,0]   # Mon→Amrit, Tue→Rog, Wed→Labh, Thu→Shubh, Fri→Char, Sat→Kaal, Sun→Udveg
NIGHT_START_IDX = [5,6,0,1,2,3,4]   # Mon→Char, Tue→Kaal, Wed→Udveg, Thu→Amrit, Fri→Rog, Sat→Labh, Sun→Shubh
```

**Algorithm:**
1. Parse date → get timezone from stored location (use `lat/lon` → `timezonefinder` or pass tz_name; actually use same pattern as existing code — get JD from local_date_anchor_jd)
2. Get sunrise JD for date, sunset JD for date, sunrise JD for date+1 (next day)
3. Compute `weekday = datetime.strptime(date, "%Y-%m-%d").weekday()`
4. Split day into 8 equal slots between sunrise and sunset
5. Split night into 8 equal slots between sunset and next sunrise
6. Walk ORDER starting from DAY_START_IDX[weekday], mod 7, for 8 slots
7. Walk ORDER starting from NIGHT_START_IDX[weekday], mod 7, for 8 slots
8. Convert slot JD boundaries to local time strings via `jd_to_local_time_string`

**Response:**
```json
{
  "date": "2026-04-18",
  "sunrise": "05:55",
  "sunset": "18:43",
  "slots": [
    {
      "name": "Udveg",
      "meaning": "Tension",
      "nature": "inauspicious",
      "start_time": "05:55",
      "end_time": "07:31",
      "period": "day"
    }
    // ...16 total
  ]
}
```

**Timezone:** use `timezonefinder` (already a dependency — existing code uses it in `location_service.py`) to get tz_name from lat/lon, then use `local_date_anchor_jd(date, tz_name)` from `astronomy.py`.

---

## Verification

1. `python app.py` — server starts, no errors
2. Open browser → `http://localhost:5000` → home page renders with red navbar + golden cards
3. Home date banner shows today's panchang data (no location set → prompt to set location)
4. Set location → banner updates, Calendar loads, day cells show tithi/nakshatra/times
5. Navigate to Choghadiya → 16 slots render, countdown ticking, current slot highlighted
6. Change date via arrows → slots refetch and rerender
7. All existing backend tests pass: `pytest tests/`
8. `curl -X POST /choghadiya -H 'Content-Type: application/json' -d '{"date":"2026-04-18","lat":26.91,"lon":75.79}'` → 200 with 16 slots

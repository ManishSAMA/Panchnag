# Panchang Calculations

The **Panchang Generator** relies on highly accurate ephemeris data provided by the C-based Swiss Ephemeris (`pyswisseph`). The foundational data includes planetary sidereal longitudes, from which the Vedic Panchang elements ("Pancha Anga", or Five Limbs) are derived.

Here is a step-by-step breakdown of how the daily elements are calculated.

---

## 1. Time Setup: Julian Date

All astronomical functions take a **Julian Day Number (JD)** as input.
By local Vedic tradition, the civil day starts at sunrise. However, typical daily almanacs evaluate the planetary positions at a standardized time—commonly 05:30 IST (Indian Standard Time).

1. Convert local time (e.g., `05:30 IST`) to **UTC** (e.g., `00:00 UTC`).
2. Pass the date and UTC hour into `swe.julday(year, month, day, hour_utc)` to get the Julian Date.

---

## 2. Ayanamsa & Planetary Longitudes

In Vedic astrology, planetary positions are measured against the fixed stars (Sidereal/Nirayana system). This requires subtracting the **Ayanamsa** (precessional offset) from the Tropical (Sayana) longitudes.

1. **Ayanamsa**: We set the sidereal mode `swe.set_sid_mode()` according to the user's choice (e.g., Lahiri, Raman, or Krishnamurti) and get the precessional difference using `swe.get_ayanamsa_ut()`.
2. **Geocentric Apparent Longitudes**: We fetch the position of celestial bodies (Sun, Moon, Mars, etc.) using `swe.calc_ut()` with the flags `FLG_SWIEPH | FLG_SIDEREAL | FLG_SPEED`.
   - This returns the decimal degree `[0, 360)` of the planet in the sidereal zodiac.
   - For **Rahu/Ketu**, we use the *True Lunar North Node*. Ketu is computed as `(Rahu_Longitude + 180) % 360`.

---

## 3. The 5 Panchang Elements (Pancha Anga)

With the specific longitudes of the Sun and Moon (`Sun_Lon` and `Moon_Lon`) determined for the day, we calculate the five limbs:

### I. Tithi (Lunar Day)
The `Tithi` is based on the angular difference between the Moon and the Sun. There are 30 Tithis in a lunar month, evenly divided into 12° segments.

**Formula:**
```text
Difference = (Moon_Lon - Sun_Lon) % 360
Tithi_Index = FLOOR( Difference / 12.0 ) + 1
```
*Result*: A value from 1 to 30. Tithi 15 is Purnima (Full Moon), and Tithi 30 is Amavasya (New Moon).

### II. Nakshatra (Lunar Mansion)
The zodiac of 360° is divided into 27 `Nakshatras`, each spanning exactly 13° 20' (or 13.3333°).

**Formula:**
```text
Nakshatra_Index = FLOOR( Moon_Lon / (360 / 27) ) + 1
```
We also calculate the `Pada` (quarter) by dividing each Nakshatra into 4 parts (3° 20' each):
```text
Pada_Index = FLOOR( Moon_Lon / ((360 / 27) / 4) ) % 4 + 1
```

### III. Yoga (Luni-Solar Combination)
The `Yoga` depends on the **sum** of the longitudes of the Sun and the Moon, rather than the difference. There are 27 Yogas.

**Formula:**
```text
Sum = (Sun_Lon + Moon_Lon) % 360
Yoga_Index = FLOOR( Sum / (360 / 27) ) + 1
```

### IV. Karana (Half-Tithi)
A `Karana` is exactly half of a Tithi (spanning 6° of the lunar–solar difference). Since there are 30 Tithis in a month, there are 60 Karanas.

**Formula:**
```text
Difference = (Moon_Lon - Sun_Lon) % 360
Karana_Index = FLOOR( Difference / 6.0 ) + 1
```
The 60 Karanas are mapped cyclically to an 11-Karana name list (4 fixed Karanas and 7 movable Karanas repeating 8 times).

### V. Vara (Weekday)
Vedic weekdays map directly to modern weekdays (0 = Sunday to 6 = Saturday). This is easily derived from the astronomical Julian Day because JD 0 was on a Monday (noon). We add an offset to align noon-epochs and map properly to the day of the week.

**Formula:**
```text
Vara_Index = (FLOOR(Julian_Date + 0.5) + 1) % 7
```

---

## 4. Rise / Set Times

**Sunrise, Sunset, Moonrise, and Moonset** are calculated contextually based on the user's Geographic Coordinate location.

1. Using `swe.rise_trans()` with the `BIT_DISC_CENTER` modifier.
2. The search starts from `00:00 UTC` of the target calendar date.
3. The returned times are converted back from UTC Julian Dates to the requested Timezone (e.g. UTC+5:30) using standard local time fraction math to determine `HH:MM:SS`.

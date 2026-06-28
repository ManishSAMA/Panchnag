# Sun Arc-Minute Tracker — Desktop App

A clean, modern Python desktop application that computes the exact times when the Sun's tropical longitude crosses every 1-arcminute boundary for a user-specified range of years. The software exports these events to a beautifully formatted Excel spreadsheet.

Calculations are powered by **Skyfield** (using astronomical algorithms and JPL DE421 ephemeris data) for maximum precision, and **Swiss Ephemeris** for accurate Lahiri Ayanamsa calculations.

## Features

- **JPL Ephemeris Accuracy**: Powered by Skyfield.
- **Vedic Traditional Columns**: Exports Date, Time (IST, minute-level resolution), Rashi, Ansha, Kala, Vikala, and Ayanamsa_DM.
- **Fast Execution**: Uses numpy vectorized calculation, completing an entire year's scan in less than 8 seconds.
- **Desktop GUI**: Clean themed layout with progress indicators and status logs.
- **Antivirus Safe**: Compiled with metadata structures to minimize antivirus false positives.

---

## Installation

Ensure you have Python 3.8+ installed.

1. Navigate to this directory:
   ```bash
   cd sun_tracker
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

### Run from Source
Execute the following command to open the GUI application:
```bash
python main.py
```

### GUI Operations
1. **Start/End Year**: Enter the year range to query (e.g. 2026 to 2026).
2. **City Selection**: Choose a city (Delhi, Kolkata, Mumbai, Chennai). The Sun's ecliptic longitude is geocentric (identical globally), but times will be displayed in IST (UTC+5:30) for all.
3. **Output Directory**: Choose where the exported files (e.g. `Sun_Delhi_2026.xlsx`) will be saved.
4. **Generate**: Click **Generate Excel Report**. 

---

## Building a Standalone Executable (.exe)

Compile this application into a standalone `.exe` using PyInstaller.

Run the following command in the parent directory:
```bash
pyinstaller --noconsole --onefile --noconfirm --name "SunTracker" --icon="sun_tracker/icon.ico" --version-file="sun_tracker/file_version_info.txt" --add-data "sun_tracker/icon.ico;sun_tracker" --collect-data "skyfield" sun_tracker/main.py
```

*Note: Skyfield uses data files, so compiling with `--collect-data "skyfield"` ensures Skyfield's data assets are properly packaged inside the executable.*

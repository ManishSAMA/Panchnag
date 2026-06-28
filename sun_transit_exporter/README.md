# Sun Transit Excel Exporter

A clean, modern Python desktop application that computes the exact times when the Sun's tropical longitude crosses every 1-arcminute boundary for a user-specified range of years. The software exports these events to a beautifully formatted Excel spreadsheet.

## Features

- **Tkinter GUI**: Easy-to-use graphical interface.
- **Background Threading**: Keeps the UI responsive during computation.
- **Parallax Accuracy**: Supports topocentric calculations for four major Indian cities (Delhi, Mumbai, Kolkata, Chennai) using their exact geographic coordinates.
- **Elegant Excel Styling**: Auto-adjusts column widths, styles headers with a professional dark blue fill, centers text columns, right-aligns numeric columns, and enables gridlines.
- **Quick-Open Integration**: Open the generated Excel file directly from the GUI after generation.

---

## Installation

Ensure you have Python 3.8+ installed.

1. Navigate to this directory:
   ```bash
   cd sun_transit_exporter
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
python app.py
```

### GUI Operations
1. **Start/End Year**: Enter the year range to query (e.g. 2026 to 2026).
2. **City Selection**: Choose a city (Delhi, Mumbai, Kolkata, Chennai) to calculate the precise topocentric positions (exact coordinates).
3. **Output Directory**: Browse to choose where the exported file will be saved.
4. **Generate**: Click **Generate Excel Report**. A progress bar and live log trace will display the status.
5. **Open Excel**: Once finished, click **Open Excel File** to open the report directly in your system default spreadsheet viewer (like Microsoft Excel).

---

## Building a Standalone Executable (.exe)

You can compile this application into a standalone `.exe` using PyInstaller.

Run the following command in this directory:
```bash
pyinstaller --noconsole --onefile --name "SunTransitExporter" app.py
```

- `--noconsole`: Hides the background command prompt window when the app runs.
- `--onefile`: Bundles everything into a single standalone executable file.
- The compiled `.exe` will be created in the `dist/` folder.

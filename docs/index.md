# Panchang Generator

Welcome to the **Panchang Generator**, a high-precision, Python-based CLI tool dedicated to calculating Vedic Ephemeris (Panchang) elements. Powered by the renowned [Swiss Ephemeris](#) (`pyswisseph`), it calculates highly accurate planetary positions and core Panchang elements for any location on Earth over any specified date range.

## What is a Panchang?
Panchang (or Panchanga) is a traditional Hindu calendar system based on the positions of the Sun and the Moon. It comprises five key attributes ("Pancha Anga"):
1. **Tithi** (Lunar Day)
2. **Nakshatra** (Lunar Mansion or Constellation)
3. **Yoga** (Luni-Solar combination)
4. **Karana** (Half-Tithi)
5. **Vara** (Weekday)

## Key Features
- **High Precision:** Computes exact planetary longitudes up to seconds using the Swiss Ephemeris (`pyswisseph`).
- **Ayanamsa Support:** Native support for Lahiri, Raman, and Krishnamurti ayanamsa systems.
- **Data Export:** Generate the parsed records in **CSV**, **Excel (.xlsx)**, **JSON**, or even a well-formatted **PDF Table**.
- **Flexibility:** Customize latitude, longitude, and custom time zones to determine the localized sunrise/sunset/moonrise/moonset timings for accurate start/end constraints.
- **Multiprocessing Support:** Drastically speed up large data generation (like an ephemeris for multiple decades) using CPU parallel processing.
- **Built-in Visualizations:** Tools to graph planetary motions intuitively, display Tithi frequency, or show an element-based heatmap calendar.

## Documentation Contents

- [**Setup and Usage**](./setup_and_usage.md) - Learn how to install prerequisites and run the generator from the CLI. Includes examples.
- [**Architecture**](./architecture.md) - Get a high-level overview of how the tools function, interact with the Swiss Ephemeris, and construct the dates.
- [**Components Details**](./components.md) - Explore what each underlying Python module (`astronomy.py`, `panchang.py`, etc.) accomplishes.
- [**Panchang Calculations**](./calculations.md) - Detailed formulas and steps explaining how each astronomical element is calculated from Julian dates and planetary longitudes.
- [**Visualizations Guide**](./visualizations.md) - Dive into mapping astronomical phenomena to visual graphics using `visualize.py`.

# Documentation Index

Welcome to the long-form documentation for Jain Panchang. The README is the quick front door; this directory explains how to run, use, extend, and reason about the project in more detail.

## Recommended Reading Order

If you are new to the project, read:

1. [Setup and usage](./setup_and_usage.md)
2. [API reference](./api.md)
3. [Architecture](./architecture.md)
4. [Components](./components.md)
5. [Calculations](./calculations.md)

## By Goal

### Run the app

Use [Setup and usage](./setup_and_usage.md) for:

- local installation
- web app startup
- daily lookup
- month overview
- Choghadiya lookup
- year-range exports
- PDF generation
- CLI examples
- common validation rules

### Integrate with the app

Use [API reference](./api.md) for:

- endpoint list
- request payloads
- response shapes
- download behavior
- location input rules

### Work on the code

Start with [Architecture](./architecture.md), then [Components](./components.md).

Those docs explain:

- how requests move through Flask, parsing, services, astronomy, and exporters
- why the daily, range, and PDF flows have separate service boundaries
- where to add new features
- where rule logic belongs
- where export and serialization logic belongs

### Understand the calculations

Use [Calculations](./calculations.md) for:

- Julian Day and timezone handling
- Swiss Ephemeris usage
- ayanamsa behavior
- Tithi, Nakshatra, Yoga, Karana, and Vara formulas
- transition end-time search
- sunrise-bound daily labeling
- Jain Tithi reference handling

Use [Hindi calculations](./Hindi_calculations.md) for a simpler Hindi explanation of the calculation flow.

### Debug generated data

Use [Visualizations](./visualizations.md) for:

- planetary longitude charts
- Tithi frequency charts
- Panchang element heatmaps
- CSV diff comparisons
- single-day console dumps

## Feature Coverage

The documentation covers all current product flows:

- daily Panchang lookup
- month overview (calendar grid data)
- Choghadiya (auspicious time slots)
- year-range CSV / Excel / JSON exports
- PDF calendar generation
- Jain festival generation (three Shwetambar profiles)
- Dainika Muhurta (daily Yoga detection)
- SQLite database pre-computation for fast repeated lookups

## Scope Note

The project documents itself as a sunrise-based Panchang generator with Jain Tithi reference support and sect-specific festival rules for three Shwetambar profiles. It does not claim to fully encode every Agamic or Digambar Jain calendrical rule.

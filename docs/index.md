# Documentation Index

This directory contains the long-form documentation for the project.

## Recommended Reading Order

If you are new to the project:

1. [Setup and usage](./setup_and_usage.md)
2. [Architecture](./architecture.md)
3. [Components](./components.md)
4. [Calculations](./calculations.md)

## Which Doc Should You Read?

### If you are a user

Read [Setup and usage](./setup_and_usage.md). It covers:

- installation
- running the Flask app
- using the daily generator
- using the year-range generator
- using the PDF generator
- CLI examples
- common mistakes and practical notes

### If you are a developer

Start with [Architecture](./architecture.md), then read [Components](./components.md).

Those docs explain:

- request flow through each generator path
- service layer boundaries
- how the web app and CLI share computation logic
- where to add new features or export formats
- where rule logic lives
- where export and serialization logic lives

### If you want the formulas and rule behavior

Read [Calculations](./calculations.md).

That document explains:

- Julian Day setup and time model
- Sun and Moon longitude derivation via Swiss Ephemeris
- Tithi, Nakshatra, Yoga, Karana, and Vara formulas
- how transition end times are found via bisection
- how sunrise-bound daily labeling works in the current implementation
- how comparison snapshots differ from the primary label

### If you want visual debugging tools

Read [Visualizations](./visualizations.md).

That document explains how to use `visualize.py` to:

- plot planetary sidereal longitudes over time
- chart Tithi frequency distributions
- render Panchang element heatmaps
- diff two CSV outputs for QA
- dump a single day to the console for debugging

## Scope and Caution

The project currently documents itself as:

- a sunrise-based Panchang generator
- with comparison reference snapshots for rule inspection
- not a finalized Agamic Jain rules engine

That wording is intentional. It is accurate to the current implementation and helps avoid overstating the scope of the current rule model.

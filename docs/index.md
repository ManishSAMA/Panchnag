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

- request flow
- service boundaries
- how the web app and CLI reuse logic
- where to add new features
- where rule logic lives
- where export logic lives

### If you want the formulas and rule behavior

Read [Calculations](./calculations.md).

That document explains:

- Julian Day setup
- Sun and Moon longitude derivation
- Tithi, Nakshatra, Yoga, Karana, and Vara formulas
- how transition end times are found
- how sunrise-bound daily labeling works in the current implementation

## Scope and Caution

The project currently documents itself as:

- a sunrise-based Panchang generator
- with comparison reference snapshots for rule inspection
- not a finalized Agamic Jain rules engine

That wording is intentional. It is accurate to the current implementation and helps avoid overstating the scope of the current rule model.

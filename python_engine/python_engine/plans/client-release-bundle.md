# Client release bundle + Hindi PDF in the web app

## Goal

Hand a client one folder they can run on Windows with a plain Python install:
double-click `start.bat`, the web app opens, and every generator (daily
panchang, CSV/Excel/JSON range export, yearly PDF, Hindi calendar PDF,
festivals) is reachable from the UI.

## Decisions (agreed with the user, 2026-09-24)

| Question | Decision |
|---|---|
| Client interface | Existing Flask web app, one-click `start.bat` launcher |
| How the folder gets the code | Build script copies runtime files only; re-run after changes |
| Client Python | 3.12 / 3.13 (pyswisseph has prebuilt wheels there; 3.14 has none) |
| Client OS | Windows only |
| Output location | `Jain_Panchang/client_release/` + `client_release.zip`, gitignored |
| Hindi calendar PDF | Add it to the web app (it was CLI-only) |
| Hindi PDF inputs | Start year, start month (default March), months (default 13, 1–24). Location, ayanamsa from app state; calendar system defaults to Purnimanta; profile `all` |
| Edge unavailable | Download the `.html` instead, with a "Ctrl+P → Save as PDF" note |

## Increments

1. `generate_hindi_pdf_calendar` returns the path it actually wrote
   (`.pdf`, or `.html` when Edge is unavailable) — today it returns the PDF
   path even when no PDF exists.
2. `parse_hindi_pdf_request` in `request_parsing.py` — validates
   start_year (required), start_month 1–12, months 1–24, location, ayanamsa,
   calendar_system.
3. `generate_hindi_pdf_export` in `pdf_generation_service.py` — resolves the
   location + timezone offset, writes into a unique temp dir, reports the file
   name, path and format (`pdf` | `html`).
4. `POST /generate-hindi-pdf` in `app.py` — same token/download contract as
   `/generate-pdf-panchang`.
5. UI card under "Export Panchang Data" + JS handler; Playwright smoke test.
6. `scripts/build_client_bundle.py` — copies the runtime file set (app +
   import closure, `jain_observances/`, `templates/`, `static/`,
   `requirements.txt`) plus `client_files/` (`start.bat`, `run_client.py`,
   `README.txt`) into the target, then zips it. Tests build into `tmp_path`
   and assert the bundle is complete (it imports `app` in a subprocess) and
   excludes dev material (tests, logs, build output, `.spec`, venvs).
7. `.gitignore` + docs (`docs/setup_and_usage.md`).

## Out of scope

- Frozen .exe (PyInstaller) — the client installs Python.
- Mac/Linux launchers.

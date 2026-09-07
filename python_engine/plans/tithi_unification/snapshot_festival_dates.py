"""
snapshot_festival_dates.py -- Before/After date-diff sheet for the 6-ghati
tithi-unification refactor (see plans/tithi_unification/ for the design).

Usage:
    # 1. Run BEFORE any refactor code changes are made:
    .venv-linux/bin/python plans/tithi_unification/snapshot_festival_dates.py --mode before

    # 2. Make the refactor changes to panchang.py / festival_rules.py / etc.

    # 3. Run again AFTER the changes, against the same xlsx, to fill the
    #    "After" columns and light up the diff formulas:
    .venv-linux/bin/python plans/tithi_unification/snapshot_festival_dates.py --mode after

Output: plans/tithi_unification/festival_dates_2026.xlsx
    One row per festival occurrence, keyed by (profile, id, occurrence_no)
    where occurrence_no is that id's 1st/2nd/3rd/... occurrence in the year
    (recurring monthly parvas fire many times; Kalyanaks/Mahaparvs once).
    Columns: profile, id, name, category, jain_month, paksha, tithi,
    Before_Start, Before_End, After_Start, After_End, Days_Diff_Start,
    Days_Diff_End, Status (SAME / CHANGED / PENDING / COUNT_CHANGED).

This script only READS the engine (generate_jain_festivals) -- it makes no
production code changes. It is a manual-comparison aid, not a test.
"""
import argparse
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.utils import get_column_letter

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from jain_observances.festival_service import generate_jain_festivals  # noqa: E402

YEAR = 2026
LAT, LON = 19.0760, 72.8777  # Mumbai -- matches the sample coords in main.py
AYANAMSA = "Lahiri"
PROFILES = [
    "shwetambar_murtipujak_tapagachchha",
    "shwetambar_sthanakvasi",
    "shwetambar_terapanthi",
    "digambar",
]

OUT_PATH = Path(__file__).resolve().parent / f"festival_dates_{YEAR}.xlsx"

HEADERS = [
    "profile", "id", "occurrence_no", "name", "category", "jain_month", "paksha", "tithi",
    "Before_Start", "Before_End", "After_Start", "After_End",
    "Days_Diff_Start", "Days_Diff_End", "Status",
]


def _iso_to_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def collect_occurrences() -> list[dict]:
    """Run the (current, unmodified-at-call-time) engine for every profile and
    return one row per occurrence with a stable (profile, id, occurrence_no) key."""
    rows = []
    for profile in PROFILES:
        data = generate_jain_festivals(YEAR, LAT, LON, AYANAMSA, profile)
        festivals = data if isinstance(data, list) else data.get("festivals", data)
        by_id = defaultdict(list)
        for f in festivals:
            by_id[f.get("id", f.get("occurrence_id", f.get("name", "")))].append(f)
        for fid, occs in by_id.items():
            occs.sort(key=lambda o: (o["start_date"], o["end_date"]))
            for i, o in enumerate(occs, start=1):
                rows.append({
                    "profile": profile,
                    "id": fid,
                    "occurrence_no": i,
                    "name": o.get("name", ""),
                    "category": o.get("category", ""),
                    "jain_month": o.get("jain_month", ""),
                    "paksha": o.get("paksha", ""),
                    "tithi": o.get("tithi", ""),
                    "start_date": _iso_to_date(o["start_date"]),
                    "end_date": _iso_to_date(o["end_date"]),
                })
    return rows


def write_before(rows: list[dict]) -> None:
    if OUT_PATH.exists():
        print(f"Refusing to overwrite existing {OUT_PATH} in --mode before. "
              f"Delete it first if you really want to re-baseline.", file=sys.stderr)
        sys.exit(1)

    wb = Workbook()
    ws = wb.active
    ws.title = f"Festivals_{YEAR}"
    ws.append(HEADERS)

    date_cols = {"Before_Start", "Before_End"}
    for r, row in enumerate(sorted(rows, key=lambda r: (r["profile"], r["id"], r["occurrence_no"])), start=2):
        values = {
            "profile": row["profile"], "id": row["id"], "occurrence_no": row["occurrence_no"],
            "name": row["name"], "category": row["category"], "jain_month": row["jain_month"],
            "paksha": row["paksha"], "tithi": str(row["tithi"]),
            "Before_Start": row["start_date"], "Before_End": row["end_date"],
        }
        for h in HEADERS:
            c = ws.cell(row=r, column=HEADERS.index(h) + 1)
            if h in values:
                c.value = values[h]
                if h in date_cols:
                    c.number_format = "yyyy-mm-dd"
            elif h in ("After_Start", "After_End"):
                c.value = None
            elif h == "Days_Diff_Start":
                c.value = f'=IF(OR($K{r}="",$I{r}=""),"", $K{r}-$I{r})'
            elif h == "Days_Diff_End":
                c.value = f'=IF(OR($L{r}="",$J{r}=""),"", $L{r}-$J{r})'
            elif h == "Status":
                c.value = (
                    f'=IF(OR($K{r}="",$L{r}=""),"PENDING",'
                    f'IF(AND($I{r}=$K{r},$J{r}=$L{r}),"SAME","CHANGED"))'
                )

    for i, h in enumerate(HEADERS, start=1):
        ws.column_dimensions[get_column_letter(i)].width = max(12, len(h) + 2)

    ws.freeze_panes = "A2"
    wb.save(OUT_PATH)
    print(f"Wrote {len(rows)} baseline rows to {OUT_PATH}")
    print("Run again with --mode after once the refactor code changes are in place.")


def write_after(rows: list[dict]) -> None:
    if not OUT_PATH.exists():
        print(f"{OUT_PATH} does not exist -- run --mode before first.", file=sys.stderr)
        sys.exit(1)

    wb = load_workbook(OUT_PATH)
    ws = wb.active

    header_row = {c.value: c.column for c in ws[1]}
    key_to_after = {(r["profile"], r["id"], r["occurrence_no"]): r for r in rows}
    seen_keys = set()

    max_row = ws.max_row
    for r in range(2, max_row + 1):
        key = (
            ws.cell(row=r, column=header_row["profile"]).value,
            ws.cell(row=r, column=header_row["id"]).value,
            ws.cell(row=r, column=header_row["occurrence_no"]).value,
        )
        after = key_to_after.get(key)
        if after is None:
            # This (profile, id, occurrence_no) no longer exists after the
            # refactor -- e.g. a double-fire got fixed and occurrence #2
            # disappeared. Leave After_* blank; Status formula covers PENDING,
            # so overwrite it explicitly to make the count-change visible.
            ws.cell(row=r, column=header_row["Status"]).value = "MISSING_AFTER"
            continue
        seen_keys.add(key)
        c_start = ws.cell(row=r, column=header_row["After_Start"])
        c_end = ws.cell(row=r, column=header_row["After_End"])
        c_start.value = after["start_date"]
        c_end.value = after["end_date"]
        c_start.number_format = "yyyy-mm-dd"
        c_end.number_format = "yyyy-mm-dd"

    # Any occurrence that exists AFTER but had no BEFORE row at all (e.g. a
    # new occurrence appeared, count went up) -- append as new rows flagged.
    existing_keys = {
        (
            ws.cell(row=r, column=header_row["profile"]).value,
            ws.cell(row=r, column=header_row["id"]).value,
            ws.cell(row=r, column=header_row["occurrence_no"]).value,
        )
        for r in range(2, max_row + 1)
    }
    new_rows = [row for key, row in key_to_after.items() if key not in existing_keys]
    for row in sorted(new_rows, key=lambda r: (r["profile"], r["id"], r["occurrence_no"])):
        r = ws.max_row + 1
        ws.cell(row=r, column=header_row["profile"]).value = row["profile"]
        ws.cell(row=r, column=header_row["id"]).value = row["id"]
        ws.cell(row=r, column=header_row["occurrence_no"]).value = row["occurrence_no"]
        ws.cell(row=r, column=header_row["name"]).value = row["name"]
        ws.cell(row=r, column=header_row["category"]).value = row["category"]
        ws.cell(row=r, column=header_row["jain_month"]).value = row["jain_month"]
        ws.cell(row=r, column=header_row["paksha"]).value = row["paksha"]
        ws.cell(row=r, column=header_row["tithi"]).value = str(row["tithi"])
        c_start = ws.cell(row=r, column=header_row["After_Start"])
        c_end = ws.cell(row=r, column=header_row["After_End"])
        c_start.value = row["start_date"]
        c_end.value = row["end_date"]
        c_start.number_format = "yyyy-mm-dd"
        c_end.number_format = "yyyy-mm-dd"
        ws.cell(row=r, column=header_row["Status"]).value = "NEW_AFTER"

    wb.save(OUT_PATH)
    print(f"Filled After_* columns in {OUT_PATH} for {len(seen_keys)} matched occurrences "
          f"({len(new_rows)} new occurrences appended). Open in Excel/LibreOffice/Sheets "
          f"and sort/filter Status != SAME to review.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["before", "after"], required=True)
    args = parser.parse_args()

    rows = collect_occurrences()
    if args.mode == "before":
        write_before(rows)
    else:
        write_after(rows)


if __name__ == "__main__":
    main()

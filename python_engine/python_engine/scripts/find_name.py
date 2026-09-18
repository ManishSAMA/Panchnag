"""Locate where a festival's displayed name comes from, and what to edit.

A name shown in the PDF or the app can originate in three different places, and
which one wins is not obvious from the output. Run this before editing anything:

    python scripts/find_name.py anantnath
    python scripts/find_name.py "मोक्ष कल्याणक"
    python scripts/find_name.py "Pakhi Chaudas"

Precedence, highest first (see hindi_calendar_pdf.translate_fest):

  1. name_hindi, if it exists and contains Devanagari  -> printed verbatim
  2. otherwise title/name, run through TRANSLATIONS_MAP word by word
"""

from __future__ import annotations

import io
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from hindi_calendar_pdf import TRANSLATIONS_MAP, translate_fest  # noqa: E402
from jain_observances.registry import FESTIVAL_REGISTRY  # noqa: E402

RULES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                          "jain_observances", "festival_rules.py")
REGISTRY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                             "jain_observances", "registry.py")


def _has_devanagari(text: str) -> bool:
    return bool(text) and any("ऀ" <= ch <= "ॿ" for ch in text)


def _registry_line(entry_id: str) -> int | None:
    """Line number of an entry's `id` in registry.py, for a clickable pointer."""
    try:
        source = io.open(REGISTRY_PATH, encoding="utf-8").read().splitlines()
    except OSError:
        return None
    needle = f'"id": "{entry_id}"'
    for number, line in enumerate(source, start=1):
        if needle in line:
            return number
    return None


def search_registry(term: str) -> list[dict]:
    lowered = term.lower()
    return [
        entry for entry in FESTIVAL_REGISTRY
        if lowered in (entry.get("id") or "").lower()
        or lowered in (entry.get("name") or "").lower()
        or lowered in (entry.get("name_hindi") or "")
        or lowered in (entry.get("title") or "").lower()
    ]


def search_rule_classes(term: str) -> list[tuple[int, str, str]]:
    """Inline name/name_hindi literals inside festival_rules.py custom classes."""
    try:
        lines = io.open(RULES_PATH, encoding="utf-8").read().splitlines()
    except OSError:
        return []

    lowered = term.lower()
    hits: list[tuple[int, str, str]] = []
    current_class = "?"
    for number, line in enumerate(lines, start=1):
        class_match = re.match(r"class\s+(\w+)", line)
        if class_match:
            current_class = class_match.group(1)
        if re.search(r'"(name|name_hindi|title)":', line) and (
            lowered in line.lower() or term in line
        ):
            hits.append((number, current_class, line.strip()))
    return hits


def main(term: str) -> None:
    print(f'Searching for: "{term}"\n')

    entries = search_registry(term)
    if entries:
        print(f"── jain_observances/registry.py — {len(entries)} matching entr"
              f"{'y' if len(entries) == 1 else 'ies'} ──")
        for entry in entries[:12]:
            line = _registry_line(entry.get("id", ""))
            where = f"registry.py:{line}" if line else "registry.py"
            rendered = translate_fest(entry)
            stored = entry.get("name_hindi")
            print(f"\n  {where}")
            print(f"    id         : {entry.get('id')}")
            print(f"    name       : {entry.get('name')}")
            if _has_devanagari(stored or ""):
                print(f"    name_hindi : {stored}")
                print(f"    -> PRINTS  : {rendered}")
                print(f"    EDIT       : the name_hindi field at {where}")
            else:
                print(f"    name_hindi : (none — auto-translated)")
                print(f"    -> PRINTS  : {rendered}")
                print(f"    EDIT       : add a name_hindi field at {where}  [preferred]")
                print(f"                 or change TRANSLATIONS_MAP in hindi_calendar_pdf.py")
        if len(entries) > 12:
            print(f"\n  … and {len(entries) - 12} more")
        print()

    hits = search_rule_classes(term)
    if hits:
        print(f"── jain_observances/festival_rules.py — {len(hits)} inline literal(s) ──")
        print("   These festivals are built by custom rule classes, so their names are")
        print("   hardcoded in code rather than stored in the registry.\n")
        for number, class_name, text in hits[:12]:
            print(f"  festival_rules.py:{number}  ({class_name})")
            print(f"    {text[:110]}")
        if len(hits) > 12:
            print(f"\n  … and {len(hits) - 12} more")
        print()

    if not entries and not hits:
        print("No match in registry.py or festival_rules.py.\n")
        words = [eng for eng in TRANSLATIONS_MAP if term.lower() in eng.lower()]
        if words:
            print("But TRANSLATIONS_MAP in hindi_calendar_pdf.py has:")
            for word in words:
                print(f"    {word!r} -> {TRANSLATIONS_MAP[word]!r}")
            print("\n  EDIT: TRANSLATIONS_MAP in hindi_calendar_pdf.py")
        else:
            print("Try a shorter term, or the English name (e.g. 'anantnath').")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    main(" ".join(sys.argv[1:]))

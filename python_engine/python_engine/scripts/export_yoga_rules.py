"""Regenerate shared/yoga_rules.json and the Dart engine's yoga_rules.g.dart from yoga_rules.py.

    python scripts/export_yoga_rules.py

Run after editing the yoga rules; tests/test_yoga_rules_json.py fails until you do.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from yoga_rules_json import write_yoga_rules_dart, write_yoga_rules_json  # noqa: E402

if __name__ == "__main__":
    print(f"wrote {write_yoga_rules_json()}")
    print(f"wrote {write_yoga_rules_dart()}")

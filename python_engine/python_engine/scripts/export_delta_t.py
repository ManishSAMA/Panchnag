"""Regenerate mobile/packages/panchang_engine/lib/src/time/delta_t_table.g.dart.

    python scripts/export_delta_t.py

tests/test_delta_t_table.py fails until you do (e.g. after a pyswisseph upgrade).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from delta_t_table import write_dart_table  # noqa: E402

if __name__ == "__main__":
    print(f"wrote {write_dart_table()}")

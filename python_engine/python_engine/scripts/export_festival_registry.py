"""Regenerate shared/festival_registry.json from jain_observances/registry.py.

    python scripts/export_festival_registry.py

Run after editing the registry; tests/test_festival_registry_json.py fails until you do.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jain_observances.registry_json import write_registry_json  # noqa: E402

if __name__ == "__main__":
    print(f"wrote {write_registry_json()}")

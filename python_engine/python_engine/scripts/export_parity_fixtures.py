"""Export the Python engine's answers as parity fixtures for the Dart engine.

    python scripts/export_parity_fixtures.py --set core --workers 14
    python scripts/export_parity_fixtures.py --set full --workers 14
    python scripts/export_parity_fixtures.py --set custom --name Shikharji --lat 23.96 --lon 86.13

Design: plans/mobile-phase1-fixtures.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from parity_fixtures import main  # noqa: E402

if __name__ == "__main__":
    main(sys.argv[1:])

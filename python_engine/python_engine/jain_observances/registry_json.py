"""The festival registry as JSON, shared with the Dart engine in mobile/.

registry.py remains where festivals are edited. shared/festival_registry.json
is generated from it (scripts/export_festival_registry.py) and a test fails
when the two drift apart.
"""

from __future__ import annotations

import json
from pathlib import Path

from jain_observances.registry import FESTIVAL_REGISTRY

# Bump when the document's shape changes, so the Dart side can refuse a stale file.
SCHEMA_VERSION = 1

REGISTRY_JSON_PATH = Path(__file__).resolve().parents[3] / "shared" / "festival_registry.json"


def registry_document() -> dict:
    return {"schema_version": SCHEMA_VERSION, "festivals": FESTIVAL_REGISTRY}


def write_registry_json(path: Path = REGISTRY_JSON_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Indented and unescaped: the file is committed, so diffs and Hindi names stay readable.
    text = json.dumps(registry_document(), indent=2, ensure_ascii=False, sort_keys=True)
    path.write_text(text + "\n", encoding="utf-8", newline="\n")
    return path

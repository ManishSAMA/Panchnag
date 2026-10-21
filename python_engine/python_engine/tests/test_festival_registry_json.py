"""The festival registry, shared with the Dart engine as one JSON file.

registry.py stays the place festivals are edited; shared/festival_registry.json
is generated from it so the mobile app reads the same definitions.
Design: plans/mobile-phase1-fixtures.md.
"""

from __future__ import annotations

import json

from jain_observances.registry import FESTIVAL_REGISTRY
from jain_observances.registry_json import (
    REGISTRY_JSON_PATH,
    SCHEMA_VERSION,
    registry_document,
    write_registry_json,
)


def test_document_holds_every_festival_in_registry_order():
    document = registry_document()

    assert document["schema_version"] == SCHEMA_VERSION
    assert document["festivals"] == FESTIVAL_REGISTRY


def test_written_file_reads_back_as_the_document(tmp_path):
    path = write_registry_json(tmp_path / "festival_registry.json")

    assert json.loads(path.read_text(encoding="utf-8")) == registry_document()


def test_hindi_names_stay_readable_in_the_file(tmp_path):
    text = write_registry_json(tmp_path / "festival_registry.json").read_text(encoding="utf-8")
    a_hindi_name = next(f["name_hindi"] for f in FESTIVAL_REGISTRY if f.get("name_hindi"))

    assert a_hindi_name in text


def test_rewriting_is_byte_identical(tmp_path):
    first = write_registry_json(tmp_path / "a.json").read_bytes()
    second = write_registry_json(tmp_path / "b.json").read_bytes()

    assert first == second


def test_shared_file_is_up_to_date_with_registry_py():
    committed = json.loads(REGISTRY_JSON_PATH.read_text(encoding="utf-8"))

    assert committed == registry_document(), (
        "shared/festival_registry.json is stale: run "
        "`python scripts/export_festival_registry.py` and commit the result."
    )

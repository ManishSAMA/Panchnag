"""Client release bundle: a folder a client runs with a plain Python install.

The bundle is generated, not hand-maintained, so these tests pin what makes it
usable: every module the web app imports travels with it (checked by resolving
each import from inside the bundle, with this repo off the path), and nothing
from the development tree -- tests, logs, build output, virtualenvs -- leaks in.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ENGINE_DIR = Path(__file__).resolve().parents[1]


def _load_builder():
    spec = importlib.util.spec_from_file_location(
        "build_client_bundle", ENGINE_DIR / "scripts" / "build_client_bundle.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = _load_builder()


@pytest.fixture(scope="module")
def bundle(tmp_path_factory) -> tuple[Path, Path]:
    target = tmp_path_factory.mktemp("release") / "client_release"
    zip_path = builder.build_client_bundle(target_dir=target)
    return target, zip_path


def _relative_files(root: Path) -> set[str]:
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}


def test_client_sees_only_the_launcher_readme_and_app_folder(bundle):
    target, _ = bundle

    assert sorted(p.name for p in target.iterdir()) == ["README.txt", "panchang_app", "start.bat"]


def test_bundle_carries_the_web_app_and_every_generator(bundle):
    target, _ = bundle
    app_dir = target / "panchang_app"

    for required in (
        "run_client.py", "app.py", "requirements.txt",
        "templates/index.html", "static/app.js", "static/app.css",
        "export.py", "export_pdf.py", "hindi_calendar_pdf.py",
        "jain_observances/festival_service.py", "jain_observances/vrats/rohini.py",
        "wheels/pyswisseph-2.10.3.2-cp314-cp314-win_amd64.whl",
    ):
        assert (app_dir / required).is_file(), required


def test_start_bat_supports_python_314_and_local_wheels(bundle):
    target, _ = bundle
    start_bat = (target / "start.bat").read_text(encoding="utf-8")

    assert "-3.14" in start_bat
    assert "--find-links wheels" in start_bat


def test_start_bat_dynamically_discovers_python(bundle):
    target, _ = bundle
    start_bat = (target / "start.bat").read_text(encoding="utf-8")

    assert "%LOCALAPPDATA%\\Programs\\Python" in start_bat
    assert "%ProgramFiles%\\Python" in start_bat
    assert "HKCU\\Software\\Python\\PythonCore" in start_bat
    assert "HKLM\\Software\\Python\\PythonCore" in start_bat
    assert "CUSTOM_PY" in start_bat
    assert "C:\\Users\\Als" in start_bat
    assert "C:\\Users\\manis" not in start_bat


def test_bundle_leaves_development_material_behind(bundle):
    target, _ = bundle
    files = _relative_files(target)

    leaked = {
        f for f in files
        if set(f.split("/")) & {"tests", "tests_ui", "docs", "plans", "scripts", "logs",
                                "output", "build", "dist", "pyswisseph", "venv",
                                ".venv", ".venv-win", "__pycache__"}
        or f.endswith((".spec", ".log", ".bsp", ".csv", ".xlsx", ".pdf"))
        or f.endswith("conftest.py")
    }
    assert leaked == set()


def test_every_import_in_the_bundle_resolves_without_the_source_tree(bundle):
    target, _ = bundle
    app_dir = target / "panchang_app"
    checker = (
        "import ast, importlib.util, pathlib, sys\n"
        "sys.path[0] = str(pathlib.Path.cwd())\n"
        "missing = set()\n"
        "for path in pathlib.Path.cwd().rglob('*.py'):\n"
        "    for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):\n"
        "        names = [a.name for a in node.names] if isinstance(node, ast.Import) else \\\n"
        "                [node.module] if isinstance(node, ast.ImportFrom) and node.level == 0 else []\n"
        "        missing |= {n for n in names if importlib.util.find_spec(n.split('.')[0]) is None}\n"
        "print(sorted(missing))\n"
    )
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}

    result = subprocess.run(
        [sys.executable, "-c", checker], cwd=app_dir, env=env,
        capture_output=True, text=True, check=True,
    )

    assert result.stdout.strip() == "[]"


def test_zip_holds_exactly_the_bundle_folder(bundle):
    target, zip_path = bundle

    with zipfile.ZipFile(zip_path) as archive:
        zipped = {n for n in archive.namelist() if not n.endswith("/")}

    assert zipped == {f"client_release/{f}" for f in _relative_files(target)}


def test_rebuild_refuses_to_wipe_a_folder_that_is_not_a_bundle(tmp_path):
    precious = tmp_path / "my_documents"
    precious.mkdir()
    (precious / "notes.txt").write_text("keep me")

    with pytest.raises(ValueError, match="not a client bundle"):
        builder.build_client_bundle(target_dir=precious)

    assert (precious / "notes.txt").read_text() == "keep me"


def test_rebuild_replaces_a_previous_bundle(tmp_path):
    target = tmp_path / "client_release"
    builder.build_client_bundle(target_dir=target)
    stale = target / "panchang_app" / "stale_module.py"
    stale.write_text("")

    builder.build_client_bundle(target_dir=target)

    assert not stale.exists()

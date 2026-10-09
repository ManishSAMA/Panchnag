"""Build the client release: a folder (and zip) that runs the web app on Windows.

    python scripts/build_client_bundle.py            # -> <repo>/client_release/
    python scripts/build_client_bundle.py --out DIR

Only what the app needs at runtime is copied. The Python modules are found by
following imports from the launcher, so a new module the app starts importing
is picked up without editing a list here. Re-run after every change; the
output is gitignored.
"""

from __future__ import annotations

import argparse
import ast
import shutil
import zipfile
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parents[1]
CLIENT_FILES_DIR = ENGINE_DIR / "client_files"
DEFAULT_TARGET = ENGINE_DIR.parents[1] / "client_release"

APP_SUBDIR = "panchang_app"
LAUNCHER = "run_client.py"
TOP_LEVEL_CLIENT_FILES = ("start.bat", "README.txt")
ASSET_DIRS = ("templates", "static")
ASSET_FILES = ("requirements.txt",)
BUNDLE_MARKER = "start.bat"


def _imported_top_level_names(source: Path) -> frozenset[str]:
    tree = ast.parse(source.read_text(encoding="utf-8"))
    return frozenset(
        name.split(".")[0]
        for node in ast.walk(tree)
        for name in (
            [alias.name for alias in node.names] if isinstance(node, ast.Import)
            else [node.module] if isinstance(node, ast.ImportFrom) and node.level == 0
            else []
        )
    )


def _local_source(name: str) -> Path | None:
    """The engine file or package a top-level import name refers to, if local."""
    module_file = ENGINE_DIR / f"{name}.py"
    if module_file.is_file():
        return module_file
    package_dir = ENGINE_DIR / name
    if (package_dir / "__init__.py").is_file():
        return package_dir
    return None


def _python_files(source: Path) -> tuple[Path, ...]:
    return (source,) if source.is_file() else tuple(
        p for p in source.rglob("*.py") if "__pycache__" not in p.parts
    )


def runtime_sources(entry_point: Path) -> frozenset[Path]:
    """Local modules and packages reachable from ``entry_point`` by import.

    Packages are taken whole: their relative imports and registries reach
    submodules that a top-level import scan cannot see.
    """
    found: set[Path] = set()
    pending = [entry_point]
    while pending:
        scanned = pending.pop()
        for name in _imported_top_level_names(scanned):
            source = _local_source(name)
            if source is None or source in found:
                continue
            found.add(source)
            pending.extend(_python_files(source))
    return frozenset(found)


def _ignore_dev_files(_directory: str, names: list[str]) -> set[str]:
    return {n for n in names if n == "__pycache__" or n.endswith((".pyc", ".pyo"))}


def _copy_with_crlf(source: Path, destination: Path) -> None:
    # cmd.exe misreads labels in batch files saved with bare LF line endings.
    text = source.read_text(encoding="utf-8").replace("\r\n", "\n")
    destination.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))


def _clean_directory(directory: Path) -> None:
    for child in directory.iterdir():
        if child.is_file() or child.is_symlink():
            child.unlink()
        elif child.is_dir():
            try:
                shutil.rmtree(child)
            except OSError:
                _clean_directory(child)


def _prepare_target(target_dir: Path) -> None:
    if target_dir.exists() and any(target_dir.iterdir()):
        is_bundle = (target_dir / BUNDLE_MARKER).is_file() or (target_dir / APP_SUBDIR).is_dir()
        if not is_bundle:
            raise ValueError(
                f"{target_dir} is not empty and is not a client bundle; refusing to replace it."
            )
        try:
            shutil.rmtree(target_dir)
        except OSError:
            _clean_directory(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)


def _zip_folder(folder: Path) -> Path:
    zip_path = folder.with_suffix(".zip")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(p for p in folder.rglob("*") if p.is_file()):
            archive.write(path, arcname=Path(folder.name) / path.relative_to(folder))
    return zip_path


def build_client_bundle(*, target_dir: Path = DEFAULT_TARGET) -> Path:
    """Write the bundle folder and its zip; returns the zip path."""
    _prepare_target(target_dir)
    app_dir = target_dir / APP_SUBDIR
    app_dir.mkdir(parents=True, exist_ok=True)

    launcher = CLIENT_FILES_DIR / LAUNCHER
    shutil.copy2(launcher, app_dir / LAUNCHER)
    for source in sorted(runtime_sources(launcher)):
        if source.is_dir():
            shutil.copytree(source, app_dir / source.name, ignore=_ignore_dev_files, dirs_exist_ok=True)
        else:
            shutil.copy2(source, app_dir / source.name)
    for asset_dir in ASSET_DIRS:
        shutil.copytree(ENGINE_DIR / asset_dir, app_dir / asset_dir, ignore=_ignore_dev_files, dirs_exist_ok=True)
    for asset_file in ASSET_FILES:
        shutil.copy2(ENGINE_DIR / asset_file, app_dir / asset_file)
    wheels_src = CLIENT_FILES_DIR / "wheels"
    if wheels_src.is_dir():
        shutil.copytree(wheels_src, app_dir / "wheels", dirs_exist_ok=True)

    for name in TOP_LEVEL_CLIENT_FILES:
        source = CLIENT_FILES_DIR / name
        if name.endswith(".bat"):
            _copy_with_crlf(source, target_dir / name)
        else:
            shutil.copy2(source, target_dir / name)

    return _zip_folder(target_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_TARGET,
                        help="bundle folder to (re)create; the zip is written beside it")
    args = parser.parse_args()

    zip_path = build_client_bundle(target_dir=args.out.resolve())
    print(f"Client bundle: {args.out.resolve()}")
    print(f"Zip to share:  {zip_path}")

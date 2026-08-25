"""Retira artefactos locales conocidos sin tocar datos ni entornos virtuales."""

import argparse
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRECTORIES = ("app", "tests", "scripts")
ROOT_CACHE_DIRECTORIES = ("__pycache__", ".pytest_cache", ".ruff_cache")
OBSOLETE_RELATIVE_FILES = (
    Path("app/static/img/logo.svg"),
    Path("app/static/css/components/_sidebar.css"),
)


def cleanup_project(project_root: Path = PROJECT_ROOT) -> list[Path]:
    """Elimina únicamente cachés de código y recursos declarados obsoletos."""
    root = Path(project_root).resolve()
    removed: list[Path] = []

    for relative_path in OBSOLETE_RELATIVE_FILES:
        target = root / relative_path
        if target.is_file() or target.is_symlink():
            target.unlink()
            removed.append(target)

    for cache_name in ROOT_CACHE_DIRECTORIES:
        target = root / cache_name
        if target.is_dir():
            shutil.rmtree(target)
            removed.append(target)

    for directory_name in SOURCE_DIRECTORIES:
        source_directory = root / directory_name
        if not source_directory.is_dir():
            continue
        cache_directories = sorted(
            source_directory.rglob("__pycache__"), key=lambda path: len(path.parts), reverse=True
        )
        for cache_directory in cache_directories:
            if cache_directory.is_dir():
                shutil.rmtree(cache_directory)
                removed.append(cache_directory)
        for pattern in ("*.pyc", "*.pyo"):
            for compiled_file in source_directory.rglob(pattern):
                if compiled_file.is_file():
                    compiled_file.unlink()
                    removed.append(compiled_file)

    return removed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quiet", action="store_true", help="No mostrar cada ruta eliminada.")
    args = parser.parse_args()

    removed = cleanup_project()
    if not args.quiet:
        if removed:
            for path in removed:
                print(f"Eliminado: {path.relative_to(PROJECT_ROOT)}")
        else:
            print("No se encontraron artefactos obsoletos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

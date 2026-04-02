"""Compatibility entry point delegating to the canonical Airflow wrapper."""

from pathlib import Path
import runpy
import sys


ROOT_WRAPPER = (
    Path(__file__).resolve().parents[4]
    / "airflow"
    / "scripts"
    / "airflow_windows.py"
)


def main() -> None:
    if not ROOT_WRAPPER.exists():
        raise FileNotFoundError(
            f"Canonical Airflow wrapper not found: {ROOT_WRAPPER}"
        )

    sys.path.insert(0, str(ROOT_WRAPPER.parent))
    runpy.run_path(str(ROOT_WRAPPER), run_name="__main__")


if __name__ == "__main__":
    main()

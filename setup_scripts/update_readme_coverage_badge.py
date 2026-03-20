#!/usr/bin/env python3

import argparse
import re
import subprocess
import sys
from pathlib import Path


def _choose_badge_color(pct: float) -> str:
    if pct >= 99:
        return "green"
    if pct >= 90:
        return "yellow"
    return "red"


def _get_total_coverage_percent(coverage_data_file: Path) -> float:
    """
    Uses `coverage report` (coverage.py) to compute TOTAL coverage percent.
    """
    try:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "coverage",
                "report",
                "--data-file",
                str(coverage_data_file),
                "--precision",
                "0",
            ],
            check=True,
            text=True,
            capture_output=True,
        )
    except Exception as e:  # pragma: no cover - CI environment variance
        raise RuntimeError(
            f"Failed to compute coverage from {coverage_data_file}: {e}"
        ) from e

    # Example line (format varies by coverage versions):
    # TOTAL 195 0 100%
    match = re.search(r"^TOTAL\s+\d+\s+\d+\s+(\d+(?:\.\d+)?)%$", completed.stdout, re.M)
    if not match:
        raise RuntimeError("Could not parse TOTAL coverage percentage")
    return float(match.group(1))


def _update_readme_badge(readme_text: str, pct: float) -> tuple[str, bool]:
    badge_re = re.compile(
        r"tests-pytest-(\d+(?:\.\d+)?)%25-coverage-(green|yellow|red)"
    )

    pct_int = int(round(pct))
    color = _choose_badge_color(pct)
    replacement = f"tests-pytest-{pct_int}%25-coverage-{color}"

    new_text, count = badge_re.subn(replacement, readme_text, count=1)
    return new_text, count == 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--readme-path",
        type=Path,
        default=Path("README.md"),
    )
    parser.add_argument(
        "--coverage-data-file",
        type=Path,
        default=Path(".coverage"),
    )
    args = parser.parse_args()

    if not args.readme_path.exists():
        raise SystemExit(f"README not found: {args.readme_path}")
    if not args.coverage_data_file.exists():
        raise SystemExit(f"Coverage data not found: {args.coverage_data_file}")

    coverage_pct = _get_total_coverage_percent(args.coverage_data_file)

    readme_text = args.readme_path.read_text(encoding="utf-8")
    updated_text, ok = _update_readme_badge(readme_text, coverage_pct)
    if not ok:
        raise SystemExit(
            "Did not find the expected coverage badge pattern in README.md"
        )

    if updated_text != readme_text:
        args.readme_path.write_text(updated_text, encoding="utf-8")

    print(f"Coverage badge update: total={coverage_pct:.0f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


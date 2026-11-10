"""Build the sequencing priority list from existing results (no ENA / WCVP re-download).

Usage (from repository root):
    python pipeline/phase_priority.py
    python pipeline/phase_priority.py --config pipeline/config.yaml
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from barcode_atlas.config import load_config  # noqa: E402
from barcode_atlas.priority import run_priority  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(Path(__file__).parent / "config.yaml"))
    args = parser.parse_args()
    summary = run_priority(load_config(args.config))
    print(
        f"gaps={summary['n_gaps']} top_endemic_in_100={summary['top_endemic_in_100']} "
        f"top5={summary['top_species']}",
        flush=True,
    )


if __name__ == "__main__":
    main()

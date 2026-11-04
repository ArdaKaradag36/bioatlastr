"""Phase 1 - build data/species.csv (default: WCVP, Turkish accepted species).

Usage (from the repository root):
    python pipeline/phase1_species.py --config pipeline/config.test.yaml
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from barcode_atlas.config import load_config  # noqa: E402
from barcode_atlas.sources import run_phase1  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(Path(__file__).parent / "config.yaml"))
    args = parser.parse_args()
    run_phase1(load_config(args.config))


if __name__ == "__main__":
    main()

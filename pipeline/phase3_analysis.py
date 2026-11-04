"""Phase 3 - alignment, trees, coverage, discrimination, JSON/CSV export.

Usage (from the repository root):
    python pipeline/phase3_analysis.py --config pipeline/config.test.yaml
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from barcode_atlas.analysis import analyse  # noqa: E402
from barcode_atlas.config import load_config  # noqa: E402
from barcode_atlas.export import export_all  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(Path(__file__).parent / "config.yaml"))
    args = parser.parse_args()
    cfg = load_config(args.config)
    export_all(cfg, analyse(cfg))


if __name__ == "__main__":
    main()

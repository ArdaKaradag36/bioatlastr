"""Fixed project paths. Everything is relative to the repository root."""

import os
from pathlib import Path

# pipeline/barcode_atlas/paths.py -> repository root is two levels above "barcode_atlas"
ROOT = Path(__file__).resolve().parents[2]

# Optional isolated run: BARCODE_RUN_DIR=runs/full writes data/, results/, web_data/ and docs/ under that
# directory, so the published site data (web/public/data) and pilot results stay untouched until the run is
# validated and copied by scripts/publish_full.sh. Downloads and the ENA cache are always shared.
_run = os.environ.get("BARCODE_RUN_DIR")
RUN = (ROOT / _run) if _run else ROOT
SHARED_DATA = ROOT / "data"
DATA = RUN / "data"
CACHE = SHARED_DATA / "cache"
SEQUENCES_DIR = DATA / "sequences"
ALIGNMENTS_DIR = DATA / "alignments"
SPECIES_CSV = DATA / "species.csv"
SPECIES_META_JSON = DATA / "species_meta.json"
SYNONYMS_CSV = DATA / "synonyms.csv"
RAW = SHARED_DATA / "raw"
SEQUENCE_TABLE_CSV = DATA / "sequence_table.csv"
DROPPED_CSV = DATA / "dropped_sequences.csv"

RESULTS = RUN / "results"
WEB_DATA = (RUN / "web_data") if _run else (ROOT / "web" / "public" / "data")
DOCS = RUN / "docs"

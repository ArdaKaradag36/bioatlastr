"""Load and validate config.yaml."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

PLACEHOLDER_EMAIL = "your.email@example.com"


class ConfigError(Exception):
    pass


def _merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in over.items():
        out[k] = _merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def _read_yaml(path: Path) -> dict[str, Any]:
    """YAML file; `base: other.yaml` inherits everything from another config in the same folder."""
    with open(path, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh) or {}
    base = cfg.pop("base", None)
    return _merge(_read_yaml(path.parent / base), cfg) if base else cfg


def load_config(path: str | Path) -> dict[str, Any]:
    """Read the YAML file, apply env overrides and check required values."""
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")
    cfg = _read_yaml(path)

    if "markers" not in cfg:
        raise ConfigError(f"Missing 'markers' in {path}")
    # Sources: the default run touches neither NCBI nor GBIF.
    cfg.setdefault("species_source", "wcvp_turkey")   # wcvp_turkey | csv | gbif
    cfg.setdefault("sequence_source", "ena")          # ena | ncbi
    if cfg["species_source"] not in ("wcvp_turkey", "csv", "gbif"):
        raise ConfigError("species_source must be wcvp_turkey | csv | gbif")
    if cfg["sequence_source"] not in ("ena", "ncbi"):
        raise ConfigError("sequence_source must be ena | ncbi")
    # families_whitelist (new name) / families (old name); empty = all families
    cfg["families_whitelist"] = list(cfg.get("families_whitelist") or cfg.get("families") or [])
    cfg["families"] = cfg["families_whitelist"]
    if cfg["species_source"] == "gbif" and not cfg["families"]:
        raise ConfigError("species_source gbif needs a non-empty families_whitelist")
    cfg.setdefault("max_species", None)
    cfg.setdefault("max_per_species_marker", cfg.get("max_sequences_per_species_marker", 10))
    cfg["max_sequences_per_species_marker"] = cfg["max_per_species_marker"]
    cfg.setdefault("ncbi", {})
    cfg.setdefault("wcvp", {})
    cfg["wcvp"].setdefault("url", "http://sftp.kew.org/pub/data-repositories/WCVP/wcvp.zip")
    cfg["wcvp"].setdefault("area_code", "TUR")
    cfg.setdefault("ena", {})
    for k, v in {"max_requests_per_second": 10, "fasta_batch": 100, "page_size": 5000,
                 "max_candidates_per_species_marker": 30, "max_identical_copies": 2,
                 "max_retries": 8, "workers": 4}.items():
        cfg["ena"].setdefault(k, v)

    # Optional defaults so older/shorter configs still work.
    cfg.setdefault("max_species_per_family", None)
    cfg.setdefault("min_occurrences_in_turkey", 1)
    cfg.setdefault("max_sequences_per_species_marker", 5)
    cfg.setdefault("allow_name_mismatch", False)
    cfg.setdefault("gbif", {})
    cfg["gbif"].setdefault("country", "TR")
    cfg["gbif"].setdefault("min_interval", 0.1)
    cfg["gbif"].setdefault("max_retries", 10)
    cfg.setdefault("analysis", {})
    for k, v in {
        "min_overlap": 200,
        "n_nearest": 5,
        "mafft_path": None,
        "mafft_threads": -1,
    }.items():
        cfg["analysis"].setdefault(k, v)
    cfg["ncbi"].setdefault("batch_size", 100)
    cfg["ncbi"].setdefault("search_retmax", 50)
    cfg["analysis"].setdefault("min_group_sequences", 3)
    cfg["analysis"].setdefault("max_group_sequences", 400)
    cfg["analysis"].setdefault("mafft_timeout_s", 600)

    # Environment variables win over the file (keeps secrets out of git).
    cfg["ncbi"]["email"] = os.environ.get("NCBI_EMAIL") or cfg["ncbi"].get("email")
    cfg["ncbi"]["api_key"] = os.environ.get("NCBI_API_KEY") or cfg["ncbi"].get("api_key")

    for name, m in cfg["markers"].items():
        for k in ("min_length", "max_length", "max_n_fraction"):
            if k not in m:
                raise ConfigError(f"Marker '{name}' is missing '{k}'")
        if cfg["sequence_source"] == "ncbi" and "query" not in m:
            raise ConfigError(f"Marker '{name}' needs 'query' for sequence_source: ncbi")
        m.setdefault("ena_terms", [])
    return cfg


def warn_if_placeholder_email(cfg: dict[str, Any]) -> None:
    """NCBI asks for a real email so they can contact you if your script misbehaves."""
    email = cfg["ncbi"].get("email")
    if not email or email == PLACEHOLDER_EMAIL:
        print(
            "WARNING: ncbi.email is still the placeholder. Please put your own email in "
            "the config file (or set NCBI_EMAIL) - NCBI requires it."
        )

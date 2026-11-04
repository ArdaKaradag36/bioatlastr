"""Choose the data sources from the config. The default run never touches NCBI or GBIF."""

from __future__ import annotations

from typing import Any

from .paths import SPECIES_CSV


def guard_full_run(cfg: dict[str, Any]) -> None:
    """The unrestricted full run must be confirmed once: create the file data/.confirm_full_run."""
    from .paths import SHARED_DATA
    if not cfg.get("families_whitelist") and not cfg.get("max_species") and not (SHARED_DATA / ".confirm_full_run").exists():
        raise SystemExit("FULL run (no families_whitelist / max_species) not confirmed yet. "
                         "Create the file data/.confirm_full_run to start it.")


def run_phase1(cfg: dict[str, Any]) -> None:
    guard_full_run(cfg)
    src = cfg["species_source"]
    if src == "wcvp_turkey":
        from .wcvp import run_phase1_wcvp
        run_phase1_wcvp(cfg)
    elif src == "gbif":  # optional, disabled by default
        from .gbif import run_phase1 as run_gbif
        run_gbif(cfg)
    elif src == "csv":
        if not SPECIES_CSV.exists():
            raise SystemExit(f"species_source: csv needs {SPECIES_CSV} (columns: species, genus, family, ...)")
        print(f"[phase 1] using existing {SPECIES_CSV}")


def run_phase2(cfg: dict[str, Any]) -> None:
    guard_full_run(cfg)
    if cfg["sequence_source"] == "ena":
        from .ena import run_phase2_ena
        run_phase2_ena(cfg)
    else:  # optional, disabled by default
        from .config import warn_if_placeholder_email
        from .ncbi import run_phase2 as run_ncbi
        warn_if_placeholder_email(cfg)
        run_ncbi(cfg)

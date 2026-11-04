"""Turkish-name helpers (pure functions, unit-tested)."""
import re, unicodedata

TR_ASCII = str.maketrans({"ı": "i", "ş": "s", "ğ": "g", "ü": "u", "ö": "o", "ç": "c", "â": "a", "î": "i", "û": "u"})

def clean(name: str) -> str:
    """NFC, collapse whitespace, trim surrounding punctuation; original capitalisation kept."""
    s = unicodedata.normalize("NFC", name or "")
    s = re.sub(r"\s+", " ", s).strip().strip(" ,;.:-–—\"'“”‘’")
    return s

def tr_lower(s: str) -> str:
    """Turkish-aware lower-casing: İ->i, I->ı (not i)."""
    return unicodedata.normalize("NFC", s.replace("İ", "i").replace("I", "ı").lower())

def fold_key(s: str) -> str:
    """Case-insensitive (Turkish-aware) key used to remove duplicates."""
    return tr_lower(clean(s))

def ascii_key(s: str) -> str:
    """Diacritic-insensitive key: 'Kızılçam' == 'kizilcam' == 'KIZILÇAM'."""
    return fold_key(s).translate(TR_ASCII)

def has_tr_diacritics(s: str) -> bool:
    return any(c in s.lower() for c in "ışğüöçâîû") or "İ" in s

def is_latin_like(name: str, latin: str, latin_genera: set[str]) -> bool:
    """True when the 'Turkish name' is just the Latin name (or another Latin binomial / genus-species string)."""
    k = ascii_key(name)
    if k == ascii_key(latin):
        return True
    parts = clean(name).split(" ")
    if len(parts) >= 2 and parts[0] in latin_genera and re.fullmatch(r"[a-z][a-z-]+\.?", parts[1]):
        return True
    return False

def bad_title(name: str) -> bool:
    """Wikipedia titles that are not names (disambiguation, lists, years...)."""
    return bool(re.search(r"[()\[\]:/0-9]|\bListesi\b|\bkategori", name)) or len(name) > 60 or not name

def merge_variants(names: list[str]) -> list[str]:
    """Remove case-insensitive (Turkish-aware) duplicates; when only the diacritics differ ('Sacli Mese' vs
    'Saçlı Meşe') keep the variant with Turkish letters. Order of first appearance is kept."""
    by_ascii: dict[str, str] = {}
    order: list[str] = []
    for n in names:
        n = clean(n)
        if not n:
            continue
        k = ascii_key(n)
        if k not in by_ascii:
            by_ascii[k] = n; order.append(k)
        else:
            cur = by_ascii[k]
            if fold_key(cur) != fold_key(n) and has_tr_diacritics(n) and not has_tr_diacritics(cur):
                by_ascii[k] = n
    return [by_ascii[k] for k in order]

def flag_ambiguous(assign: dict[str, set[str]]) -> dict[str, bool]:
    """assign: name_key -> set of accepted Latin names. Ambiguous when the same name belongs to >1 taxa."""
    return {k: len(v) > 1 for k, v in assign.items()}

def resolve_name(name: str, rank: str, species: set[str], syn: dict[str, str], genera: set[str], families: set[str]):
    """Map a (possibly synonym) Latin name to the accepted taxon: (accepted, 'accepted'|'synonym') or (None, None)."""
    if rank == "species":
        if name in species:
            return name, "accepted"
        if name in syn:
            return syn[name], "synonym"
    elif rank == "genus" and name in genera:
        return name, "accepted"
    elif rank == "family" and name in families:
        return name, "accepted"
    return None, None

# ---------------------------------------------------------------- source quality / licence classes
# tier A = reliable curated source, B = usable, community / restricted, C = excluded
# license_class: "open" (free reuse with attribution) | "non-commercial"
SOURCES = {
    "wikidata":    ("Wikidata", "A", "open", "CC0 1.0", "https://www.wikidata.org/wiki/Wikidata:Licensing", ""),
    "trwiki":      ("Vikipedi (tr)", "A", "open", "CC BY-SA 4.0", "https://tr.wikipedia.org/", ""),
    "gbif:Catalogue of Life": ("GBIF · Catalogue of Life", "A", "open", "CC BY 4.0 (dataset licence on GBIF)", "https://www.catalogueoflife.org/", ""),
    "gbif:Cichorieae Systematics Portal": ("GBIF · Cichorieae Systematics Portal", "A", "open", "CC BY 4.0 (stated on the portal and as the GBIF dataset licence)", "http://cichorieae.e-taxonomy.net/portal/", ""),
    "inaturalist": ("iNaturalist", "B", "non-commercial", "CC BY-NC (user-contributed content, iNaturalist Terms of Use)", "https://www.inaturalist.org/pages/terms", ""),
    "gbif:IUCN Red List": ("GBIF · IUCN Red List", "B", "non-commercial", "IUCN Red List terms of use (non-commercial); GBIF lists the dataset as CC BY 4.0, treated conservatively as non-commercial", "https://www.iucnredlist.org/terms/terms-of-use", ""),
}
EXCLUDED_REASONS = {
    "GRIN": "excluded: CC0 is stated only in the GBIF registry; GRIN's own pages state no data licence (could not be verified)",
    "Divriği": "tier C: environmental-impact-assessment dataset of a railway project, not a plant-name source; licence unclear",
    "World Register of Marine Species": "tier C: marine species register (WoRMS); terrestrial plant names are incidental / unverified",
    "WRiMS": "tier C: register of introduced marine species; terrestrial plant names are incidental / unverified",
    "DAISIE": "tier C: inventory of alien invasive species in Europe; names not curated for Turkish",
}

def source_info(src_family: str):
    """(label, tier, license_class, license_text, url, excluded_reason) for a src_family; unknown GBIF datasets are tier C."""
    if src_family in SOURCES:
        return SOURCES[src_family]
    for k, why in EXCLUDED_REASONS.items():
        if k in src_family:
            return (src_family.replace("gbif:", "GBIF · "), "C", "unknown", "see GBIF dataset", "https://www.gbif.org/", why)
    return (src_family, "C", "unknown", "unknown", "", "tier C: dataset not reviewed (not in the tier A/B list)")

def include_non_commercial(config_path: str | None = None) -> bool:
    """names.include_non_commercial in pipeline/config.yaml (default false = open licences only); env NAMES_INCLUDE_NON_COMMERCIAL=0/1 overrides."""
    import os
    from pathlib import Path
    env = os.environ.get("NAMES_INCLUDE_NON_COMMERCIAL")
    if env is not None:
        return env.strip().lower() in ("1", "true", "yes")
    import yaml
    p = Path(config_path) if config_path else Path(__file__).resolve().parents[1] / "pipeline" / "config.yaml"
    return bool(((yaml.safe_load(p.read_text()) or {}).get("names") or {}).get("include_non_commercial", False))

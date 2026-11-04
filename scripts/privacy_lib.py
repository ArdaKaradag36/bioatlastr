"""Remove personal data (collector / submitter names in specimen vouchers and free-text descriptions) from published sequence records."""
import re

# GenBank/ENA descriptions that mention these words may contain names of collectors, isolates or people
RISKY = re.compile(r"\b(voucher|collector|collected|specimen|herbarium|note|leg|isolate|clone|strain|cultivar|accession|coll)\b", re.I)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")

def country_only(c: str) -> str:
    """'USA:California, Siskiyou Co.: @ 3 mi SW of Scott' -> 'USA' (drop locality text)."""
    return (c or "").split(":")[0].strip()

def safe_definition(defn: str, organism: str, marker: str) -> str:
    """Keep the description only if it has no voucher/collector/isolate wording; otherwise a generic one."""
    d = (defn or "").strip()
    if not d or RISKY.search(d) or EMAIL.search(d):
        return f"{organism or ''} {marker} sequence".strip() if (organism or marker) else ""
    return d

def sanitize_sequence(rec: dict, organism: str = "", marker: str = "") -> dict:
    """Return a copy of a sequence record without voucher, locality text, or risky free text."""
    out = dict(rec)
    if "voucher" in out: out["voucher"] = ""
    if "country" in out: out["country"] = country_only(out["country"])
    if "definition" in out: out["definition"] = safe_definition(out["definition"], organism or out.get("organism", ""), marker)
    if "source_title" in out: out["source_title"] = safe_definition(out["source_title"], organism or out.get("organism", ""), marker) if out["source_title"] else ""
    return out

// Formatting helpers and Turkish labels for codes produced by the pipeline.
import type { DiscriminationStatus } from "./types";

export const num = (n: number) => n.toLocaleString("tr-TR");

/** 0.4567 -> "%45,7" (Turkish style) ; null -> "—" */
export function pct(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined) return "—";
  return `%${(value * 100).toLocaleString("tr-TR", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })}`;
}

/** p-distance (0..1) shown as percent with up to 3 decimals. */
export function distancePct(d: number): string {
  return `%${(d * 100).toLocaleString("tr-TR", { minimumFractionDigits: 2, maximumFractionDigits: 3 })}`;
}

export const DISCRIMINATION: Record<
  DiscriminationStatus,
  { label: string; classes: string; hint: string }
> = {
  success: {
    label: "Ayırt edilebiliyor",
    classes: "bg-emerald-100 text-link",
    hint: "En yakın komşu dizi aynı türe ait.",
  },
  ambiguous: {
    label: "Belirsiz",
    classes: "bg-amber-100 text-amber-800",
    hint: "En yakın mesafe hem aynı türle hem başka bir türle paylaşılıyor.",
  },
  fail: {
    label: "Ayırt edilemiyor",
    classes: "bg-red-100 text-red-800",
    hint: "En yakın komşu dizi başka bir türe ait.",
  },
  single_sequence: {
    label: "Tek dizi (test edilemedi)",
    classes: "bg-stone-100 text-stone-700",
    hint: "Yöntem en az 2 dizisi olan türlerde uygulanabilir.",
  },
  not_evaluable: {
    label: "Değerlendirilemedi",
    classes: "bg-stone-100 text-stone-700",
    hint: "Aynı ailede karşılaştırılabilir başka tür/dizi yok.",
  },
  none: {
    label: "Veri yok",
    classes: "bg-stone-100 text-stone-500",
    hint: "Bu barkod bölgesi için filtreyi geçen dizi bulunamadı.",
  },
};

/** Turkish explanation of the reason codes in data/dropped_sequences.csv. */
export const DROP_REASONS: Record<string, string> = {
  ambiguous_sp: "Tür adı belirsiz (\"sp.\")",
  ambiguous_cf: "Tür adı belirsiz (\"cf.\")",
  ambiguous_aff: "Tür adı belirsiz (\"aff.\")",
  hybrid: "Melez",
  unverified: "GenBank'ta \"UNVERIFIED\" olarak işaretli",
  not_binomial: "Tür adı \"Cins tür\" biçiminde değil",
  no_organism: "Organizma adı yok",
  name_mismatch: "Kayıttaki ad ile kabul edilen ad farklı",
  unmatched_name: "Ad, Türkiye florası türleri (WCVP) arasında yok",
  ambiguous_synonym: "Ad, birden fazla türün eş adı (belirsiz)",
  marker_not_in_description: "Kayıt açıklamasında marker adı yok",
  missing_description: "Açıklama (tanım) alanı boş kayıt",
  wrong_region_or_genome: "Başka bölge (aralık bölgesi) veya genom kaydı",
  multi_marker_record: "Birden fazla marker içeren kayıt",
  too_long: "Maksimum uzunluktan uzun",
  near_duplicate: "Aynı dizinin fazladan kopyası",
  fasta_missing: "ENA FASTA döndürmedi",
  not_downloaded_candidate_cap: "Aday sınırı nedeniyle indirilmedi",
  too_short: "Minimum uzunluktan kısa",
  too_many_N: "Çok fazla N karakteri",
  invalid_characters: "Geçersiz karakter",
  empty_sequence: "Boş dizi",
  not_dna: "DNA değil (ör. mRNA/cDNA kaydı)",
  duplicate_accession: "Aynı erişim numarası tekrar",
  record_not_returned: "NCBI kaydı döndürmedi",
  no_summary: "NCBI özeti alınamadı",
  not_selected_cap: "Tür başına dizi sınırı nedeniyle seçilmedi",
};

export const ncbiUrl = (accession: string) =>
  `https://www.ncbi.nlm.nih.gov/nuccore/${encodeURIComponent(accession)}`;
export const enaUrl = (accession: string) =>
  `https://www.ebi.ac.uk/ena/browser/view/${encodeURIComponent(accession)}`;
export const powoUrl = (powoId: string) => `https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:${powoId}`;

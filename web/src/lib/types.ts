// Types of the JSON files produced by the Python pipeline (web/public/data).

export type DiscriminationStatus =
  | "success"
  | "ambiguous"
  | "fail"
  | "single_sequence"
  | "not_evaluable"
  | "none";

export interface MarkerConfig {
  min_length: number;
  max_length: number;
  max_n_fraction: number;
}

export interface SpeciesMeta {
  source: string;
  url: string;
  area_name: string;
  wcvp_file_date: string | null;
  downloaded: string;
  rules: string;
  species_in_file: number;
  endemic_in_file: number;
  synonyms_in_file: number;
  stats: Record<string, number>;
}

export interface SequenceMeta {
  source: string;
  retrieved: string;
  genera_queried: number;
  /** All WCVP genus strings (accepted + synonym-only) with no ENA taxon id. */
  genera_unresolved: string[];
  genera_unresolved_total?: number;
  /** Accepted WCVP genera among genera_unresolved. */
  accepted_genera_without_ena_taxon?: string[];
  /** Synonym-only genus names among genera_unresolved (not accepted genera of the flora). */
  synonym_only_genera_without_ena_taxon?: string[];
  records_kept: number;
}

export interface Meta {
  generated_at: string;
  pipeline_version: string;
  country: string;
  species_source: string;
  sequence_source: string;
  families: string[];
  max_species: number | null;
  species_meta: SpeciesMeta | null;
  sequence_meta: SequenceMeta | null;
  markers: Record<string, MarkerConfig>;
  max_sequences_per_species_marker: number;
  max_identical_copies: number;
  max_group_sequences: number;
  min_group_sequences: number;
  allow_name_mismatch: boolean;
  min_overlap: number;
  n_nearest: number;
  aligner: string;
  /** "MAFFT" or "fallback (preliminary)": shown next to every tree and statistic. */
  aligner_label: string;
}

/** A Turkish common name taken from an open source (never written by hand). */
export interface TurkishName {
  n: string; // the name
  a: number; // 1 = the same name is used for more than one taxon
  src: { l: string; u: string; t: string; c: string; lic: string }[]; // source label, link, tier (A/B), licence class (open / nc), licence text
}

export interface TaxonNames {
  genus: Record<string, TurkishName[]>;
  family: Record<string, TurkishName[]>;
  meta?: {
    species_total: number;
    species_with_name: number;
    genus_with_name: number;
    family_with_name: number;
    ambiguous_species_names: number;
    sources: string[];
    sources_info: { label: string; tier: string; license_class: string; license: string; url: string; rows: number }[];
    excluded_rows: number;
  };
}

export interface SpeciesIndexEntry {
  slug: string;
  name: string;
  genus: string;
  family: string;
  tr: string; // Turkish common name(s) shown in lists ("" if unknown)
  ts?: string; // further Turkish names, only used for searching
  en: string; // English common name ("" if unknown)
  endemic: number; // 1 = native only in Türkiye (WCVP)
  counts: Record<string, number>; // sequences per marker
}

export interface SequenceRecord {
  accession: string;
  length: number;
  source_title: string;
  definition: string;
  country: string;
  is_turkey: number; // 1 = specimen collected in Türkiye
  matched_via: string; // "accepted" | "synonym"
  sequence: string;
  suspect?: boolean; // exact sequence also assigned to another family
}

export interface NearestRelative {
  species: string;
  slug: string;
  distance: number; // p-distance 0..1
  same_genus: boolean;
}

export interface MarkerDetail {
  n_sequences: number;
  sequences: SequenceRecord[];
  nearest: NearestRelative[];
  indistinguishable: { species: string; slug: string }[];
  tree: { file: string; leaves: string[] } | null;
  discrimination: DiscriminationStatus;
}

export interface SpeciesDetail {
  slug: string;
  name: string;
  genus: string;
  family: string;
  authorship: string;
  endemic: number;
  wcvp_id: string;
  powo_id: string;
  common_name_tr: string;
  common_name_en: string;
  names_tr?: TurkishName[];
  markers: Record<string, MarkerDetail>;
  /** Only for species without any sequence: congeners (or family members) that have data. */
  related_with_data: {
    level: "genus" | "family" | null;
    species: { name: string; slug: string; n_sequences: number; markers: string[] }[];
  } | null;
}

export interface TreeFile {
  family: string;
  genus: string | null;
  group: string; // "Rosaceae" or "Asteraceae/Centaurea"
  marker: string;
  file: string;
  n_leaves: number;
  n_species: number;
  method: string;
  aligner: string; // "MAFFT" | "fallback (preliminary)"
  newick: string;
}

export interface FamilyTree {
  marker: string;
  file: string;
  group: string;
  leaves: number;
  species: number;
}

export interface FamilyEntry {
  family: string;
  species: number;
  split_by_genus: boolean;
  trees: FamilyTree[];
}

export interface BcmSummary {
  sequences_evaluated: number;
  sequences_excluded: number;
  success: number;
  ambiguous: number;
  fail: number;
  success_rate: number | null;
  species_evaluated: number;
  species_success: number;
  species_success_rate: number | null;
}

export interface MarkerStats {
  sequences: number;
  species_total: number;
  species_0: number;
  species_1: number;
  species_2plus: number;
  discrimination: BcmSummary;
  zero_distance_pairs: number;
  zero_distance_pairs_singleton: number;
}

export interface FamilyMarkerStats {
  sequences: number;
  species_0: number;
  species_1: number;
  species_2plus: number;
  discrimination: BcmSummary;
  tree: string | null;
  trees: { file: string; group: string; leaves: number; species: number }[];
  tree_leaves: number;
  split_by_genus: boolean;
  groups_analysed: number;
  groups_skipped: number;
  alignment_method: string;
  alignment: string;
}

export interface FamilyStats {
  species: number;
  species_with_any_sequence: number;
  sequences: number;
  markers: Record<string, FamilyMarkerStats>;
}

export interface GenusRow {
  genus: string;
  family: string;
  species: number;
  endemic_species: number;
  endemic_without_any: number;
  species_with_any: number;
  species_without_any: number;
  sequences: number;
  [key: string]: string | number | null;
}

export interface Stats {
  totals: {
    species: number;
    families: number;
    genera: number;
    species_with_any_sequence: number;
    species_without_sequences: number;
    sequences: number;
    sequences_from_turkey: number;
    endemic_species: number;
    endemic_with_sequence: number;
    endemic_without_sequence: number;
    genera_without_sequence: number;
    families_without_sequence: number;
    species_with_3_markers: number;
    suspect_sequences: number;
  };
  combinations: CombinationRow[];
  markers: Record<string, MarkerStats>;
  families: Record<string, FamilyStats>;
  genera: GenusRow[];
  filter_summary: { marker: string; step: string; count: number }[];
  unmatched_names_total: number;
  unmatched_names_top: { name: string; records: number }[];
  groups_skipped: number;
  groups_analysed: number;
}

export interface CombinationRow {
  combination: string; // "rbcL" or "rbcL+matK"
  n_markers: number;
  species_evaluated: number;
  success: number;
  ambiguous: number;
  fail: number;
  success_rate: number | null;
  definition?: string; // "strict_combined_distance" = mean of shared-marker p-distances + strict species NN
}

export interface GapsFile {
  families: { family: string; species: number }[];
  genera: { family: string; genus: string; species: number; endemic_species: number }[];
  species: { name: string; slug: string; genus: string; family: string; endemic: number }[];
  endemics: { name: string; slug: string; genus: string; family: string }[];
}

/** [accession, species, sequence] */
export type ReferenceRecord = [string, string, string];

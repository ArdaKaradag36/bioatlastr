// Single source for contact, repo, and citation fields used by every page.
export const CONTACT_EMAIL = "karadagardaa@gmail.com";
export const CONTACT_EMAIL_BIOLOGY = "busemenekse@ogr.eskisehir.edu.tr";
export const REPO_URL = "https://github.com/ArdaKaradag36/bioatlastr";
export const PROJECT_TITLE = "Türkiye Bitki DNA Barkod Atlası";
export const PROJECT_TITLE_EN = "Turkey Plant DNA Barcode Atlas";
export const PROJECT_FUNDING = "";
export const PROJECT_YEAR = 2026;
export const PROJECT_VERSION = "0.2.0";

export const AUTHORS = [
  { given: "Arda", family: "Karadağ", roleTr: "yazılım ve geliştirme", roleEn: "software and development" },
  { given: "Buse", family: "Menekşe", roleTr: "biyoloji ve içerik", roleEn: "biology and content" },
] as const;

/** APA-like citation, kept in sync with CITATION.cff. */
export function citationText(): string {
  return (
    `Karadağ, A. & Menekşe, B. (${PROJECT_YEAR}). ${PROJECT_TITLE} ` +
    `(${PROJECT_TITLE_EN}) (version ${PROJECT_VERSION}). ${REPO_URL}`
  );
}

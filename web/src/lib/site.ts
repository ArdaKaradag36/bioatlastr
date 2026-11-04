// Single source for contact, repo, and citation fields used by every page.
export const CONTACT_EMAIL = "karadagardaa@gmail.com";
export const GITHUB_USER = "ArdaKaradag36";
export const REPO_URL = "https://github.com/ArdaKaradag36/bioatlastr";
export const PROJECT_TITLE = "Türkiye Bitki DNA Barkod Atlası";
export const PROJECT_TITLE_EN = "Turkey Plant DNA Barcode Atlas";
export const PROJECT_KIND_TR = "Araştırma projesi";
export const PROJECT_KIND_EN = "Research project";
export const PROJECT_FUNDING = "";
export const PROJECT_YEAR = 2026;
export const PROJECT_VERSION = "0.2.0";

export const STATIC_PATHS = [
  "/",
  "/turler",
  "/agaclar",
  "/veri-bosluklari",
  "/dizi-ara",
  "/sozluk",
  "/yontem",
  "/kaynaklar",
  "/en",
] as const;

/** Canonical origin. Prefer an explicit public URL; else the Vercel production host. */
export function siteUrl(): string {
  const explicit = process.env.NEXT_PUBLIC_SITE_URL?.replace(/\/$/, "");
  if (explicit) return explicit;
  const vercel = process.env.VERCEL_PROJECT_PRODUCTION_URL?.replace(/\/$/, "");
  if (vercel) return vercel.startsWith("http") ? vercel : `https://${vercel}`;
  return "http://localhost:3000";
}

export const AUTHORS = [
  { given: "Arda", family: "Karadağ", roleTr: "yazılım ve geliştirme", roleEn: "software and development" },
  { given: "Buse", family: "Menekşe", roleTr: "biyoloji ve içerik", roleEn: "biology and content" },
] as const;

export const PRODUCERS_TR = "Arda Karadağ, Buse Menekşe";
export const PRODUCERS_EN = "Arda Karadağ, Buse Menekşe";

/** APA-like citation, kept in sync with CITATION.cff. */
export function citationText(): string {
  return (
    `Karadağ, A. & Menekşe, B. (${PROJECT_YEAR}). ${PROJECT_TITLE} ` +
    `(${PROJECT_TITLE_EN}) (version ${PROJECT_VERSION}). ${REPO_URL}`
  );
}

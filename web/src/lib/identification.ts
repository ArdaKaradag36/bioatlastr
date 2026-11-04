// ---------------------------------------------------------------------------
// FUTURE: photo-based plant identification (NOT implemented yet).
//
// This file only defines the contract so the feature can be added later without
// touching the rest of the site:
//
//   1. create  src/app/api/identify/route.ts  (POST, multipart/form-data with "photo")
//   2. implement `PhotoIdentifier` below (e.g. call an image model / external service)
//   3. build a client component that posts to /api/identify and links each candidate
//      to /turler/[slug] using the slugs from public/data/species_index.json
//
// The site is deployed with normal Next.js output (no `output: "export"`), so an API
// route works on Vercel without further configuration.
// ---------------------------------------------------------------------------

export interface IdentificationCandidate {
  /** Latin name; must exist in public/data/species_index.json */
  species: string;
  slug: string;
  /** 0..1 confidence reported by the model */
  score: number;
}

export interface IdentificationResult {
  candidates: IdentificationCandidate[];
  /** Free-text caveat shown to the user. */
  note?: string;
}

export interface PhotoIdentifier {
  identify(photo: Blob): Promise<IdentificationResult>;
}

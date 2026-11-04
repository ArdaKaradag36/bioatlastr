import { publicUrl } from "./site";

const latin = "U+0020-007E, U+00A0-00FF, U+2013, U+2014, U+2018, U+2019, U+201C, U+201D, U+2022, U+2026, U+2212";
const turkish = "U+011E, U+011F, U+0130, U+0131, U+015E, U+015F";

function face(family: string, style: string, file: string, unicodeRange: string): string {
  return (
    `@font-face { font-family: "${family}"; font-style: ${style}; font-weight: 200 900; font-display: swap; ` +
    `src: url("${publicUrl(`/fonts/${file}`)}") format("woff2"); unicode-range: ${unicodeRange}; }`
  );
}

/** Self-hosted Source Sans 3 / Source Serif 4 subsets (SIL OFL 1.1). */
export const FONT_FACE_CSS = [
  face("Atlas Sans", "normal", "sans-latin.woff2", latin),
  face("Atlas Sans", "normal", "sans-tr.woff2", turkish),
  face("Atlas Sans", "italic", "sans-italic-latin.woff2", latin),
  face("Atlas Sans", "italic", "sans-italic-tr.woff2", turkish),
  face("Atlas Serif", "normal", "serif-latin.woff2", latin),
  face("Atlas Serif", "normal", "serif-tr.woff2", turkish),
].join("\n");

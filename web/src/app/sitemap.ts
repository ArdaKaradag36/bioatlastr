import type { MetadataRoute } from "next";
import { getSpeciesIndex } from "@/lib/data.server";
import { siteUrl, STATIC_PATHS } from "@/lib/site";

export const dynamic = "force-static";

export default function sitemap(): MetadataRoute.Sitemap {
  const base = siteUrl();
  const trail = process.env.GITHUB_PAGES === "true" ? "/" : "";
  const pages: MetadataRoute.Sitemap = STATIC_PATHS.map((path) => ({
    url: path === "/" ? `${base}/` : `${base}${path}${trail}`,
    changeFrequency: "monthly",
    priority: path === "/" ? 1 : 0.6,
  }));
  const species: MetadataRoute.Sitemap = getSpeciesIndex().map((s) => ({
    url: `${base}/turler/${s.slug}${trail}`,
    changeFrequency: "monthly",
    priority: 0.4,
  }));
  const all = [...pages, ...species];
  if (all.length >= 50_000) {
    throw new Error(`sitemap has ${all.length} URLs; must stay under 50 000`);
  }
  return all;
}

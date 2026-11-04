import SpeciesView from "@/components/SpeciesView";
// Bundled at build time (not read from disk at request time): public/ files are not available to serverless functions.
import meta from "../../../../public/data/meta.json";

// Species pages are rendered on first request (and cached): the atlas has thousands of species, and the
// species data itself is loaded in the browser from /data/species/<genus>.json. Unknown slugs show a message.
export const dynamicParams = true;

export function generateStaticParams() {
  return [];
}

/** "quercus-robur" -> "Quercus robur" (no data access needed). */
function titleFromSlug(slug: string): string {
  const text = slug.replace(/-/g, " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  return { title: titleFromSlug(slug) };
}

export default async function SpeciesPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const markers = Object.keys(meta.markers);
  return <SpeciesView slug={slug} markers={markers} />;
}

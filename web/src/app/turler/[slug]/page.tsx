import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import SpeciesView from "@/components/SpeciesView";
import { getMeta, getSpeciesBySlug, getSpeciesIndex } from "@/lib/data.server";
import { PROJECT_TITLE, siteUrl } from "@/lib/site";

const isGithubPages = process.env.GITHUB_PAGES === "true";

// Literal `true` is required by Next.js. GitHub Pages export rewrites this to
// `false` in .github/workflows/pages.yml after every slug is prerendered.
export const dynamicParams = true;

export function generateStaticParams() {
  if (!isGithubPages) return [];
  return getSpeciesIndex().map((s) => ({ slug: s.slug }));
}

function summaryFor(slug: string) {
  const sp = getSpeciesBySlug().get(slug);
  if (!sp) return null;
  const nSeq = Object.values(sp.counts).reduce((n, c) => n + c, 0);
  const bits = [`${sp.name} (${sp.family} / ${sp.genus})`];
  if (sp.tr) bits.push(sp.tr);
  bits.push(
    nSeq > 0
      ? `Bu tür için ${nSeq} DNA barkod kaydı var.`
      : "ENA/INSDC’de barkod kaydı bulunamadı. BOLD taranmadı; gelecek çalışma olarak planlandı.",
  );
  if (sp.endemic === 1) bits.push("WCVP’ye göre Türkiye endemiği (Kırmızı Liste değil).");
  return { sp, nSeq, text: bits.join(" ") };
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params;
  const info = summaryFor(slug);
  if (!info) return { title: "Tür bulunamadı", robots: { index: false, follow: false } };
  const url = `${siteUrl()}/turler/${slug}`;
  return {
    title: info.sp.name,
    description: info.text,
    alternates: { canonical: url, languages: { "tr-TR": url, en: `${siteUrl()}/en` } },
    openGraph: { title: `${info.sp.name} · ${PROJECT_TITLE}`, description: info.text, url, type: "article", locale: "tr_TR" },
    twitter: { card: "summary", title: info.sp.name, description: info.text },
  };
}

export default async function SpeciesPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const info = summaryFor(slug);
  if (!info) notFound();
  const markers = Object.keys(getMeta().markers);
  const { sp, text } = info;
  return (
    <div>
      <header>
        <p className="text-sm text-stone-600">
          <Link className="underline" href="/turler">Türler</Link> / {sp.family} / {sp.genus}
        </p>
        <h1 className="mt-1 text-3xl font-bold italic text-stone-900 sm:text-4xl">{sp.name}</h1>
        <p className="mt-2 max-w-3xl text-stone-800">{text}</p>
      </header>
      <SpeciesView slug={slug} markers={markers} hideHeader />
    </div>
  );
}

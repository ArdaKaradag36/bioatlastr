import type { Metadata } from "next";
import Link from "next/link";
import Header from "@/components/Header";
import { Logo } from "@/components/Icons";
import { getMeta } from "@/lib/data.server";
import { FONT_FACE_CSS } from "@/lib/fonts";
import { AUTHORS, CONTACT_EMAIL, GITHUB_USER, PROJECT_FUNDING, PROJECT_KIND_TR, PROJECT_TITLE, PROJECT_YEAR, PRODUCERS_TR, REPO_URL, publicUrl, siteUrl } from "@/lib/site";
import "./globals.css";

const DESCRIPTION =
  "Kısa DNA barkod bölgeleri (rbcL, matK, ITS) Türkiye'de yetişen bitki türlerini birbirinden ayırmaya yeter mi? Herkese açık verilerle hazırlanmış, herkesin anlayabileceği bir araştırma atlası.";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl()),
  title: {
    default: PROJECT_TITLE,
    template: `%s · ${PROJECT_TITLE}`,
  },
  description: DESCRIPTION,
  alternates: {
    canonical: "/",
    languages: { "tr-TR": "/", en: "/en" },
  },
  openGraph: {
    type: "website",
    locale: "tr_TR",
    alternateLocale: ["en_GB"],
    siteName: PROJECT_TITLE,
    title: PROJECT_TITLE,
    description: DESCRIPTION,
    url: "/",
  },
  twitter: {
    card: "summary",
    title: PROJECT_TITLE,
    description: DESCRIPTION,
  },
  robots: { index: true, follow: true },
};

const FOOT = [
  { href: "/", label: "Ana Sayfa" },
  { href: "/turler", label: "Türler" },
  { href: "/agaclar", label: "Ağaçlar" },
  { href: "/veri-bosluklari", label: "Veri boşlukları" },
  { href: "/oncelik", label: "Öncelik listesi" },
  { href: "/rehber", label: "Marker rehberi" },
  { href: "/dizi-ara", label: "Dizi ara" },
  { href: "/sozluk", label: "Sözlük" },
  { href: "/yontem", label: "Yöntem ve sınırlar" },
  { href: "/kaynaklar", label: "Kaynaklar ve lisanslar" },
  { href: "/en", label: "English" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const meta = getMeta();
  const date = new Date(meta.generated_at).toLocaleDateString("tr-TR", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
  return (
    <html lang="tr">
      <head>
        <style dangerouslySetInnerHTML={{ __html: FONT_FACE_CSS }} />
        <link rel="preload" href={publicUrl("/fonts/sans-latin.woff2")} as="font" type="font/woff2" crossOrigin="anonymous" />
        <link rel="preload" href={publicUrl("/fonts/serif-latin.woff2")} as="font" type="font/woff2" crossOrigin="anonymous" />
      </head>
      <body className="flex min-h-screen flex-col">
        <a href="#icerik" className="skip-link">Ana içeriğe geç</a>
        <Header />
        <main id="icerik" className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 max-md:overflow-x-clip sm:px-6 sm:py-10">{children}</main>
        <footer className="mt-10 bg-forest text-on-dark">
          <div className="mx-auto grid max-w-6xl gap-8 px-4 py-10 sm:px-6 md:grid-cols-[1.4fr_1fr]">
            <div>
              <div className="mb-3 flex items-center gap-3">
                <Logo size={34} />
                <span className="font-serif text-lg font-bold">{PROJECT_TITLE}</span>
              </div>
              <p className="max-w-xl text-sm leading-relaxed text-snow/85">
                Bu site, kısa DNA barkodlarının Türkiye&apos;deki bitki türlerini birbirinden ayırmaya yetip yetmediğini herkes için anlaşılır biçimde
                gösteren bir {PROJECT_KIND_TR.toLocaleLowerCase("tr-TR")}dir.
                {PROJECT_FUNDING ? <> {PROJECT_FUNDING}</> : null}
              </p>
              <p className="mt-3 text-sm leading-relaxed text-snow/85">
                <strong>Yapımcılar:</strong> {PRODUCERS_TR}.{" "}
                {AUTHORS.map((a, i) => (
                  <span key={a.family}>
                    {i > 0 ? "; " : ""}
                    {a.given} {a.family} ({a.roleTr})
                  </span>
                ))}
                .
              </p>
              <p className="mt-3 text-sm leading-relaxed text-snow/85">
                © {PROJECT_YEAR} {PRODUCERS_TR}. İletişim:{" "}
                <a className="text-snow underline" href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>
                {" · "}
                GitHub:{" "}
                <a className="text-snow underline" href={REPO_URL} target="_blank" rel="noreferrer">{GITHUB_USER}</a>
              </p>
              <p className="mt-3 max-w-xl rounded-lg bg-snow/10 p-3 text-sm leading-relaxed text-snow/90">
                <strong>Sorumluluk reddi:</strong> Araştırma amaçlıdır; sonuçlar tahmin niteliğindedir, uzman doğrulaması yoktur ve bilimsel ya da
                ticari karar için kullanılmamalıdır.
              </p>
            </div>
            <div>
              <p className="mb-2 text-sm font-semibold uppercase tracking-wider text-snow/70">Sayfalar</p>
              <ul className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
                {FOOT.map((l) => (
                  <li key={l.href}><Link className="inline-block py-1 text-snow underline-offset-4 hover:underline" href={l.href}>{l.label}</Link></li>
                ))}
              </ul>
              <p className="mt-4 text-sm text-snow/80">
                Veri kaynakları:{" "}
                <a className="text-snow underline" href="https://powo.science.kew.org" target="_blank" rel="noreferrer">WCVP (Kew)</a> ve{" "}
                <a className="text-snow underline" href="https://www.ebi.ac.uk/ena/browser/home" target="_blank" rel="noreferrer">ENA (INSDC)</a>.
                Lisanslar ve atıf: <Link className="text-snow underline" href="/kaynaklar">Kaynaklar ve lisanslar</Link>
                {" · "}
                <Link className="text-snow underline" href="/kaynaklar#atif">Nasıl atıf yapılır</Link>
                . Veriler son güncelleme: {date}.
              </p>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}

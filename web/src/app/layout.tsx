import type { Metadata } from "next";
import Link from "next/link";
import Header from "@/components/Header";
import { getMeta } from "@/lib/data.server";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Türkiye Bitki DNA Barkod Atlası",
    template: "%s · Türkiye Bitki DNA Barkod Atlası",
  },
  description:
    "Kısa DNA barkod bölgeleri (rbcL, matK, ITS) Türkiye'de yetişen bitki türlerini birbirinden ayırmaya yeter mi? Herkese açık verilerle hazırlanmış bir araştırma atlası.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const meta = getMeta();
  const date = new Date(meta.generated_at).toLocaleDateString("tr-TR", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
  return (
    <html lang="tr">
      <body className="flex min-h-screen flex-col">
        <Header />
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6">{children}</main>
        <footer className="border-t border-stone-200 bg-white">
          <div className="mx-auto max-w-6xl px-4 py-6 text-sm text-stone-500 sm:px-6">
            <p>
              TÜBİTAK kapsamında bir üniversite öğrenci araştırma projesi. Veri kaynakları:{" "}
              <a className="underline hover:text-emerald-700" href="https://powo.science.kew.org" target="_blank" rel="noreferrer">
                WCVP (Kew)
              </a>{" "}
              ve{" "}
              <a
                className="underline hover:text-emerald-700"
                href="https://www.ebi.ac.uk/ena/browser/home"
                target="_blank"
                rel="noreferrer"
              >
                ENA (INSDC)
              </a>
              . Veriler son güncelleme: {date}.
            </p>
            <p className="mt-1">
              Araştırma amaçlıdır; tahmin niteliğindedir, uzman doğrulaması yoktur. Atıf, lisans ve iletişim: <Link className="underline hover:text-emerald-700" href="/kaynaklar">Kaynaklar ve lisanslar</Link>.
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}

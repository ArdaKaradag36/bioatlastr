"use client";

import { useState } from "react";
import { citationText } from "@/lib/site";

export default function CiteBox({ lang = "tr" }: { lang?: "tr" | "en" }) {
  const text = citationText();
  const [copied, setCopied] = useState(false);
  const title = lang === "en" ? "How to cite" : "Nasıl atıf yapılır";
  const hint =
    lang === "en"
      ? "Copy this citation. Also cite WCVP and the original sequence accessions (see Sources)."
      : "Bu metni kopyalayın. Ayrıca WCVP’ye ve kullandığınız dizilerin erişim numaralarına atıf yapın (Kaynaklar sayfası).";
  const copiedLabel = lang === "en" ? "Copied" : "Kopyalandı";
  const copyLabel = lang === "en" ? "Copy" : "Kopyala";

  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }

  return (
    <section className="rounded-2xl border border-stone-200 bg-white p-5 shadow-card" aria-labelledby="atif-baslik">
      <h2 id="atif-baslik" className="font-serif text-xl font-semibold text-stone-900">
        {title}
      </h2>
      <p className="mt-1 text-sm text-stone-600">{hint}</p>
      <pre tabIndex={0} className="mt-3 overflow-x-auto whitespace-pre-wrap rounded-lg bg-stone-50 p-3 text-sm text-stone-800">
        {text}
      </pre>
      <button
        type="button"
        className="mt-3 inline-flex min-h-11 items-center rounded-xl bg-forest px-4 font-semibold text-on-dark hover:bg-forest-2"
        onClick={copy}
      >
        {copied ? copiedLabel : copyLabel}
      </button>
    </section>
  );
}

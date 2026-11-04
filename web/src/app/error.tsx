"use client";

import Link from "next/link";

export default function Error({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <div className="mx-auto max-w-xl py-8">
      <h1 className="font-serif text-3xl font-bold text-stone-900">Bir şeyler ters gitti</h1>
      <p className="mt-3 text-stone-800">Sayfa yüklenemedi. Yeniden deneyin veya ana sayfaya dönün.</p>
      <div className="mt-6 flex flex-wrap gap-3">
        <button
          type="button"
          className="inline-flex min-h-11 items-center rounded-xl bg-forest px-4 font-semibold text-on-dark"
          onClick={() => reset()}
        >
          Yeniden dene
        </button>
        <Link className="inline-flex min-h-11 items-center font-semibold text-link underline" href="/">
          Ana sayfa
        </Link>
      </div>
    </div>
  );
}

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import SpeciesSearch from "./SpeciesSearch";

const LINKS = [
  { href: "/", label: "Ana Sayfa" },
  { href: "/turler", label: "Türler" },
  { href: "/agaclar", label: "Ağaçlar" },
  { href: "/veri-bosluklari", label: "Veri Boşlukları" },
  { href: "/dizi-ara", label: "Dizi Ara" },
  { href: "/yontem", label: "Yöntem ve Sınırlar" },
  { href: "/kaynaklar", label: "Kaynaklar" },
];

export default function Header() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  const isActive = (href: string) => (href === "/" ? pathname === "/" : pathname.startsWith(href));

  return (
    <header className="sticky top-0 z-40 border-b border-stone-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center gap-4 px-4 py-3 sm:px-6">
        <Link href="/" className="flex items-center gap-2 font-semibold text-emerald-800">
          <span aria-hidden className="text-2xl">🌿</span>
          <span className="hidden leading-tight sm:block">
            Türkiye Bitki
            <br />
            DNA Barkod Atlası
          </span>
        </Link>

        <nav className="ml-4 hidden items-center gap-1 xl:flex" aria-label="Ana menü">
          {LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={`whitespace-nowrap rounded-lg px-3 py-2 text-sm font-medium transition ${
                isActive(l.href)
                  ? "bg-emerald-50 text-emerald-800"
                  : "text-stone-600 hover:bg-stone-100 hover:text-stone-900"
              }`}
            >
              {l.label}
            </Link>
          ))}
        </nav>

        <div className="ml-auto w-full max-w-xs">
          <SpeciesSearch placeholder="Tür ara (Latince / Türkçe)" size="sm" />
        </div>

        <button
          type="button"
          className="rounded-lg border border-stone-300 p-2 xl:hidden"
          aria-label="Menüyü aç/kapat"
          aria-expanded={open}
          onClick={() => setOpen((v) => !v)}
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2">
            {open ? <path d="M4 4l12 12M16 4L4 16" /> : <path d="M3 6h14M3 10h14M3 14h14" />}
          </svg>
        </button>
      </div>

      {open && (
        <nav className="border-t border-stone-200 bg-white px-4 py-2 xl:hidden" aria-label="Mobil menü">
          {LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              onClick={() => setOpen(false)}
              className={`block rounded-lg px-3 py-2.5 text-sm font-medium ${
                isActive(l.href) ? "bg-emerald-50 text-emerald-800" : "text-stone-700"
              }`}
            >
              {l.label}
            </Link>
          ))}
        </nav>
      )}
    </header>
  );
}

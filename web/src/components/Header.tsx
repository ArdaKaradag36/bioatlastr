"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Logo } from "./Icons";
import SpeciesSearch from "./SpeciesSearch";

const LINKS = [
  { href: "/", label: "Ana Sayfa" },
  { href: "/turler", label: "Türler" },
  { href: "/agaclar", label: "Ağaçlar" },
  { href: "/veri-bosluklari", label: "Veri Boşlukları" },
  { href: "/dizi-ara", label: "Dizi Ara" },
  { href: "/sozluk", label: "Sözlük" },
  { href: "/yontem", label: "Yöntem" },
  { href: "/kaynaklar", label: "Kaynaklar" },
];

export default function Header() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  const isActive = (href: string) => (href === "/" ? pathname === "/" : pathname.startsWith(href));

  return (
    <header className="sticky top-0 z-40 border-b border-stone-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center gap-3 px-4 py-2.5 sm:px-6">
        <Link href="/" className="flex shrink-0 items-center gap-2.5" aria-label="Türkiye Bitki DNA Barkod Atlası, ana sayfa">
          <Logo size={38} />
          <span className="hidden font-serif text-lg font-bold leading-tight text-stone-900 sm:block">
            Bitki DNA
            <br />
            Barkod Atlası
          </span>
        </Link>

        <nav className="ml-2 hidden items-center gap-0.5 xl:flex" aria-label="Ana menü">
          {LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              aria-current={isActive(l.href) ? "page" : undefined}
              className={`whitespace-nowrap rounded-lg px-3 py-2 text-[0.95rem] font-medium transition ${
                isActive(l.href) ? "bg-emerald-100 text-link" : "text-stone-700 hover:bg-stone-100 hover:text-stone-900"
              }`}
            >
              {l.label}
            </Link>
          ))}
        </nav>

        <div className="ml-auto w-full max-w-xs">
          <SpeciesSearch placeholder="Tür ara: meşe, Quercus…" size="sm" />
        </div>

        <button
          type="button"
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-stone-300 xl:hidden"
          aria-label={open ? "Menüyü kapat" : "Menüyü aç"}
          aria-expanded={open}
          aria-controls="mobile-nav"
          onClick={() => setOpen((v) => !v)}
        >
          <svg width="22" height="22" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
            {open ? <path d="M4 4l12 12M16 4L4 16" /> : <path d="M3 6h14M3 10h14M3 14h14" />}
          </svg>
        </button>
      </div>

      {open && (
        <nav id="mobile-nav" className="border-t border-stone-200 bg-white px-4 py-2 xl:hidden" aria-label="Mobil menü">
          <ul className="grid grid-cols-2 gap-1 sm:grid-cols-3">
            {LINKS.map((l) => (
              <li key={l.href}>
                <Link
                  href={l.href}
                  onClick={() => setOpen(false)}
                  aria-current={isActive(l.href) ? "page" : undefined}
                  className={`flex min-h-12 items-center rounded-xl px-3 font-medium ${
                    isActive(l.href) ? "bg-emerald-100 text-link" : "text-stone-800 hover:bg-stone-100"
                  }`}
                >
                  {l.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      )}
    </header>
  );
}

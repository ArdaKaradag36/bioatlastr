import Link from "next/link";
import SpeciesSearch from "@/components/SpeciesSearch";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-xl py-8">
      <h1 className="font-serif text-3xl font-bold text-stone-900">Sayfa bulunamadı</h1>
      <p className="mt-3 text-stone-800">
        Bu adres sitede yok. Ana sayfaya dönebilir veya bir tür adı arayabilirsiniz.
      </p>
      <div className="mt-6">
        <SpeciesSearch placeholder="Tür ara: meşe, kızılçam, Quercus…" />
      </div>
      <p className="mt-6">
        <Link className="inline-flex min-h-11 items-center font-semibold text-link underline" href="/">
          Ana sayfa
        </Link>
        {" · "}
        <Link className="inline-flex min-h-11 items-center font-semibold text-link underline" href="/turler">
          Tür listesi
        </Link>
      </p>
    </div>
  );
}

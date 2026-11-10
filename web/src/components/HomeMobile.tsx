import Link from "next/link";
import Fold from "@/components/Fold";
import Term from "@/components/Term";
import { Card, COVERAGE_COLORS, StackedBar } from "@/components/ui";
import { num, pct } from "@/lib/format";
import type { FamilyEntry, Meta, Stats } from "@/lib/types";

const MARKER_TERM: Record<string, string> = { rbcL: "rbcl", matK: "matk", ITS: "its" };

export default function HomeMobile({
  stats,
  meta,
  families,
}: {
  stats: Stats;
  meta: Meta;
  families: FamilyEntry[];
}) {
  const markers = Object.keys(meta.markers);
  const t = stats.totals;
  const comboRows = stats.combinations.filter((c) => c.n_markers > 1);
  const bestStrict = markers
    .map((m) => ({ m, d: stats.markers[m].discrimination }))
    .filter((x) => x.d.species_success_rate != null)
    .sort((a, b) => (b.d.species_success_rate ?? 0) - (a.d.species_success_rate ?? 0))[0];

  return (
    <div className="space-y-6">
      <h1 className="font-serif text-2xl font-bold text-stone-900">Türkiye Bitki DNA Barkod Atlası</h1>
      <p className="text-lg text-stone-800">
        Türkiye&apos;de yetişen bitkilerin kısa DNA barkodlarıyla birbirinden ayırt edilip edilemediğini ve hangilerinin kaydının eksik olduğunu gösterir.
      </p>

      <Card className="border-emerald-400">
        <p className="text-sm font-semibold uppercase tracking-wider text-stone-600">Kayıtlı barkod</p>
        <p className="mt-2 font-serif text-4xl font-bold text-link">
          {num(t.species)} türün {num(t.species_with_any_sequence)}&apos;inde
        </p>
        <p className="mt-2 text-stone-800">
          ENA/INSDC&apos;de en az bir barkod kaydı var ({pct(t.species_with_any_sequence / t.species)}). BOLD taranmadı; gelecek çalışma olarak planlandı.
        </p>
      </Card>

      <Link
        href="/veri-bosluklari"
        className="flex min-h-12 items-center justify-center rounded-xl bg-forest px-5 text-center font-semibold text-on-dark"
      >
        Eksik olanlar ({num(t.species_without_sequences)} tür)
      </Link>

      <div className="grid grid-cols-1 gap-3">
        {markers.map((m) => {
          const s = stats.markers[m];
          const d = s.discrimination;
          return (
            <Card key={m} className="p-4">
              <div className="flex items-baseline justify-between gap-2">
                <h2 className="font-serif text-xl font-semibold">{MARKER_TERM[m] ? <Term id={MARKER_TERM[m]}>{m}</Term> : m}</h2>
                <span className="text-2xl font-bold text-link">{pct(d.species_success_rate)}</span>
              </div>
              <p className="mt-1 text-sm text-stone-700">
                kayıtlı {pct(s.species_2plus + s.species_1 > 0 ? (s.species_2plus + s.species_1) / t.species : 0)} · katı başarı {pct(d.species_success_rate)}
                {" "}(aile/cins içi)
              </p>
              {m === "ITS" && (
                <p className="mt-2 text-sm text-amber-900">ITS nükleer ve çok kopyalıdır (n = {num(d.species_evaluated)} tür).</p>
              )}
            </Card>
          );
        })}
      </div>

      <Fold title="Nasıl okunur?" lead="Katı tanım: türün bütün dizileri en yakın komşuyu geçmeli.">
        <p className="text-stone-800">
          Resmî başarı tanımı katıdır. Karşılaştırma aynı aile (büyük ailelerde aynı cins) içindedir.{" "}
          {bestStrict && (
            <>
              Tek bölgeler arasında en yüksek katı başarı {bestStrict.m} ({pct(bestStrict.d.species_success_rate)}, n = {num(bestStrict.d.species_evaluated)}).
              {bestStrict.m === "ITS" && " ITS nükleer bir bölgedir."}
            </>
          )}
        </p>
        {markers.map((m) => {
          const s = stats.markers[m];
          return (
            <div key={m} className="mt-3">
              <div className="mb-1 text-sm font-medium">{m}</div>
              <StackedBar
                segments={[
                  { label: "Dizi yok", value: s.species_0, color: COVERAGE_COLORS.zero },
                  { label: "1 dizi", value: s.species_1, color: COVERAGE_COLORS.one },
                  { label: "2 ve üzeri dizi", value: s.species_2plus, color: COVERAGE_COLORS.twoPlus },
                ]}
              />
            </div>
          );
        })}
      </Fold>

      <Fold title="Yöntem özeti" lead="WCVP listesi, ENA dizileri, eşiksiz en-yakın-komşu.">
        <p className="text-stone-800">
          Tür listesi Kew WCVP; diziler ENA/INSDC. Hizalama: {meta.aligner_label}. Ölçüm eşiksiz en-yakın-komşudur.
          Ayrıntı: <Link className="text-link underline" href="/yontem">Yöntem</Link>.
        </p>
      </Fold>

      <Fold title="Bölgeleri birlikte kullanırsak?" lead="Birleşik mesafe (strict_combined_distance); n = tüm bölgelerde dizisi olan türler; yalnız sütunları aynı n.">
        <ul className="space-y-3">
          {comboRows.map((c) => (
            <li key={c.combination} className="rounded-xl border border-stone-200 p-3">
              <div className="font-semibold">{c.combination.replaceAll("+", " + ")}</div>
              <p className="text-sm text-stone-700">
                n = {num(c.species_evaluated)} · birleşik {pct(c.success_rate)}
                {c.rbcL_alone_success_rate != null && <> · rbcL {pct(c.rbcL_alone_success_rate)}</>}
                {c.matK_alone_success_rate != null && <> · matK {pct(c.matK_alone_success_rate)}</>}
                {c.ITS_alone_success_rate != null && <> · ITS {pct(c.ITS_alone_success_rate)}</>}
              </p>
            </li>
          ))}
        </ul>
      </Fold>

      <Fold title="Hangi ailelerde veri var?" lead={`En çok türü olan ${Math.min(8, families.length)} aile.`}>
        <ul className="space-y-2 text-sm">
          {[...families]
            .sort((a, b) => b.species - a.species)
            .slice(0, 8)
            .map((f) => {
              const fs = stats.families[f.family];
              return (
                <li key={f.family} className="flex justify-between gap-2">
                  <Link className="text-link underline" href={`/agaclar?aile=${f.family}`}>{f.family}</Link>
                  <span>{num(fs.species_with_any_sequence)}/{num(fs.species)}</span>
                </li>
              );
            })}
        </ul>
      </Fold>
    </div>
  );
}

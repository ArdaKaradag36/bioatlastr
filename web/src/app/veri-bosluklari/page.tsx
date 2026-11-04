import type { Metadata } from "next";
import { GeneraTable, MissingSpeciesTable } from "@/components/GapsTables";
import { Bar, COVERAGE_COLORS, Card, Legend, PageTitle, SectionTitle, StackedBar } from "@/components/ui";
import { getMeta, getStats } from "@/lib/data.server";
import { num, pct } from "@/lib/format";

export const metadata: Metadata = { title: "Veri boşlukları" };

export default function DataGapsPage() {
  const stats = getStats();
  const markers = Object.keys(getMeta().markers);
  const families = Object.keys(stats.families).sort((a, b) => stats.families[b].species - stats.families[a].species);
  const t = stats.totals;
  const maxMissing = Math.max(
    ...families.map((f) => stats.families[f].species - stats.families[f].species_with_any_sequence),
    1,
  );
  const legend = [
    { label: "Dizi yok", color: COVERAGE_COLORS.zero },
    { label: "1 dizi", color: COVERAGE_COLORS.one },
    { label: "2+ dizi", color: COVERAGE_COLORS.twoPlus },
  ];

  return (
    <div>
      <PageTitle title="Veri boşlukları">
        Barkodlama için en büyük engel eksik veridir. Bu sayfa hangi türlerin, cinslerin ve markerların
        ENA/GenBank&apos;ta yeterince temsil edilmediğini gösterir.
      </PageTitle>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <div className="text-sm text-stone-500">Hiçbir markerde dizisi olmayan tür</div>
          <div className="text-3xl font-bold text-emerald-800">{num(t.species_without_sequences)}</div>
          <div className="text-sm text-stone-500">{num(t.species)} türün {pct(t.species_without_sequences / t.species)}&apos;i</div>
        </Card>
        <Card>
          <div className="text-sm text-stone-500">Dizisi olmayan endemik tür</div>
          <div className="text-3xl font-bold text-red-800">{num(t.endemic_without_sequence)}</div>
          <div className="text-sm text-stone-500">{num(t.endemic_species)} endemik türün {pct(t.endemic_species ? t.endemic_without_sequence / t.endemic_species : null)}&apos;i</div>
        </Card>
        <Card>
          <div className="text-sm text-stone-500">Hiç dizisi olmayan cins / aile</div>
          <div className="text-3xl font-bold text-emerald-800">{num(t.genera_without_sequence)} / {num(t.families_without_sequence)}</div>
          <div className="text-sm text-stone-500">{num(t.genera)} cins, {num(t.families)} aile içinde</div>
        </Card>
      </div>

      <SectionTitle>Marker başına kapsam</SectionTitle>
      <Card>
        <ul className="space-y-5">
          {markers.map((m) => {
            const s = stats.markers[m];
            return (
              <li key={m}>
                <div className="mb-1 flex items-baseline justify-between">
                  <span className="font-semibold">{m}</span>
                  <span className="text-sm text-stone-500">{num(s.sequences)} dizi</span>
                </div>
                <StackedBar
                  segments={[
                    { label: "Dizi yok", value: s.species_0, color: COVERAGE_COLORS.zero },
                    { label: "1 dizi", value: s.species_1, color: COVERAGE_COLORS.one },
                    { label: "2+ dizi", value: s.species_2plus, color: COVERAGE_COLORS.twoPlus },
                  ]}
                />
                <div className="mt-1 text-sm text-stone-600">
                  {num(s.species_0)} tür dizisiz ({pct(s.species_0 / s.species_total)}) · {num(s.species_1)} tür tek dizili ·{" "}
                  {num(s.species_2plus)} tür 2+ dizili ({pct(s.species_2plus / s.species_total)})
                </div>
              </li>
            );
          })}
        </ul>
        <div className="mt-4"><Legend items={legend} /></div>
      </Card>

      <SectionTitle>Ailelere göre eksik türler</SectionTitle>
      <Card>
        <ul className="space-y-3">
          {families.map((f) => {
            const fs = stats.families[f];
            const missing = fs.species - fs.species_with_any_sequence;
            return (
              <li key={f} className="grid items-center gap-2 sm:grid-cols-[10rem_1fr_14rem]">
                <span className="font-medium">{f}</span>
                <Bar value={missing} max={maxMissing} color="#a8a29e" />
                <span className="text-sm text-stone-600 sm:text-right">
                  {num(missing)} / {num(fs.species)} tür dizisiz ({pct(missing / fs.species, 0)})
                </span>
              </li>
            );
          })}
        </ul>
      </Card>

      <h3 className="mb-2 mt-8 text-lg font-semibold">Aile × marker tablosu (tür sayısı: 0 / 1 / 2+ dizi)</h3>
      <div className="overflow-x-auto rounded-xl border border-stone-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-stone-50 text-left text-stone-600">
            <tr>
              <th className="p-3">Aile</th>
              <th className="p-3 text-right">Tür</th>
              {markers.map((m) => <th key={m} className="p-3 text-right">{m}</th>)}
            </tr>
          </thead>
          <tbody>
            {families.map((f) => {
              const fs = stats.families[f];
              return (
                <tr key={f} className="border-t border-stone-100">
                  <td className="p-3 font-medium">{f}</td>
                  <td className="p-3 text-right">{num(fs.species)}</td>
                  {markers.map((m) => {
                    const x = fs.markers[m];
                    return (
                      <td key={m} className="whitespace-nowrap p-3 text-right font-mono text-xs">
                        {num(x.species_0)} / {num(x.species_1)} / {num(x.species_2plus)}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <SectionTitle>En az veriye sahip cinsler</SectionTitle>
      <GeneraTable genera={stats.genera} families={families} markers={markers} />

      <SectionTitle>Dizisi olmayan türler</SectionTitle>
      <MissingSpeciesTable families={families} markers={markers} />

      <SectionTitle>Dizisi olmayan endemik türler</SectionTitle>
      <p className="mb-3 max-w-3xl text-sm text-stone-600">
        Endemik tür: WCVP&apos;ye göre yalnızca Türkiye&apos;de doğal olarak yetişen tür. Bu türlerin barkod verisi
        başka ülkelerden toplanamaz; öncelikli toplama hedefleridir.
      </p>
      <MissingSpeciesTable families={families} markers={markers} initialEndemic />
    </div>
  );
}

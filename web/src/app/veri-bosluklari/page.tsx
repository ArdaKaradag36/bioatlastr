import type { Metadata } from "next";
import { GeneraTable, MissingSpeciesTable } from "@/components/GapsTables";
import Link from "next/link";
import Term from "@/components/Term";
import { Bar, COVERAGE_COLORS, Card, Legend, PageIntro, PageTitle, Purpose, SectionTitle, StackedBar } from "@/components/ui";
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
    { label: "2 ve üzeri dizi", color: COVERAGE_COLORS.twoPlus },
  ];

  return (
    <div>
      <PageTitle eyebrow="Veri boşlukları" title="Hangi türlerin DNA barkodu eksik?">
        Bir türün DNA barkodu yoksa o türü barkodla tanıyamayız. Bu sayfa, nerede eksik olduğunu ve en çok hangi türlerin beklediğini gösterir.
      </PageTitle>
      <PageIntro
        what={
          <p>
            Türkiye&apos;deki türlerden hangilerinin, hangi cinslerin ve ailelerin henüz herkese açık arşivlerde DNA barkodu bulunmadığını.
            Bu eksiklere <Term id="veri-boslugu">veri boşluğu</Term> diyoruz. Boşluk, türün önemsiz olduğunu değil, yalnızca henüz okunmadığını ya da yüklenmediğini gösterir.
          </p>
        }
        how={
          <p>
            Önce üstteki üç kutuya bakın: her birinin altında sayının ne demek olduğu yazıyor. Aşağıda çubuklar kısmen dolu ya da boştur; boş kısım eksik demektir.
            En altta <Term id="endemik">endemik</Term> (yalnızca Türkiye&apos;de yetişen) türlerden dizisi olmayanlar var; bu türlerin barkodunu başka ülkenin verisi tamamlayamaz.
          </p>
        }
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <div className="text-sm font-semibold text-stone-600">Hiçbir bölgede dizisi olmayan tür</div>
          <div className="font-serif text-4xl font-bold text-link">{num(t.species_without_sequences)}</div>
          <p className="mt-2 border-t border-stone-100 pt-2 text-sm text-stone-700">{num(t.species)} türün {num(t.species_without_sequences)} tanesinin ({pct(t.species_without_sequences / t.species)}) üç barkod bölgesinin hiçbirinde ENA/INSDC kaydı yok. BOLD taranmadı; gelecek çalışma olarak planlandı.</p>
        </Card>
        <Card>
          <div className="text-sm font-semibold text-stone-600">Dizisi olmayan endemik tür</div>
          <div className="font-serif text-4xl font-bold text-red-800">{num(t.endemic_without_sequence)}</div>
          <p className="mt-2 border-t border-stone-100 pt-2 text-sm text-stone-700">{num(t.endemic_species)} endemik (WCVP; Kırmızı Liste değil) türün {num(t.endemic_without_sequence)} tanesinin ({pct(t.endemic_species ? t.endemic_without_sequence / t.endemic_species : null)}) hiç dizisi yok. Bu türler yalnızca Türkiye&apos;de yetiştiği için öncelikli toplama hedefleridir.</p>
        </Card>
        <Card>
          <div className="text-sm font-semibold text-stone-600">Hiç dizisi olmayan cins / aile</div>
          <div className="font-serif text-4xl font-bold text-link">{num(t.genera_without_sequence)} / {num(t.families_without_sequence)}</div>
          <p className="mt-2 border-t border-stone-100 pt-2 text-sm text-stone-700">{num(t.genera)} cinsin {num(t.genera_without_sequence)} tanesinde, {num(t.families)} ailenin {num(t.families_without_sequence)} tanesinde hiçbir türün dizisi yok.</p>
        </Card>
      </div>

      <SectionTitle>Her barkod bölgesinde kaç tür eksik?</SectionTitle>
      <p className="mb-3 max-w-3xl text-stone-700">Her çubuk, o <Term id="barkod-bolgesi">barkod bölgesi</Term> için türleri üç gruba ayırır: hiç dizisi olmayanlar, tek dizisi olanlar ve birden çok dizisi olanlar. Tek diziyle bir türün çeşitliliği anlaşılamaz (<Term id="orneklem">örneklem</Term> küçüktür).</p>
      <Card>
        <ul className="space-y-5">
          {markers.map((m) => {
            const s = stats.markers[m];
            return (
              <li key={m}>
                <div className="mb-1 flex items-baseline justify-between">
                  <span className="font-semibold">{m}</span>
                  <span className="text-sm text-stone-700">{num(s.sequences)} dizi</span>
                </div>
                <StackedBar
                  segments={[
                    { label: "Dizi yok", value: s.species_0, color: COVERAGE_COLORS.zero },
                    { label: "1 dizi", value: s.species_1, color: COVERAGE_COLORS.one },
                    { label: "2 ve üzeri dizi", value: s.species_2plus, color: COVERAGE_COLORS.twoPlus },
                  ]}
                />
                <div className="mt-1 text-sm text-stone-700">
                  {num(s.species_total)} türün {num(s.species_0)} tanesinin hiç dizisi yok ({pct(s.species_0 / s.species_total)}); {num(s.species_1)} tanesinin tek dizisi var; {num(s.species_2plus)} tanesinin ({pct(s.species_2plus / s.species_total)}) iki ya da daha çok dizisi var.
                </div>
              </li>
            );
          })}
        </ul>
        <div className="mt-4"><Legend items={legend} /></div>
      </Card>

      <SectionTitle>Hangi ailelerde en çok tür eksik?</SectionTitle>
      <p className="mb-3 max-w-3xl text-stone-700">Çubuk ne kadar uzunsa o <Term id="familya">ailede</Term> dizisi olmayan tür sayısı o kadar fazla. (Çubuklar en kalabalık aileye göre ölçeklenmiştir.)</p>
      <Card>
        <ul className="space-y-3">
          {families.map((f) => {
            const fs = stats.families[f];
            const missing = fs.species - fs.species_with_any_sequence;
            return (
              <li key={f} className="grid items-center gap-2 sm:grid-cols-[10rem_1fr_14rem]">
                <span className="font-medium">{f}</span>
                <Bar value={missing} max={maxMissing} color="var(--st-400)" />
                <span className="text-sm text-stone-700 sm:text-right">
                  {num(fs.species)} türün {num(missing)} tanesinde dizi yok ({pct(missing / fs.species, 0)})
                </span>
              </li>
            );
          })}
        </ul>
      </Card>

      <h3 className="mb-1 mt-8 font-serif text-xl font-semibold">Aile ve barkod bölgesi tablosu</h3>
      <p className="mb-2 text-stone-700">Her hücrede üç sayı var: <strong>hiç dizisi olmayan / tek dizisi olan / iki ve daha çok dizisi olan</strong> tür sayısı.</p>
      <div tabIndex={0} className="overflow-x-auto rounded-xl border border-stone-200 bg-white">
        <table className="w-full text-[0.95rem]">
          <thead className="bg-stone-50 text-left text-stone-700">
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

      <SectionTitle>Hangi cinslerde veri en az?</SectionTitle>
      <p className="mb-3 max-w-3xl text-stone-700"><Term id="cins">Cinsler</Term>, dizisi olan tür oranına göre en azdan başlayarak sıralanır. Süzgeçlerle aile seçebilir ya da çok az türü olan cinsleri gizleyebilirsiniz.</p>
      <GeneraTable genera={stats.genera} families={families} markers={markers} />

      <SectionTitle>Dizisi olmayan türlerin listesi</SectionTitle>
      <p className="mb-3 max-w-3xl text-stone-700">Bir türün adına tıklayarak o türün sayfasına gidebilir, dizisi olan en yakın akrabalarını görebilirsiniz.</p>
      <MissingSpeciesTable families={families} markers={markers} />

      <SectionTitle>Dizisi olmayan endemik türler</SectionTitle>
      <p className="mb-3 max-w-3xl text-stone-700">
        <Term id="endemik">Endemik tür</Term>: WCVP&apos;ye göre yalnızca Türkiye&apos;de doğal olarak yetişen tür. Bu türlerin barkod verisi başka ülkelerden alınamaz; bu yüzden önce bunların toplanması gerekir.
      </p>
      <MissingSpeciesTable families={families} markers={markers} initialEndemic />

      <Purpose>
        Hangi türlerin DNA barkodunun eksik olduğunu açıkça göstermek; böylece sonraki saha ve laboratuvar çalışmaları önce bu boşlukları doldurmaya yönelebilsin. <Link className="font-medium text-on-dark underline" href="/turler">Türlere göz atın</Link>.
      </Purpose>
    </div>
  );
}

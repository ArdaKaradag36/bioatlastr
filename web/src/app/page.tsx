import Link from "next/link";
import SpeciesSearch from "@/components/SpeciesSearch";
import { Bar, Card, Legend, SectionTitle, StackedBar, StatCard, COVERAGE_COLORS } from "@/components/ui";
import { getFamilies, getMeta, getStats } from "@/lib/data.server";
import { num, pct } from "@/lib/format";

export default function HomePage() {
  const stats = getStats();
  const meta = getMeta();
  const families = getFamilies();
  const markers = Object.keys(meta.markers);
  const t = stats.totals;

  return (
    <div>
      {/* Hero */}
      <section className="rounded-3xl bg-gradient-to-br from-emerald-700 to-emerald-900 px-6 py-12 text-white sm:px-12 sm:py-16">
        <p className="mb-3 text-sm font-medium uppercase tracking-wider text-emerald-200">
          TÜBİTAK öğrenci araştırma projesi
        </p>
        <h1 className="max-w-3xl text-3xl font-bold leading-tight sm:text-5xl">
          Türkiye Bitki DNA Barkod Atlası
        </h1>
        <p className="mt-4 max-w-3xl text-lg text-emerald-50">
          Araştırma sorusu: <strong>kısa bir DNA barkod bölgesi ({markers.join(", ")}) Türkiye&apos;de
          yetişen bitki türlerini birbirinden ayırmaya yeter mi?</strong>
        </p>
        <div className="mt-8 max-w-xl text-stone-900">
          <SpeciesSearch placeholder="Tür ara: ör. meşe, Quercus, çam…" autoFocus={false} />
        </div>
      </section>

      {/* Headline numbers */}
      <SectionTitle>Rakamlarla atlas</SectionTitle>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Türkiye florası türleri (WCVP)"
          value={num(t.species)}
          note={`${num(t.families)} aile, ${num(t.genera)} cins · ${num(t.endemic_species)} endemik`}
        />
        <StatCard
          label="Dizisi olan tür"
          value={num(t.species_with_any_sequence)}
          note={`${pct(t.species_with_any_sequence / t.species)} (en az bir marker)`}
        />
        <StatCard
          label="Filtreden geçen dizi"
          value={num(t.sequences)}
          note={`ENA/GenBank erişim numaralarıyla · ${num(t.sequences_from_turkey)} tanesi Türkiye örneği`}
        />
        <StatCard
          label="Dizisi olmayan tür"
          value={num(t.species_without_sequences)}
          note={
            <>
              {num(t.endemic_without_sequence)} tanesi endemik (dizisi olmayan endemik tür) ·{" "}
              <Link className="text-emerald-700 underline" href="/veri-bosluklari">Veri boşluklarına bak</Link>
            </>
          }
        />
      </div>

      {/* Per marker */}
      <SectionTitle>Her marker türleri ne kadar ayırt ediyor?</SectionTitle>
      <p className="mb-4 max-w-3xl text-stone-600">
        &quot;En yakın eşleşme&quot; yöntemi: her dizi için, aynı ailedeki (çok büyük ailelerde aynı cinsteki) diğer
        dizilerle p-mesafesi hesaplanır; en yakın komşu aynı türe aitse başarılıdır. Yalnızca{" "}
        en az 2 dizisi olan türler değerlendirilir. Hizalama: <strong>{meta.aligner_label}</strong>.
      </p>
      <div className="grid gap-4 md:grid-cols-3">
        {markers.map((m) => {
          const s = stats.markers[m];
          const d = s.discrimination;
          return (
            <Card key={m}>
              <div className="flex items-baseline justify-between">
                <h3 className="text-xl font-semibold">{m}</h3>
                <span className="text-sm text-stone-500">{num(s.sequences)} dizi</span>
              </div>
              <div className="mt-3 text-4xl font-bold text-emerald-800">{pct(d.success_rate)}</div>
              <div className="text-sm text-stone-500">
                ayırt etme başarısı ({num(d.success)} / {num(d.sequences_evaluated)} dizi)
              </div>
              <div className="mt-3 text-sm text-stone-600">
                Tür düzeyinde: {pct(d.species_success_rate)} ({num(d.species_success)} / {num(d.species_evaluated)} tür)
              </div>
              <div className="mt-4">
                <div className="mb-1 text-xs font-medium text-stone-500">Kapsam (tür sayısı)</div>
                <StackedBar
                  segments={[
                    { label: "Dizi yok", value: s.species_0, color: COVERAGE_COLORS.zero },
                    { label: "1 dizi", value: s.species_1, color: COVERAGE_COLORS.one },
                    { label: "2+ dizi", value: s.species_2plus, color: COVERAGE_COLORS.twoPlus },
                  ]}
                />
                <div className="mt-2 text-xs text-stone-500">
                  {num(s.species_0)} dizi yok · {num(s.species_1)} tek dizi · {num(s.species_2plus)} iki ve üzeri
                </div>
              </div>
              <div className="mt-3 text-sm text-stone-600">
                Mesafesi 0 olan tür çifti: {num(s.zero_distance_pairs)}
              </div>
            </Card>
          );
        })}
      </div>
      <div className="mt-3">
        <Legend
          items={[
            { label: "Dizi yok", color: COVERAGE_COLORS.zero },
            { label: "1 dizi", color: COVERAGE_COLORS.one },
            { label: "2+ dizi", color: COVERAGE_COLORS.twoPlus },
          ]}
        />
      </div>

      {/* Marker combinations */}
      <SectionTitle>Marker kombinasyonları</SectionTitle>
      <p className="mb-3 max-w-3xl text-sm text-stone-600">
        Tür düzeyinde en yakın komşu testi: bir türün kendi içindeki en küçük mesafesi, başka herhangi bir türe olan en
        küçük mesafeden (kombinasyonda ortak olan markerların ortalaması) küçükse başarılı sayılır. Yalnızca ilgili
        markerlerin hepsinde değerlendirilebilen gruplar sayılır.
      </p>
      <div className="overflow-x-auto rounded-xl border border-stone-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-stone-50 text-left text-stone-600">
            <tr>
              <th className="p-3">Marker / kombinasyon</th>
              <th className="p-3 text-right">Değerlendirilen tür</th>
              <th className="p-3 text-right">Başarılı</th>
              <th className="p-3 text-right">Belirsiz</th>
              <th className="p-3 text-right">Başarısız</th>
              <th className="p-3 text-right">Başarı oranı</th>
            </tr>
          </thead>
          <tbody>
            {stats.combinations.map((c) => (
              <tr key={c.combination} className="border-t border-stone-100">
                <td className="p-3 font-medium">{c.combination.replaceAll("+", " + ")}</td>
                <td className="p-3 text-right">{num(c.species_evaluated)}</td>
                <td className="p-3 text-right">{num(c.success)}</td>
                <td className="p-3 text-right">{num(c.ambiguous)}</td>
                <td className="p-3 text-right">{num(c.fail)}</td>
                <td className="p-3 text-right font-semibold text-emerald-800">{pct(c.success_rate)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Families */}
      <SectionTitle>Ailelere göre dizisi olan türler</SectionTitle>
      <Card>
        <ul className="space-y-3">
          {[...families].sort((a, b) => b.species - a.species).slice(0, 25).map((f) => {
            const fs = stats.families[f.family];
            return (
              <li key={f.family} className="grid items-center gap-2 sm:grid-cols-[10rem_1fr_9rem]">
                <Link href={`/agaclar?aile=${f.family}`} className="font-medium text-emerald-800 hover:underline">
                  {f.family}
                </Link>
                <Bar value={fs.species_with_any_sequence} max={fs.species} />
                <span className="text-sm text-stone-600 sm:text-right">
                  {num(fs.species_with_any_sequence)} / {num(fs.species)} tür
                </span>
              </li>
            );
          })}
        </ul>
      </Card>

      {/* Navigation cards */}
      <SectionTitle>Neler yapabilirsiniz?</SectionTitle>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { href: "/turler", title: "Türleri keşfedin", text: "Latince veya Türkçe adla arayın, ENA/GenBank dizilerini ve en yakın akrabaları görün." },
          { href: "/agaclar", title: "Filogenetik ağaçlar", text: "Aile ve marker seçerek etkileşimli komşu birleştirme ağaçlarını inceleyin." },
          { href: "/veri-bosluklari", title: "Veri boşlukları", text: "Hangi türlerin ve cinslerin barkod verisi eksik?" },
          { href: "/dizi-ara", title: "Dizi arama", text: "Kendi DNA dizinizi yapıştırın, referans dizilerle karşılaştırın." },
        ].map((c) => (
          <Link key={c.href} href={c.href} className="group rounded-2xl border border-stone-200 bg-white p-5 shadow-sm transition hover:border-emerald-500 hover:shadow">
            <h3 className="font-semibold text-stone-900 group-hover:text-emerald-800">{c.title} →</h3>
            <p className="mt-2 text-sm text-stone-600">{c.text}</p>
          </Link>
        ))}
      </div>

      <p className="mt-10 text-sm text-stone-500">
        Tür listesi WCVP (Kew), diziler ENA/INSDC kayıtlarına dayanır; hatalı tanımlanmış kayıtlar içerebilir. Ayrıntılar için{" "}
        <Link className="underline" href="/yontem">Yöntem ve Sınırlar</Link> sayfasına bakın.
      </p>
    </div>
  );
}

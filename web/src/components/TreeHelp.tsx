import Term from "./Term";

/** Legend + "Nasıl okunur?" panel for the tree views (inline SVG sample drawn for this site). */
export default function TreeHelp({ defaultOpen = false }: { defaultOpen?: boolean }) {
  return (
    <details open={defaultOpen} className="mb-4 rounded-2xl border border-accent-line bg-accent-soft p-4">
      <summary className="flex min-h-11 items-center gap-2 font-semibold text-accent">
        <span aria-hidden>▸</span> Nasıl okunur? Ağaçtaki çizgiler ve renkler ne anlama geliyor?
      </summary>
      <div className="mt-3 grid gap-5 md:grid-cols-[minmax(0,17rem)_1fr]">
        <svg viewBox="0 0 270 150" className="w-full rounded-xl bg-surface" role="img" aria-label="Örnek ağaç: bir kök, iki düğüm, dört yaprak, bir ölçek çubuğu ve kırmızı ile işaretlenmiş seçili tür">
          <g fill="none" strokeWidth="2" strokeLinecap="round" style={{ stroke: "var(--tree-line)" }}>
            <path d="M12 75h30M42 75V40M42 75V110M42 40h50M42 110h30M92 40V25M92 40V55M72 110V97M72 110V123M92 25h60M92 55h90M72 97h110M72 123h70" />
          </g>
          <path d="M42 110h30M72 110V123M72 123h70" fill="none" strokeWidth="3" strokeLinecap="round" style={{ stroke: "var(--tree-hi)" }} />
          {[[152, 25], [182, 55], [182, 97], [142, 123]].map(([x, y], i) => (
            <circle key={i} cx={x} cy={y} r={i === 3 ? 5 : 3.5} style={{ fill: i === 3 ? "var(--tree-hi)" : "var(--st-600)" }} />
          ))}
          <g style={{ fill: "var(--st-700)" }} fontSize="9.5">
            <text x="160" y="28">yaprak</text><text x="190" y="58">yaprak</text><text x="190" y="100">yaprak</text>
            <text x="150" y="127" style={{ fill: "var(--tree-hi)" }} fontWeight="700">seçili tür</text>
            <text x="28" y="70">düğüm</text><text x="2" y="90">kök</text>
          </g>
          <path d="M20 142h50" stroke="var(--st-600)" strokeWidth="2" /><text x="76" y="145" fontSize="9.5" style={{ fill: "var(--st-700)" }}>ölçek çubuğu</text>
        </svg>
        <ul className="space-y-2 text-stone-800">
          <li><strong><Term id="dal-yaprak-dugum">Yaprak</Term>:</strong> ağacın ucundaki noktadır; bir DNA dizisini (bir kaydı) temsil eder ve yanında türün Latince adı yazar. Aynı türün birden çok dizisi varsa birden çok yaprağı olur.</li>
          <li><strong>Yakın dallar = benzer diziler.</strong> Aynı daldan ayrılan yapraklar, dizileri birbirine en çok benzeyen kayıtlardır. Bu, kesin bir akrabalık kanıtı değil, yalnızca bu kısa bölgeye göre bir ipucudur.</li>
          <li><strong>Renkler:</strong> yaprak renkleri <Term id="cins">cinsi</Term> gösterir (aynı cins aynı renk). <span className="font-semibold" style={{ color: "var(--tree-hi)" }}>Kırmızı</span> çizgi ve etiket, seçtiğiniz türdür.</li>
          <li><strong>Çizgi uzunluğu:</strong> <Term id="mesafeli-gorunum">Mesafeli görünümde</Term> yatay çizgilerin uzunluğu <Term id="p-mesafesi">genetik farkla</Term> orantılıdır; ölçek çubuğu belirli bir farkın uzunluğunu gösterir. <Term id="dallanma-duzeni">Dallanma düzeninde</Term> çizgiler eşit uzunlukta çizilir ve uzunluk bir anlam taşımaz; yalnızca kimin kiminle aynı daldan ayrıldığına bakın.</li>
          <li><strong>Klavye ve dokunmatik:</strong> ağacın üzerine odaklanıp ok tuşlarıyla türler arasında gezebilir, + / − ile yakınlaştırabilir, Enter ile türün sayfasını açabilirsiniz.</li>
        </ul>
      </div>
    </details>
  );
}

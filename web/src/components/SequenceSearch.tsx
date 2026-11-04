"use client";

import Link from "next/link";
import { useState } from "react";
import { loadReference } from "@/lib/data.client";
import { ncbiUrl, num, pct } from "@/lib/format";
import {
  MAX_QUERY_LENGTH,
  MIN_QUERY_LENGTH,
  TOP_N_MATCHES,
  cleanQuery,
  invalidCharacters,
  searchReference,
  type SearchHit,
} from "@/lib/seqsearch";
import { slugify } from "@/lib/text";

export default function SequenceSearch({ markers }: { markers: string[] }) {
  const [marker, setMarker] = useState(markers[0]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hits, setHits] = useState<SearchHit[] | null>(null);
  const [info, setInfo] = useState<{ queryLength: number; references: number; marker: string } | null>(null);

  const run = async () => {
    setError(null);
    setHits(null);
    const query = cleanQuery(text);
    if (query.length < MIN_QUERY_LENGTH) {
      setError(`Dizi çok kısa. En az ${MIN_QUERY_LENGTH} baz gerekli (şu an ${query.length}).`);
      return;
    }
    if (query.length > MAX_QUERY_LENGTH) {
      setError(`Dizi çok uzun. En fazla ${num(MAX_QUERY_LENGTH)} baz kabul edilir (şu an ${num(query.length)}).`);
      return;
    }
    const bad = invalidCharacters(query);
    if (bad.length > 0) {
      setError(`Geçersiz karakterler: ${bad.join(", ")}. Yalnızca DNA harfleri (A, C, G, T ve belirsiz kodlar) kullanın.`);
      return;
    }
    setBusy(true);
    try {
      const refs = await loadReference(marker);
      if (refs.length === 0) {
        setError(`${marker} için referans dizi yok.`);
        return;
      }
      const result = await searchReference(query, refs);
      setHits(result);
      setInfo({ queryLength: query.length, references: refs.length, marker });
    } catch {
      setError("Arama sırasında bir hata oluştu. Sayfayı yenileyip tekrar deneyin.");
    } finally {
      setBusy(false);
    }
  };

  const top = hits?.[0];

  return (
    <div>
      <div
        role="note"
        className="mb-6 rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900"
      >
        <strong>Uyarı:</strong> Sonuçlar yalnızca <em>gösterge niteliğindedir</em>, kesin tür tayini değildir.
        Referans veri ENA/INSDC kayıtlarından gelir ve hatalı tanımlanmış kayıtlar ya da eksik türler içerebilir. Yüksek
        benzerlik bile aynı cinsten yakın bir türle karışıklığı dışlamaz. Kesin tanı için uzman doğrulaması ve
        morfolojik inceleme gerekir.
      </div>

      <div className="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm">
        <label className="mb-1 block text-sm font-medium text-stone-700" htmlFor="seq">
          DNA dizisi (düz metin veya FASTA)
        </label>
        <textarea
          id="seq"
          rows={8}
          value={text}
          onChange={(e) => setText(e.target.value)}
          spellCheck={false}
          placeholder={">örnek\nATGAGTCGTAGGGAGGGACTTATGTCACCACAAACAGAGACTAAAGCAAGTG…"}
          className="w-full rounded-xl border border-stone-300 p-3 font-mono text-sm outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-200"
        />
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <label className="text-sm">
            Marker:{" "}
            <select value={marker} onChange={(e) => setMarker(e.target.value)} className="ml-1 rounded-lg border border-stone-300 bg-white px-3 py-2 text-sm">
              {markers.map((m) => <option key={m}>{m}</option>)}
            </select>
          </label>
          <button
            type="button"
            onClick={run}
            disabled={busy || text.trim() === ""}
            className="rounded-xl bg-emerald-700 px-5 py-2.5 font-medium text-white hover:bg-emerald-800 disabled:opacity-50"
          >
            {busy ? "Aranıyor…" : "Karşılaştır"}
          </button>
          <span className="text-sm text-stone-500">Dizi tarayıcınızda işlenir, sunucuya gönderilmez.</span>
        </div>
        {error && <p role="alert" className="mt-3 text-sm text-red-700">{error}</p>}
      </div>

      {hits && info && (
        <div className="mt-8">
          <h2 className="text-2xl font-semibold">En iyi {TOP_N_MATCHES} eşleşme ({info.marker})</h2>
          <p className="mb-3 mt-1 text-sm text-stone-500">
            {num(info.references)} referans diziyle karşılaştırıldı; sorgu uzunluğu {num(info.queryLength)} baz.
          </p>
          {hits.length === 0 ? (
            <p className="text-stone-600">Benzer bir referans dizi bulunamadı.</p>
          ) : (
            <>
              <div className="overflow-x-auto rounded-xl border border-stone-200 bg-white">
                <table className="w-full text-sm">
                  <thead className="bg-stone-50 text-left text-stone-600">
                    <tr>
                      <th className="p-3">#</th>
                      <th className="p-3">Tür</th>
                      <th className="p-3">Erişim no</th>
                      <th className="p-3 text-right">Benzerlik</th>
                      <th className="hidden p-3 text-right sm:table-cell">Örtüşme (baz)</th>
                      <th className="hidden p-3 text-right sm:table-cell">Sorgu kapsaması</th>
                    </tr>
                  </thead>
                  <tbody>
                    {hits.map((h, i) => (
                      <tr key={h.accession} className="border-t border-stone-100">
                        <td className="p-3 text-stone-500">{i + 1}</td>
                        <td className="p-3">
                          <Link href={`/turler/${slugify(h.species)}`} className="italic text-emerald-800 hover:underline">{h.species}</Link>
                          {h.reverseComplement && <span className="ml-2 text-xs text-stone-500">(ters tamamlayıcı)</span>}
                        </td>
                        <td className="p-3">
                          <a href={ncbiUrl(h.accession)} target="_blank" rel="noreferrer" className="font-mono text-emerald-800 underline">{h.accession}</a>
                        </td>
                        <td className="p-3 text-right font-semibold">{pct(h.identity)}</td>
                        <td className="hidden p-3 text-right sm:table-cell">{num(h.alignedLength)}</td>
                        <td className="hidden p-3 text-right sm:table-cell">{pct(h.queryCoverage, 0)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {top && hits.filter((h) => h.identity === top.identity && h.species !== top.species).length > 0 && (
                <p className="mt-3 rounded-lg bg-amber-50 p-3 text-sm text-amber-900">
                  En iyi benzerliği birden fazla tür paylaşıyor; bu barkod bölgesi bu türleri ayırt etmeye yetmiyor olabilir.
                </p>
              )}
              <p className="mt-3 text-sm text-stone-500">
                Benzerlik = eşleşen baz sayısı / hizalanan sütun sayısı (örtüşen bölgede). Sonuçlar gösterge niteliğindedir.
              </p>
            </>
          )}
        </div>
      )}
    </div>
  );
}

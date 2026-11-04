"use client";

import { useState } from "react";
import { enaUrl, ncbiUrl } from "@/lib/format";
import type { SequenceRecord } from "@/lib/types";

const LINE = 60; // bases per line
const GROUP = 10; // bases per group

/** FASTA text for a list of records (70 columns, like NCBI). */
export function toFasta(species: string, marker: string, records: SequenceRecord[]): string {
  return records
    .map((r) => {
      const lines = r.sequence.match(/.{1,70}/g) ?? [];
      return `>${r.accession} ${species} [${marker}]${r.is_turkey === 1 ? " Turkey" : ""}\n${lines.join("\n")}\n`;
    })
    .join("");
}

function download(filename: string, text: string) {
  const url = URL.createObjectURL(new Blob([text], { type: "text/plain" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function ColoredSequence({ sequence }: { sequence: string }) {
  const lines: { start: number; text: string }[] = [];
  for (let i = 0; i < sequence.length; i += LINE) lines.push({ start: i, text: sequence.slice(i, i + LINE) });
  return (
    <pre className="max-h-96 overflow-auto rounded-lg bg-stone-50 p-3 font-mono text-xs leading-5">
      {lines.map((l) => (
        <div key={l.start}>
          <span className="inline-block w-12 select-none pr-2 text-right text-stone-400">{l.start + 1}</span>
          {(l.text.match(new RegExp(`.{1,${GROUP}}`, "g")) ?? []).map((g, gi) => (
            <span key={gi} className="mr-2">
              {g.split("").map((c, ci) => (
                <span key={ci} className={`nt-${"ACGT".includes(c) ? c : "N"}`}>
                  {c}
                </span>
              ))}
            </span>
          ))}
        </div>
      ))}
    </pre>
  );
}

export default function SequenceViewer({
  species,
  marker,
  records,
}: {
  species: string;
  marker: string;
  records: SequenceRecord[];
}) {
  const [open, setOpen] = useState<string | null>(null);

  if (records.length === 0) {
    return <p className="text-stone-500">Bu marker için filtreyi geçen dizi bulunamadı.</p>;
  }
  const base = species.replace(/\s+/g, "_");

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm text-stone-600">{records.length} dizi</p>
        <button
          type="button"
          className="rounded-lg border border-emerald-600 px-3 py-1.5 text-sm font-medium text-emerald-800 hover:bg-emerald-50"
          onClick={() => download(`${base}_${marker}.fasta`, toFasta(species, marker, records))}
        >
          Tümünü FASTA olarak indir
        </button>
      </div>
      <ul className="divide-y divide-stone-200 rounded-xl border border-stone-200">
        {records.map((r) => (
          <li key={r.accession} className="p-3">
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
              <a
                href={ncbiUrl(r.accession)}
                target="_blank"
                rel="noreferrer"
                className="font-mono text-sm font-semibold text-emerald-800 underline"
              >
                {r.accession}
              </a>
              <span className="text-xs text-stone-500">
                <a className="underline" href={enaUrl(r.accession)} target="_blank" rel="noreferrer">ENA</a>
                {" · "}
                <a className="underline" href={ncbiUrl(r.accession)} target="_blank" rel="noreferrer">GenBank</a>
              </span>
              {r.is_turkey === 1 && (
                <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-800">Türkiye örneği</span>
              )}
              {r.matched_via === "synonym" && (
                <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-900" title="Kayıtta eş ad (synonym) kullanılmış">eş ad</span>
              )}
              <span className="text-sm text-stone-600">{r.length} bp</span>
              {r.country && <span className="text-sm text-stone-500">{r.country}</span>}
              <span className="ml-auto flex gap-2">
                <button
                  type="button"
                  className="rounded-md bg-stone-100 px-2.5 py-1 text-sm hover:bg-stone-200"
                  onClick={() => setOpen(open === r.accession ? null : r.accession)}
                  aria-expanded={open === r.accession}
                >
                  {open === r.accession ? "Gizle" : "Diziyi göster"}
                </button>
                <button
                  type="button"
                  className="rounded-md bg-stone-100 px-2.5 py-1 text-sm hover:bg-stone-200"
                  onClick={() => download(`${r.accession}.fasta`, toFasta(species, marker, [r]))}
                >
                  FASTA
                </button>
              </span>
            </div>
            <p className="mt-1 text-sm text-stone-600">{r.source_title || r.definition}</p>
            {open === r.accession && (
              <div className="mt-2">
                <ColoredSequence sequence={r.sequence} />
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

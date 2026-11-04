// Plain-language sentences generated from the data (no hard-coded figures).
// Turkish suffixes after numbers are avoided on purpose ("... tanesini", "... türün ... tanesi").
import { num, pct } from "./format";

/** "Değerlendirilen her 100 türden yaklaşık 61 tanesini ... (N tür üzerinden)". rate is 0..1. */
export function per100(rate: number | null | undefined): string {
  if (rate === null || rate === undefined) return "—";
  return num(Math.round(rate * 100));
}

export function speciesRateSentence(rate: number | null | undefined, evaluated: number, what = "birbirinden ayırabiliyor"): string {
  if (rate === null || rate === undefined || evaluated === 0) return "Bu bölge için değerlendirilebilen tür yok.";
  return `Değerlendirilen her 100 türden yaklaşık ${per100(rate)} tanesini ${what} (${num(evaluated)} tür üzerinden, ${pct(rate)}).`;
}

export function sequenceRateSentence(rate: number | null | undefined, evaluated: number): string {
  if (rate === null || rate === undefined || evaluated === 0) return "Değerlendirilebilen dizi yok.";
  return `Değerlendirilen her 100 diziden yaklaşık ${per100(rate)} tanesinde en yakın akraba dizi aynı türe ait çıkıyor (${num(evaluated)} dizi üzerinden, ${pct(rate)}).`;
}

/** Coverage sentence: "N türün M tanesinin ... " */
export function shareSentence(part: number, total: number, subject: string, predicate: string): string {
  if (total === 0) return "";
  return `${num(total)} ${subject} içinde ${num(part)} tanesi ${predicate} (${pct(part / total)}).`;
}

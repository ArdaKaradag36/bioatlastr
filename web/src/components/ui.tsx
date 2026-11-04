// Small presentational components shared by several pages (server-safe).
import Link from "next/link";
import type { ReactNode } from "react";
import { InfoIcon, TargetIcon } from "./Icons";
import Term from "./Term";

export function PageTitle({ title, eyebrow, children }: { title: string; eyebrow?: string; children?: ReactNode }) {
  return (
    <div className="rise mb-6">
      {eyebrow && <p className="mb-2 text-sm font-semibold uppercase tracking-wider text-link">{eyebrow}</p>}
      <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">{title}</h1>
      {children && <p className="mt-3 max-w-3xl text-lg text-stone-600">{children}</p>}
    </div>
  );
}

/** "Bu sayfa ne gösterir?" (+ optional "Nasıl okunur?") box that opens every page. */
export function PageIntro({ what, how }: { what: ReactNode; how?: ReactNode }) {
  return (
    <section aria-label="Sayfa özeti" className={`rise-2 mb-10 grid gap-4 ${how ? "lg:grid-cols-2" : ""}`}>
      <div className="rounded-2xl border border-accent-line bg-accent-soft p-5">
        <h2 className="mb-1 flex items-center gap-2 font-sans text-base font-semibold text-accent">
          <InfoIcon width={20} height={20} /> Bu sayfa ne gösterir?
        </h2>
        <div className="text-stone-800">{what}</div>
      </div>
      {how && (
        <div className="rounded-2xl border border-accent-line bg-surface p-5">
          <h2 className="mb-1 flex items-center gap-2 font-sans text-base font-semibold text-accent">
            <CompassSmall /> Nasıl okunur?
          </h2>
          <div className="text-stone-800">{how}</div>
        </div>
      )}
    </section>
  );
}
function CompassSmall() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <circle cx="12" cy="12" r="9" /><path d="M15.5 8.5l-2 5-5 2 2-5z" />
    </svg>
  );
}

/** Closing line of a page that ties it back to the project goal ("Amacımız"). */
export function Purpose({ children }: { children: ReactNode }) {
  return (
    <aside className="mt-14 flex gap-3 rounded-2xl bg-forest p-5 text-on-dark">
      <TargetIcon width={26} height={26} className="mt-0.5 shrink-0 text-leaf" />
      <p className="text-base leading-relaxed">
        <strong className="font-semibold">Amacımız: </strong>
        {children}{" "}
        <Link className="font-medium text-on-dark underline" href="/yontem">Yöntemi okuyun</Link>
      </p>
    </aside>
  );
}

export function Callout({ children, tone = "info" }: { children: ReactNode; tone?: "info" | "warn" }) {
  const cls = tone === "warn" ? "border-amber-300 bg-amber-50 text-amber-900" : "border-accent-line bg-accent-soft text-stone-800";
  return <div role="note" className={`rounded-xl border p-4 text-sm leading-relaxed ${cls}`}>{children}</div>;
}

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div className={`rounded-2xl border border-stone-200 bg-white p-5 shadow-card ${className}`}>
      {children}
    </div>
  );
}

export function StatCard({
  label,
  value,
  note,
  meaning,
}: {
  label: ReactNode;
  value: ReactNode;
  note?: ReactNode;
  /** one plain sentence that says what the number means */
  meaning?: ReactNode;
}) {
  return (
    <Card className="lift">
      <div className="text-sm font-semibold text-stone-600">{label}</div>
      <div className="mt-1 font-serif text-4xl font-bold text-link">{value}</div>
      {note && <div className="mt-1 text-sm text-stone-600">{note}</div>}
      {meaning && <p className="mt-2 border-t border-stone-100 pt-2 text-sm text-stone-700">{meaning}</p>}
    </Card>
  );
}

export function SectionTitle({ children, id }: { children: ReactNode; id?: string }) {
  return (
    <h2 id={id} className="mb-4 mt-14 scroll-mt-24 text-2xl font-semibold sm:text-3xl">
      {children}
    </h2>
  );
}

/** Horizontal stacked bar. Segments are drawn proportional to their values. */
export function StackedBar({
  segments,
}: {
  segments: { label: string; value: number; color: string }[];
}) {
  const total = segments.reduce((a, s) => a + s.value, 0);
  return (
    <div
      className="flex h-6 w-full overflow-hidden rounded-full bg-stone-100"
      role="img"
      aria-label={segments.map((s) => `${s.label}: ${s.value.toLocaleString("tr-TR")}`).join(", ")}
    >
      {segments.map((s) =>
        s.value > 0 ? (
          <div
            key={s.label}
            title={`${s.label}: ${s.value.toLocaleString("tr-TR")}`}
            style={{ width: `${(s.value / total) * 100}%`, backgroundColor: s.color }}
          />
        ) : null,
      )}
    </div>
  );
}

export function Legend({ items }: { items: { label: string; color: string }[] }) {
  return (
    <ul className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-stone-600" aria-label="Renk açıklaması">
      {items.map((i) => (
        <li key={i.label} className="flex items-center gap-1.5">
          <span aria-hidden className="inline-block h-3 w-3 rounded-sm" style={{ backgroundColor: i.color }} />
          {i.label}
        </li>
      ))}
    </ul>
  );
}

/** Single horizontal bar (value / max). */
export function Bar({ value, max, color = "var(--cov-two)", label }: { value: number; max: number; color?: string; label?: string }) {
  return (
    <div className="h-3 w-full rounded-full bg-stone-100" role="img" aria-label={label ?? `${value.toLocaleString("tr-TR")} / ${max.toLocaleString("tr-TR")}`}>
      <div className="h-3 rounded-full" style={{ width: `${max > 0 ? (value / max) * 100 : 0}%`, backgroundColor: color }} />
    </div>
  );
}

export const COVERAGE_COLORS = {
  zero: "var(--cov-zero)",
  one: "var(--cov-one)",
  twoPlus: "var(--cov-two)",
};

/** Latin scientific name in italics; `note` adds the small "(Latince bilimsel ad)" hint at first appearance. */
export function Latin({ children, note = false }: { children: ReactNode; note?: boolean }) {
  return (
    <>
      <i className="latin">{children}</i>
      {note && <span className="ml-1 text-sm not-italic text-stone-500">(<Term id="latince-ad">Latince bilimsel ad</Term>)</span>}
    </>
  );
}

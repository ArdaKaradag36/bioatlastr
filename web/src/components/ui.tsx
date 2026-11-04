// Small presentational components shared by several pages (server-safe).
import type { ReactNode } from "react";

export function PageTitle({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="mb-8">
      <h1 className="text-3xl font-bold tracking-tight text-stone-900 sm:text-4xl">{title}</h1>
      {children && <p className="mt-3 max-w-3xl text-lg text-stone-600">{children}</p>}
    </div>
  );
}

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div className={`rounded-2xl border border-stone-200 bg-white p-5 shadow-sm ${className}`}>
      {children}
    </div>
  );
}

export function StatCard({
  label,
  value,
  note,
}: {
  label: string;
  value: ReactNode;
  note?: ReactNode;
}) {
  return (
    <Card>
      <div className="text-sm font-medium text-stone-500">{label}</div>
      <div className="mt-1 text-3xl font-bold text-emerald-800">{value}</div>
      {note && <div className="mt-1 text-sm text-stone-500">{note}</div>}
    </Card>
  );
}

export function SectionTitle({ children, id }: { children: ReactNode; id?: string }) {
  return (
    <h2 id={id} className="mb-4 mt-12 text-2xl font-semibold text-stone-900">
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
      aria-label={segments.map((s) => `${s.label}: ${s.value}`).join(", ")}
    >
      {segments.map((s) =>
        s.value > 0 ? (
          <div
            key={s.label}
            title={`${s.label}: ${s.value}`}
            style={{ width: `${(s.value / total) * 100}%`, backgroundColor: s.color }}
          />
        ) : null,
      )}
    </div>
  );
}

export function Legend({ items }: { items: { label: string; color: string }[] }) {
  return (
    <ul className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-stone-600">
      {items.map((i) => (
        <li key={i.label} className="flex items-center gap-1.5">
          <span className="inline-block h-3 w-3 rounded-sm" style={{ backgroundColor: i.color }} />
          {i.label}
        </li>
      ))}
    </ul>
  );
}

/** Single horizontal bar (value / max). */
export function Bar({ value, max, color = "#059669" }: { value: number; max: number; color?: string }) {
  return (
    <div className="h-3 w-full rounded-full bg-stone-100">
      <div
        className="h-3 rounded-full"
        style={{ width: `${max > 0 ? (value / max) * 100 : 0}%`, backgroundColor: color }}
      />
    </div>
  );
}

export const COVERAGE_COLORS = {
  zero: "#d6d3d1",
  one: "#fbbf24",
  twoPlus: "#059669",
};

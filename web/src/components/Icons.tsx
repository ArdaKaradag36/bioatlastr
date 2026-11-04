// Small inline SVG icons and illustrations drawn for this project (no external images).
// All are decorative (aria-hidden) unless a title is given.
import type { SVGProps } from "react";

type P = SVGProps<SVGSVGElement>;
const base = (p: P) => ({ width: 24, height: 24, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round" as const, strokeLinejoin: "round" as const, "aria-hidden": true, ...p });

export const LeafIcon = (p: P) => (
  <svg {...base(p)}><path d="M5 19C5 10 10 5 20 4c0 10-4 15-13 15" /><path d="M5 19c2-5 5-8 9-10" /></svg>
);
export const DnaIcon = (p: P) => (
  <svg {...base(p)}><path d="M7 3c0 6 10 6 10 12s-10 6-10 6" /><path d="M17 3c0 6-10 6-10 12s10 6 10 6" /><path d="M8.5 7h7M8.5 17h7M7.3 12h9.4" /></svg>
);
export const TreeIcon = (p: P) => (
  <svg {...base(p)}><path d="M3 12h4m0 0V6m0 6v6M7 6h5m-5 12h5m0-12V4m0 2v2m0 8v2m0 2v2" /><circle cx="14" cy="4" r="1.2" /><circle cx="14" cy="8" r="1.2" /><circle cx="14" cy="16" r="1.2" /><circle cx="14" cy="20" r="1.2" /><path d="M14 4h6M14 8h6M14 16h6M14 20h6" /></svg>
);
export const ListIcon = (p: P) => (
  <svg {...base(p)}><path d="M9 6h11M9 12h11M9 18h11" /><circle cx="4.5" cy="6" r="1" /><circle cx="4.5" cy="12" r="1" /><circle cx="4.5" cy="18" r="1" /></svg>
);
export const SearchIcon = (p: P) => (
  <svg {...base(p)}><circle cx="11" cy="11" r="6.5" /><path d="M16 16l4.5 4.5" /></svg>
);
export const BookIcon = (p: P) => (
  <svg {...base(p)}><path d="M4 5.5C4 4.7 4.7 4 5.5 4H11v15H5.5C4.7 19 4 18.3 4 17.5z" /><path d="M20 5.5c0-.8-.7-1.5-1.5-1.5H13v15h5.5c.8 0 1.5-.7 1.5-1.5z" /></svg>
);
export const GapIcon = (p: P) => (
  <svg {...base(p)}><rect x="3.5" y="4.5" width="17" height="15" rx="2.5" /><path d="M3.5 10h17M9.5 4.5v15" strokeDasharray="2 2.5" /></svg>
);
export const TargetIcon = (p: P) => (
  <svg {...base(p)}><circle cx="12" cy="12" r="8" /><circle cx="12" cy="12" r="3.5" /></svg>
);
export const ShieldIcon = (p: P) => (
  <svg {...base(p)}><path d="M12 3l7 3v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6z" /><path d="M9 12l2 2 4-4" /></svg>
);
export const InfoIcon = (p: P) => (
  <svg {...base(p)}><circle cx="12" cy="12" r="9" /><path d="M12 11v5M12 7.7v.1" /></svg>
);
export const CompassIcon = (p: P) => (
  <svg {...base(p)}><circle cx="12" cy="12" r="9" /><path d="M15.5 8.5l-2 5-5 2 2-5z" /></svg>
);

/** The project mark: a leaf whose midrib is a DNA ladder. */
export function Logo({ size = 36 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" aria-hidden>
      <rect width="48" height="48" rx="12" fill="var(--forest)" />
      <path d="M12 36C12 21 21 12 38 10c0 17-8 26-23 26" fill="var(--leaf)" />
      <path d="M13 35c5-9 11-15 19-19" stroke="var(--forest)" strokeWidth="2.2" strokeLinecap="round" fill="none" />
      <path d="M19 28.5l3-3M24 24l3-3M28.5 19.5l2.5-2.5" stroke="#fff" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

/** Hero illustration: a DNA strand flowing into a small tree diagram. */
export function HeroArt() {
  return (
    <svg viewBox="0 0 420 300" className="h-auto w-full" role="img" aria-label="Çizim: bir DNA zinciri ve ondan çıkan akrabalık ağacı">
      <defs>
        <linearGradient id="hg" x1="0" x2="1"><stop offset="0" stopColor="#7fd49a" /><stop offset="1" stopColor="#3d9a55" /></linearGradient>
      </defs>
      <g opacity="0.95">
        {Array.from({ length: 11 }, (_, i) => {
          const x = 24 + i * 15; const a = Math.sin(i * 0.62) * 34;
          return (
            <g key={i}>
              <line x1={x} y1={70 + a} x2={x} y2={70 - a} stroke="#cfe8d6" strokeWidth="2" opacity="0.7" />
              <circle cx={x} cy={70 + a} r="4.5" fill="url(#hg)" />
              <circle cx={x} cy={70 - a} r="4.5" fill="#8dbdf0" />
            </g>
          );
        })}
      </g>
      <path d="M205 70h30" stroke="#cfe8d6" strokeWidth="2" strokeDasharray="4 5" />
      <g stroke="#8dbdf0" strokeWidth="2.4" fill="none" strokeLinecap="round">
        <path d="M250 70h26M276 70V30M276 70V110M276 30h40M276 110h30M316 30V12M316 30V48M306 110V92M306 110V128" />
        <path d="M316 12h50M316 48h60M306 92h58M306 128h70" />
      </g>
      {[[366, 12], [376, 48], [364, 92], [376, 128]].map(([x, y], i) => <circle key={i} cx={x} cy={y} r="5" fill="#7fd49a" />)}
      <g fill="#e8f4ea" fontSize="12" fontStyle="italic">
        <text x="380" y="16">tür A</text><text x="388" y="52">tür B</text><text x="372" y="96">tür C</text><text x="388" y="132">tür D</text>
      </g>
      <g transform="translate(40 190)">
        <path d="M0 80C0 30 40 0 130 -6c0 70-38 98-100 98" fill="#2f7a4a" opacity="0.9" />
        <path d="M6 86c26-40 56-66 100-84" stroke="#0f3d24" strokeWidth="3" fill="none" strokeLinecap="round" />
        <path d="M30 70l22-22M50 54l22-22M70 40l16-16" stroke="#cfe8d6" strokeWidth="2" strokeLinecap="round" />
      </g>
      <text x="200" y="262" fill="#cfe8d6" fontSize="14">Kısa bir DNA bölümü, bitkiyi tanımak için ipucu verir.</text>
    </svg>
  );
}

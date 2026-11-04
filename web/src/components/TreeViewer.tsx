"use client";

// Interactive rectangular tree (D3 zoom + pan, drawn with plain SVG).
// Big trees stay fast because only the leaves inside the viewport get dots/labels.

import Link from "next/link";
import { useRouter } from "next/navigation";
import { select } from "d3-selection";
import { zoom, zoomIdentity, type D3ZoomEvent, type ZoomBehavior } from "d3-zoom";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { distancePct } from "@/lib/format";
import { layoutTree, parseLeafLabel, parseNewick } from "@/lib/newick";
import { slugify } from "@/lib/text";
import type { TreeFile } from "@/lib/types";

const TREE_W = 520; // drawing width of the tree in SVG units
const LABEL_W = 240; // space reserved for leaf labels
const ROW_H = 14;
const HIGHLIGHT = "#dc2626";

interface Props {
  tree: TreeFile;
  /** Latin name of the species to highlight (root-to-leaf path + label). */
  highlight?: string | null;
  height?: number;
  /** Wheel zooms only while Ctrl is held (so the page can still scroll). */
  lockWheel?: boolean;
  /** Called when a leaf is clicked; without it, a click opens the species page. */
  onSelectSpecies?: (species: string) => void;
}

function genusColor(genus: string): string {
  let h = 0;
  for (let i = 0; i < genus.length; i++) h = (h * 31 + genus.charCodeAt(i)) % 360;
  return `hsl(${h}, 55%, 36%)`;
}

/** 1, 2 or 5 times a power of ten that is <= value */
function niceNumber(value: number): number {
  const p = Math.pow(10, Math.floor(Math.log10(value)));
  const f = value / p;
  return (f >= 5 ? 5 : f >= 2 ? 2 : 1) * p;
}

export default function TreeViewer({ tree, highlight, height = 520, lockWheel = false, onSelectSpecies }: Props) {
  const router = useRouter();
  const containerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const zoomRef = useRef<ZoomBehavior<SVGSVGElement, unknown> | null>(null);
  const [width, setWidth] = useState(0);
  // big trees start as a cladogram: one long branch would otherwise squash all other branches into a line
  const [mode, setMode] = useState<"phylogram" | "cladogram">(tree.n_leaves > 100 ? "cladogram" : "phylogram");
  const [modeFor, setModeFor] = useState(tree);
  if (modeFor !== tree) {
    setModeFor(tree);
    setMode(tree.n_leaves > 100 ? "cladogram" : "phylogram");
  }
  const [t, setT] = useState({ x: 0, y: 0, k: 1 });
  const [hover, setHover] = useState<number | null>(null);
  const size = { w: width, h: height };

  // ---- layout ---------------------------------------------------------
  const root = useMemo(() => parseNewick(tree.newick), [tree.newick]);
  const layout = useMemo(() => layoutTree(root, mode, TREE_W, ROW_H), [root, mode]);
  const leafInfo = useMemo(
    () => layout.leaves.map((i) => parseLeafLabel(layout.nodes[i].node.name)),
    [layout],
  );

  const branches = useMemo(() => {
    const parts: string[] = [];
    const minY = new Map<number, number>();
    const maxY = new Map<number, number>();
    layout.nodes.forEach((n) => {
      if (n.parent < 0) return;
      const p = layout.nodes[n.parent];
      parts.push(`M${p.x.toFixed(1)},${n.y.toFixed(1)}H${n.x.toFixed(1)}`);
      minY.set(n.parent, Math.min(minY.get(n.parent) ?? Infinity, n.y));
      maxY.set(n.parent, Math.max(maxY.get(n.parent) ?? -Infinity, n.y));
    });
    minY.forEach((y0, idx) => {
      const x = layout.nodes[idx].x.toFixed(1);
      parts.push(`M${x},${y0.toFixed(1)}V${maxY.get(idx)!.toFixed(1)}`);
    });
    return parts.join("");
  }, [layout]);

  const highlightRows = useMemo(
    () => leafInfo.map((l, i) => (highlight && l.species === highlight ? i : -1)).filter((i) => i >= 0),
    [leafInfo, highlight],
  );
  const highlightSet = useMemo(() => new Set(highlightRows), [highlightRows]);

  const highlightPath = useMemo(() => {
    const parts: string[] = [];
    const seen = new Set<number>();
    for (const row of highlightRows) {
      let idx = layout.leaves[row];
      while (idx >= 0 && !seen.has(idx)) {
        seen.add(idx);
        const n = layout.nodes[idx];
        if (n.parent < 0) break;
        const p = layout.nodes[n.parent];
        parts.push(`M${p.x.toFixed(1)},${p.y.toFixed(1)}V${n.y.toFixed(1)}H${n.x.toFixed(1)}`);
        idx = n.parent;
      }
    }
    return parts.join("");
  }, [highlightRows, layout]);

  // ---- size observer ----------------------------------------------------
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver((entries) => setWidth(Math.floor(entries[0].contentRect.width)));
    ro.observe(el);
    setWidth(Math.floor(el.getBoundingClientRect().width));
    return () => ro.disconnect();
  }, []);

  // ---- zoom behaviour -----------------------------------------------------
  const ready = width > 0;
  useEffect(() => {
    const el = svgRef.current;
    if (!el) return;
    const z = zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.002, 80])
      .filter((e: Event) => {
        const ev = e as WheelEvent & MouseEvent;
        if (e.type === "wheel") return lockWheel ? ev.ctrlKey || ev.metaKey : true;
        return !ev.button && (!ev.ctrlKey || e.type === "wheel");
      })
      .on("zoom", (e: D3ZoomEvent<SVGSVGElement, unknown>) =>
        setT({ x: e.transform.x, y: e.transform.y, k: e.transform.k }),
      );
    select(el).call(z);
    zoomRef.current = z;
    return () => {
      select(el).on(".zoom", null);
    };
  }, [lockWheel, ready]);

  const apply = useCallback((x: number, y: number, k: number) => {
    if (!svgRef.current || !zoomRef.current) return;
    select(svgRef.current).call(zoomRef.current.transform, zoomIdentity.translate(x, y).scale(k));
  }, []);

  const fit = useCallback(() => {
    const w = TREE_W + LABEL_W + 20;
    const h = layout.leaves.length * ROW_H + 20;
    const k = Math.min(Math.max(Math.min(size.w / w, size.h / h), 0.002), 2);
    apply((size.w - w * k) / 2 + 10 * k, (size.h - h * k) / 2 + 10 * k, k);
  }, [layout, size.w, size.h, apply]);

  const focusHighlight = useCallback(() => {
    if (highlightRows.length === 0) return;
    const n = layout.nodes[layout.leaves[highlightRows[0]]];
    const k = 1.2;
    apply(size.w * 0.55 - k * n.x, size.h / 2 - k * n.y, k);
  }, [highlightRows, layout, size.w, size.h, apply]);

  // first view: show everything (small trees) or jump to the highlighted species (big trees)
  useEffect(() => {
    if (!ready || !zoomRef.current) return;
    if (highlightRows.length > 0 && layout.leaves.length > 40) focusHighlight();
    else fit();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, layout, highlight]);

  // ---- what is visible ------------------------------------------------------
  const n = layout.leaves.length;
  const i0 = Math.max(0, Math.floor(-t.y / t.k / ROW_H) - 1);
  const i1 = Math.min(n - 1, Math.ceil((size.h - t.y) / t.k / ROW_H) + 1);
  const rowPx = ROW_H * t.k;
  const showDots = rowPx >= 3.5;
  const showLabels = rowPx >= 7;
  const showAccession = rowPx >= 11;

  const onLeafClick = (species: string) => {
    if (onSelectSpecies) onSelectSpecies(species);
    else router.push(`/turler/${slugify(species)}`);
  };

  const shown = hover ?? highlightRows[0] ?? null;
  const shownInfo = shown !== null ? leafInfo[shown] : null;

  // scale bar (only meaningful when branch lengths are drawn)
  const scaleUnits = niceNumber(((80 / t.k / TREE_W) * layout.span) || 0.0001);
  const scalePx = layout.usesLengths ? (scaleUnits / layout.span) * TREE_W * t.k : 0;

  const btn =
    "rounded-lg border border-stone-300 bg-white/95 px-2.5 py-1.5 text-sm font-medium text-stone-700 shadow-sm hover:bg-stone-50";

  return (
    <div ref={containerRef} className="relative overflow-hidden rounded-2xl border border-stone-200 bg-white" style={{ height }}>
      {ready && (
        <svg
          ref={svgRef}
          width={size.w}
          height={size.h}
          className="block cursor-grab touch-none select-none active:cursor-grabbing"
          role="img"
          aria-label={`${tree.family} ${tree.marker} ağacı, ${tree.n_leaves} dizi`}
        >
          <g transform={`translate(${t.x},${t.y}) scale(${t.k})`}>
            <path d={branches} className="tree-line" fill="none" stroke="#a8a29e" strokeWidth={1} />
            {highlightPath && (
              <path d={highlightPath} className="tree-line" fill="none" stroke={HIGHLIGHT} strokeWidth={2.4} />
            )}
            {(showDots || showLabels) &&
              Array.from({ length: Math.max(0, i1 - i0 + 1) }, (_, d) => i0 + d).map((i) => {
                const node = layout.nodes[layout.leaves[i]];
                const info = leafInfo[i];
                const isHi = highlightSet.has(i);
                const color = genusColor(info.species.split(" ")[0]);
                return (
                  <g
                    key={i}
                    className="cursor-pointer"
                    onMouseEnter={() => setHover(i)}
                    onMouseLeave={() => setHover(null)}
                    onClick={() => onLeafClick(info.species)}
                  >
                    {isHi && (
                      <rect x={node.x - 4} y={node.y - ROW_H / 2} width={LABEL_W} height={ROW_H} rx={3} fill="#fee2e2" />
                    )}
                    <rect x={node.x - 4} y={node.y - ROW_H / 2} width={LABEL_W} height={ROW_H} fill="transparent" />
                    {showDots && <circle cx={node.x} cy={node.y} r={isHi ? 5 : 2.6} fill={isHi ? HIGHLIGHT : color} />}
                    {showLabels && (
                      <text x={node.x + 8} y={node.y + 4} fontSize={11} fill={isHi ? HIGHLIGHT : color} fontWeight={isHi ? 700 : 400}>
                        <tspan fontStyle="italic">{info.species}</tspan>
                        {showAccession && (
                          <tspan dx={4} fontSize={9} fill="#a8a29e">
                            {info.accession}
                          </tspan>
                        )}
                      </text>
                    )}
                  </g>
                );
              })}
          </g>
        </svg>
      )}

      {/* info box */}
      <div className="pointer-events-none absolute left-2 top-2 max-w-[70%] rounded-lg bg-white/95 px-3 py-1.5 text-sm shadow-sm">
        {shownInfo ? (
          <span className="pointer-events-auto">
            <Link href={`/turler/${slugify(shownInfo.species)}`} className="font-medium italic text-emerald-800 hover:underline">
              {shownInfo.species}
            </Link>{" "}
            <span className="text-stone-500">{shownInfo.accession}</span>
          </span>
        ) : (
          <span className="text-stone-500">
            {tree.n_leaves} dizi · {tree.n_species} tür
          </span>
        )}
      </div>

      {/* controls */}
      <div className="absolute right-2 top-2 flex flex-wrap justify-end gap-1.5">
        <button type="button" className={btn} aria-label="Yakınlaştır" onClick={() => svgRef.current && zoomRef.current && select(svgRef.current).call(zoomRef.current.scaleBy, 1.6)}>
          +
        </button>
        <button type="button" className={btn} aria-label="Uzaklaştır" onClick={() => svgRef.current && zoomRef.current && select(svgRef.current).call(zoomRef.current.scaleBy, 1 / 1.6)}>
          −
        </button>
        <button type="button" className={btn} onClick={fit}>
          Sığdır
        </button>
        {highlightRows.length > 0 && (
          <button type="button" className={btn} onClick={focusHighlight}>
            Türe git
          </button>
        )}
        {layout.hasBranchLengths && (
          <button type="button" className={btn} onClick={() => setMode((m) => (m === "phylogram" ? "cladogram" : "phylogram"))}>
            {mode === "phylogram" ? "Dallanma düzeni" : "Mesafeli görünüm"}
          </button>
        )}
      </div>

      {/* scale bar + hint */}
      <div className="pointer-events-none absolute bottom-2 left-2 text-xs text-stone-500">
        {layout.usesLengths && scalePx > 0 && (
          <div className="mb-1">
            <div className="h-1.5 border-x border-b border-stone-500" style={{ width: scalePx }} />
            {distancePct(scaleUnits)} p-mesafe
          </div>
        )}
        {lockWheel ? "Kaydır: sürükle · Yakınlaştır: Ctrl + tekerlek veya +/−" : "Sürükle: kaydır · Tekerlek: yakınlaştır"}
      </div>
    </div>
  );
}

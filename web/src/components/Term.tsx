"use client";

// Inline glossary help: dotted underline + popover (hover, keyboard, touch) with a short explanation and a link to /sozluk#id.
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useCallback, useEffect, useId, useRef, useState, type ReactNode } from "react";
import { GLOSSARY_BY_ID } from "@/lib/glossary";

const seenByPage = new Map<string, Set<string>>();

export default function Term({ id, children }: { id: string; children?: ReactNode }) {
  const entry = GLOSSARY_BY_ID[id];
  const [open, setOpen] = useState(false);
  const [pos, setPos] = useState<{ top: number; left: number; width: number }>({ top: 0, left: 0, width: 288 });
  const wrap = useRef<HTMLSpanElement>(null);
  const btn = useRef<HTMLButtonElement>(null);
  const pinned = useRef(false);
  const uid = useId();
  const close = useCallback(() => { pinned.current = false; setOpen(false); }, []);

  // fixed position (so tables with horizontal scroll cannot clip it), kept inside the viewport
  const show = useCallback(() => {
    const r = btn.current?.getBoundingClientRect();
    if (!r) return;
    const width = Math.min(288, window.innerWidth - 16);
    const left = Math.max(8, Math.min(r.left, window.innerWidth - width - 8));
    setPos({ top: r.bottom, left, width });
    setOpen(true);
  }, []);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: PointerEvent) => { if (wrap.current && !wrap.current.contains(e.target as Node)) close(); };
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") { close(); btn.current?.focus(); } };
    document.addEventListener("pointerdown", onDoc);
    document.addEventListener("keydown", onKey);
    window.addEventListener("scroll", close, true);
    window.addEventListener("resize", close);
    return () => {
      document.removeEventListener("pointerdown", onDoc);
      document.removeEventListener("keydown", onKey);
      window.removeEventListener("scroll", close, true);
      window.removeEventListener("resize", close);
    };
  }, [open, close]);

  const pathname = usePathname();
  const [repeatOnMobile, setRepeatOnMobile] = useState(false);
  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      const mobile = window.matchMedia("(max-width: 767px)").matches;
      if (!mobile) {
        setRepeatOnMobile(false);
        return;
      }
      let set = seenByPage.get(pathname);
      if (!set) {
        set = new Set();
        seenByPage.set(pathname, set);
      }
      if (set.has(id)) setRepeatOnMobile(true);
      else set.add(id);
    });
    return () => window.cancelAnimationFrame(frame);
  }, [id, pathname]);

  if (!entry) return <>{children ?? null}</>;
  if (repeatOnMobile) {
    return <span>{children ?? entry.term}</span>;
  }
  return (
    <span
      ref={wrap}
      className="inline-block"
      onMouseEnter={(e) => { if ((e.nativeEvent as PointerEvent).pointerType !== "touch") show(); }}
      onMouseLeave={() => { if (!pinned.current) setOpen(false); }}
      onBlur={(e) => { if (!wrap.current?.contains(e.relatedTarget as Node)) close(); }}
    >
      <button
        ref={btn}
        type="button"
        className="term"
        aria-expanded={open}
        aria-controls={`${uid}-pop`}
        aria-label={`${typeof children === "string" ? children : (Array.isArray(children) ? children.filter((c) => typeof c === "string").join("") : "") || entry.term} — ${entry.term}: açıklamayı göster`}
        onClick={() => { if (open && pinned.current) close(); else { pinned.current = true; show(); } }}
      >
        {children ?? entry.term}
      </button>
      {open && (
        <span
          id={`${uid}-pop`}
          role="note"
          style={{ top: pos.top, left: pos.left, width: pos.width }}
          className="fixed z-50 block pt-2"
        >
          <span className="block rounded-xl border border-accent-line bg-surface p-3 text-left text-sm font-normal not-italic leading-snug text-stone-800 shadow-lg">
            <strong className="mb-1 block font-semibold text-stone-900">{entry.term}</strong>
            {entry.short}
            <Link href={`/sozluk#${entry.id}`} className="mt-2 block py-1 font-medium text-accent underline">
              Sözlükte ayrıntılı oku →
            </Link>
          </span>
        </span>
      )}
    </span>
  );
}

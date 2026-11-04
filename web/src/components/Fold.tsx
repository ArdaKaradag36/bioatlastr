"use client";

import { useEffect, useRef, type ReactNode } from "react";

/** Closed accordion below 768px; on md+ the summary is hidden and the body stays in normal flow. */
export default function Fold({
  title,
  lead,
  children,
}: {
  title: string;
  lead?: ReactNode;
  children: ReactNode;
}) {
  const ref = useRef<HTMLDetailsElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const mq = window.matchMedia("(min-width: 768px)");
    const sync = () => {
      if (mq.matches) el.open = true;
    };
    sync();
    mq.addEventListener("change", sync);
    return () => mq.removeEventListener("change", sync);
  }, []);

  return (
    <details ref={ref} className="mb-4 rounded-2xl border border-stone-200 bg-white md:mb-0 md:border-0 md:bg-transparent">
      <summary className="flex min-h-11 cursor-pointer list-none items-center justify-between gap-3 px-4 py-3 text-left md:hidden">
        <span>
          <span className="block font-serif text-lg font-semibold text-stone-900">{title}</span>
          {lead && <span className="mt-0.5 block text-sm text-stone-600">{lead}</span>}
        </span>
        <span className="text-stone-500" aria-hidden>
          +
        </span>
      </summary>
      <div className="px-4 pb-4 md:px-0 md:pb-0">{children}</div>
    </details>
  );
}

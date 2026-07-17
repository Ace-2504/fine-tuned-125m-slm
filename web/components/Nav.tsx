"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import ThemePicker from "./ThemePicker";

export type NavDoc = { slug: string; title: string; subtitle: string };

function Menu({ label, base, docs }: { label: string; base: string; docs: NavDoc[] }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    function onEsc(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onEsc);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onEsc);
    };
  }, []);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-haspopup="true"
        className="flex items-center gap-1.5 text-[13px] text-[var(--fg-muted)] transition-colors hover:text-[var(--fg)]"
      >
        {label}
        <span
          className="text-[9px] transition-transform"
          style={{ transform: open ? "rotate(180deg)" : "none" }}
          aria-hidden
        >
          ▼
        </span>
      </button>

      {open && (
        <div
          className="panel absolute right-0 z-50 mt-3 w-[19rem] overflow-hidden p-1.5"
          style={{ boxShadow: "0 18px 50px rgba(0,0,0,.45)" }}
        >
          <Link
            href={base}
            onClick={() => setOpen(false)}
            className="mono block rounded-lg px-3 py-2 text-[11px] uppercase tracking-[0.14em] text-[var(--fg-dim)] hover:bg-[var(--panel-2)] hover:text-[var(--fg)]"
          >
            All {label.toLowerCase()} →
          </Link>
          <div className="hairline my-1.5" />
          <div className="max-h-[60vh] overflow-y-auto">
            {docs.map((d) => (
              <Link
                key={d.slug}
                href={`${base}/${d.slug}`}
                onClick={() => setOpen(false)}
                className="flex items-baseline justify-between gap-3 rounded-lg px-3 py-2 hover:bg-[var(--panel-2)]"
              >
                <span className="text-[13px] text-[var(--fg)]">{d.title}</span>
                <span className="mono shrink-0 text-[11px] text-[var(--fg-dim)]">{d.subtitle}</span>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function Nav({ reports, learnings }: { reports: NavDoc[]; learnings: NavDoc[] }) {
  return (
    <header className="sticky top-0 z-40 border-b border-[var(--border)] bg-[color-mix(in_srgb,var(--bg)_88%,transparent)] backdrop-blur">
      <nav className="mx-auto flex max-w-5xl items-center justify-between px-5 py-3.5">
        <Link href="/" className="flex items-baseline gap-2.5">
          <span className="mono text-[13px] font-semibold tracking-tight text-[var(--fg)]">
            SFT-SLM-125M
          </span>
          <span className="hidden text-[12px] text-[var(--fg-dim)] sm:inline">
            SFT scaling study
          </span>
        </Link>

        <div className="flex items-center gap-5">
          <Link
            href="/#demo"
            className="hidden text-[13px] text-[var(--fg-muted)] hover:text-[var(--fg)] sm:inline"
          >
            demo
          </Link>
          <Menu label="Reports" base="/reports" docs={reports} />
          <Menu label="Learnings" base="/learnings" docs={learnings} />
          <a
            href="https://github.com/Ace-2504/fine-tuned-125m-slm"
            target="_blank"
            rel="noreferrer"
            className="hidden text-[13px] text-[var(--fg-muted)] hover:text-[var(--fg)] sm:inline"
          >
            github
          </a>
          <ThemePicker />
        </div>
      </nav>
    </header>
  );
}

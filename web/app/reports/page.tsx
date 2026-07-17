import type { Metadata } from "next";
import Link from "next/link";
import { CURVE, getDocs } from "@/lib/content";

export const metadata: Metadata = { title: "Run reports · SLM-125M SFT study" };

export default function ReportsIndex() {
  const docs = getDocs("reports");
  const byRound = new Map(CURVE.map((c) => [c.round, c]));

  return (
    <main className="mx-auto max-w-4xl px-5 py-12">
      <p className="tag mb-3">Run reports</p>
      <h1 className="mb-3 text-[30px] font-semibold tracking-tight">Every training run, in full</h1>
      <p className="mb-8 max-w-[68ch] text-[var(--fg-muted)]">
        One report per round — all parameters, dataset composition, catastrophic-forgetting analysis,
        perplexity versus the previous checkpoint, judge score, sample generations and Modal runtime.
        Eleven runs: the base baseline plus ten scaling rounds.
      </p>

      <div className="panel overflow-hidden">
        <div className="hidden grid-cols-[1fr_auto_auto_auto] gap-4 border-b border-[var(--border)] bg-[var(--panel-2)] px-5 py-2.5 sm:grid">
          <span className="tag">Round</span>
          <span className="tag text-right">Judge /5</span>
          <span className="tag text-right">Forgetting</span>
          <span className="tag text-right">Ppl</span>
        </div>
        {docs.map((d) => {
          const c = byRound.get(d.order);
          return (
            <Link
              key={d.slug}
              href={`/reports/${d.slug}`}
              className="grid grid-cols-1 gap-1 border-b border-[var(--border-soft)] px-5 py-3.5 last:border-0 hover:bg-[var(--panel-2)] sm:grid-cols-[1fr_auto_auto_auto] sm:items-center sm:gap-4"
            >
              <span>
                <span className="text-[14px] text-[var(--fg)]">{d.title}</span>
                <span className="mono ml-2.5 text-[11.5px] text-[var(--fg-dim)]">{d.subtitle}</span>
              </span>
              <span className="mono text-[13px] text-[var(--fg)] sm:text-right">
                {c ? c.judge.toFixed(2) : "—"}
              </span>
              <span className="mono text-[13px] text-[var(--fg-muted)] sm:text-right">
                {c?.forget != null ? `+${c.forget}%` : "—"}
              </span>
              <span className="mono text-[13px] text-[var(--fg-muted)] sm:text-right">
                {c ? c.ppl.toFixed(2) : "—"}
              </span>
            </Link>
          );
        })}
      </div>

      <p className="mt-5 text-[13px] text-[var(--fg-dim)]">
        Judge is flat from round 2 onward; only forgetting responds to more data. See{" "}
        <Link href="/learnings/day-10" className="text-[var(--accent)] hover:underline">
          the closing analysis
        </Link>
        .
      </p>
    </main>
  );
}

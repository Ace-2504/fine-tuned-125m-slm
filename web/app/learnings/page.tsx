import type { Metadata } from "next";
import Link from "next/link";
import { getDocs } from "@/lib/content";

export const metadata: Metadata = { title: "Learnings · SLM-125M SFT study" };

/** One-line "what this round taught us", so the index is readable without opening each. */
const GIST: Record<string, string> = {
  "day-1": "Perplexity crashed but the judge didn't move — two root causes surfaced.",
  "day-2": "Trends, not snapshots: data volume looks like a weak, diminishing lever.",
  "day-3": "The round the trend broke — and common facts start landing.",
  "day-4": "Plateau confirmed; the stop rule fires.",
  "day-5": "A confirmation round — and an instrumentation gap we can't undo.",
  "day-6": "Still flat; forgetting decelerates but never reverses.",
  "day-7": "The scare: the judge jumps. Signal or noise?",
  "day-8": "The jump holds. The plateau's strongest challenge.",
  "day-9": "It collapses — and hands us the judge's noise band.",
  "day-10": "Closed as a negative result, with a regression at 10k.",
  "v2-pivot": "The redesign the evidence keeps pointing to: stop testing memory, train reading.",
};

export default function LearningsIndex() {
  const docs = getDocs("learnings");

  return (
    <main className="mx-auto max-w-4xl px-5 py-12 text-center">
      <p className="tag mb-3">Learnings</p>
      <h1 className="mb-3 text-[30px] font-semibold tracking-tight">What each round taught us</h1>
      <p className="mx-auto mb-8 max-w-[68ch] text-[var(--fg-muted)]">
        Feedback written after every training round: what it revealed, how severe, and the fix — plus
        the pivot decision the evidence kept pointing to. Read in order, they show a hypothesis being
        formed, challenged, and settled.
      </p>

      <div className="grid gap-3 text-left sm:grid-cols-2">
        {docs.map((d) => (
          <Link
            key={d.slug}
            href={`/learnings/${d.slug}`}
            className="panel px-5 py-4 transition-colors hover:bg-[var(--panel-2)]"
          >
            <div className="mb-1.5 flex items-baseline justify-between gap-3">
              <span className="text-[14.5px] font-medium text-[var(--fg)]">{d.title}</span>
              <span className="mono shrink-0 text-[11px] text-[var(--fg-dim)]">{d.subtitle}</span>
            </div>
            <p className="text-[13px] leading-relaxed text-[var(--fg-muted)]">{GIST[d.slug] ?? ""}</p>
          </Link>
        ))}
      </div>
    </main>
  );
}

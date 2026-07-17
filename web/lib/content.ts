import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";

/**
 * Static content layer: the study's run reports and per-round feedback, read from
 * web/content/ at build time (synced from sft/ by scripts/sync-content.mjs).
 */

export type Kind = "reports" | "learnings";

export type Doc = {
  slug: string;
  kind: Kind;
  title: string;
  subtitle: string;
  order: number;
  body: string;
};

const DIR = (kind: Kind) => join(process.cwd(), "content", kind);

/** run-00 -> Baseline; run-07 -> Round 7. day1 -> Round 1; v2-pivot -> the pivot decision. */
function describe(kind: Kind, file: string): Pick<Doc, "slug" | "title" | "subtitle" | "order"> {
  const base = file.replace(/\.md$/, "");
  if (kind === "reports") {
    const n = Number(base.replace("run-", ""));
    return {
      slug: `run-${String(n).padStart(2, "0")}`,
      order: n,
      title: n === 0 ? "Baseline · base model" : `Round ${n}`,
      subtitle: n === 0 ? "0 pairs — the “before” reference" : `${(n * 1000).toLocaleString()} pairs`,
    };
  }
  if (base === "v2-pivot") {
    return { slug: "v2-pivot", order: 99, title: "The v2 pivot", subtitle: "Decision · open-book redesign" };
  }
  const n = Number(base.replace("day", ""));
  return {
    slug: `day-${n}`,
    order: n,
    title: `Round ${n} feedback`,
    subtitle: `${(n * 1000).toLocaleString()} pairs`,
  };
}

export function getDocs(kind: Kind): Doc[] {
  const files = readdirSync(DIR(kind)).filter((f) => f.endsWith(".md"));
  return files
    .map((f) => {
      const meta = describe(kind, f);
      return { ...meta, kind, body: readFileSync(join(DIR(kind), f), "utf8") };
    })
    .sort((a, b) => a.order - b.order);
}

export function getDoc(kind: Kind, slug: string): Doc | undefined {
  return getDocs(kind).find((d) => d.slug === slug);
}

/** Headline numbers per round, for the nav/index tables. Source: sft/research_log.md. */
export const CURVE = [
  { round: 0, pairs: 0, ppl: 24.44, retention: 11.35, forget: null, judge: 1.0 },
  { round: 1, pairs: 1000, ppl: 8.6, retention: 12.05, forget: 6.1, judge: 1.32 },
  { round: 2, pairs: 2000, ppl: 8.0, retention: 12.42, forget: 9.5, judge: 1.5 },
  { round: 3, pairs: 3000, ppl: 7.7, retention: 12.6, forget: 11.0, judge: 1.46 },
  { round: 4, pairs: 4000, ppl: 7.51, retention: 12.74, forget: 12.2, judge: 1.5 },
  { round: 5, pairs: 5000, ppl: 7.37, retention: 12.9, forget: 13.6, judge: 1.52 },
  { round: 6, pairs: 6000, ppl: 7.28, retention: 12.95, forget: 14.1, judge: 1.54 },
  { round: 7, pairs: 7000, ppl: 7.2, retention: 13.0, forget: 14.6, judge: 1.6 },
  { round: 8, pairs: 8000, ppl: 7.12, retention: 13.1, forget: 15.4, judge: 1.6 },
  { round: 9, pairs: 9000, ppl: 7.05, retention: 13.18, forget: 16.2, judge: 1.54 },
  { round: 10, pairs: 10000, ppl: 7.01, retention: 13.2, forget: 16.3, judge: 1.54 },
];

/**
 * How the model was fine-tuned: the teacher, the data pipeline, and the training recipe.
 * The flowchart mirrors the pretraining site's strip, one step per stage.
 */

const STEPS = [
  { label: "corpus", sub: "670k cleaned docs" },
  { label: "chunk", sub: "~500-token passages" },
  { label: "teacher", sub: "gemini-3.1-flash-lite" },
  { label: "filter", sub: "format + grounding" },
  { label: "dedup", sub: "exact · MiniLM · decontam" },
  { label: "balance", sub: "task + domain mix" },
  { label: "fine-tune", sub: "L4 · 3 epochs" },
  { label: "eval", sub: "ppl · retention · judge" },
];

const RECIPE: [string, string][] = [
  ["teacher", "gemini-3.1-flash-lite"],
  ["pairs", "1,000 per round → 10,000"],
  ["method", "full fine-tune (no LoRA)"],
  ["loss", "assistant tokens only"],
  ["epochs / batch", "3 · 16"],
  ["lr", "3e-5 → 3e-6 cosine"],
  ["precision", "bf16 · AdamW · seed 1337"],
  ["hardware", "one Modal L4 · ~$0.10/run"],
];

export default function Pipeline() {
  return (
    <div className="space-y-3">
      {/* flowchart */}
      <div className="panel overflow-x-auto p-5">
        <div className="flex min-w-max items-stretch justify-center gap-1.5">
          {STEPS.map((s, i) => (
            <div key={s.label} className="flex items-stretch gap-1.5">
              <div className="panel-inset flex min-w-[7.5rem] flex-col items-center justify-center px-3 py-2.5">
                <span className="mono text-[12px] font-semibold text-[var(--fg)]">{s.label}</span>
                <span className="mono mt-0.5 text-[9.5px] leading-tight text-[var(--fg-dim)]">
                  {s.sub}
                </span>
              </div>
              {i < STEPS.length - 1 && (
                <span className="self-center text-[11px] text-[var(--fg-dim)]" aria-hidden>
                  →
                </span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* recipe */}
      <div className="panel p-5 text-left sm:p-6">
        <dl className="grid gap-x-8 gap-y-2 sm:grid-cols-2">
          {RECIPE.map(([k, v]) => (
            <div key={k} className="flex items-baseline justify-between gap-3 border-b border-[var(--border-soft)] pb-1.5">
              <dt className="tag">{k}</dt>
              <dd className="mono text-right text-[12.5px] text-[var(--fg)]">{v}</dd>
            </div>
          ))}
        </dl>
      </div>
    </div>
  );
}

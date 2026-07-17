"use client";

import { useState } from "react";

type Result = { "day-2"?: string; "day-10"?: string; seconds?: number };

const EXAMPLES = [
  "What is the standard of proof in a civil lawsuit?",
  "What does it mean for a contract clause to be severable?",
  "Summarize what a 10-K annual report contains.",
  "What is a preponderance of the evidence?",
];

const MODELS = [
  { key: "day-2" as const, label: "2,000 pairs", note: "judge 1.50 · forgetting +9.5%", best: true },
  { key: "day-10" as const, label: "10,000 pairs", note: "judge 1.54 · forgetting +16.3%", best: false },
];

export default function Demo() {
  const [question, setQuestion] = useState(EXAMPLES[0]);
  const [tokens, setTokens] = useState(120);
  const [temp, setTemp] = useState(0.7);
  const [busy, setBusy] = useState(false);
  const [res, setRes] = useState<Result | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function run() {
    if (!question.trim() || busy) return;
    setBusy(true);
    setErr(null);
    setRes(null);
    try {
      const r = await fetch("/api/compare", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ question, max_new_tokens: tokens, temperature: temp }),
      });
      const data = await r.json();
      if (!r.ok) {
        setErr(
          ["not_configured", "unreachable", "timeout"].includes(data?.error)
            ? "The demo backend is offline — it runs on a local CPU endpoint that isn't always up. The study results below are unaffected."
            : `Upstream error (${data?.status ?? r.status}).`
        );
      } else {
        setRes(data);
      }
    } catch {
      setErr("Could not reach the demo backend.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section id="demo" className="scroll-mt-20">
      <p className="tag mb-2.5">Live comparison</p>
      <h2 className="mb-2 text-[22px] font-semibold tracking-tight">Ask both models the same thing</h2>
      <p className="mb-5 max-w-[70ch] text-[14.5px] text-[var(--fg-muted)]">
        Left was fine-tuned on 2,000 QnA pairs; right on 10,000 — five times the data. The study says
        the extra data bought no quality. Judge for yourself.
      </p>

      <div className="panel p-5 sm:p-6">
        <div className="grid gap-4 lg:grid-cols-[1fr_15rem]">
          <div>
            <label className="tag mb-2 block">Question</label>
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              rows={3}
              className="field mono w-full resize-y text-[13.5px]"
            />
            <div className="mt-2.5 flex flex-wrap gap-1.5">
              {EXAMPLES.map((ex) => (
                <button
                  key={ex}
                  onClick={() => setQuestion(ex)}
                  className="badge cursor-pointer hover:text-[var(--fg)]"
                >
                  {ex.length > 42 ? ex.slice(0, 40) + "…" : ex}
                </button>
              ))}
            </div>
          </div>

          <div className="flex flex-col gap-3.5">
            <div>
              <div className="mb-1.5 flex justify-between">
                <span className="tag">Max tokens</span>
                <span className="mono text-[12px] text-[var(--fg-muted)]">{tokens}</span>
              </div>
              <input
                type="range"
                min={20}
                max={256}
                step={10}
                value={tokens}
                onChange={(e) => setTokens(Number(e.target.value))}
                className="w-full accent-[var(--accent)]"
              />
            </div>
            <div>
              <div className="mb-1.5 flex justify-between">
                <span className="tag">Temperature</span>
                <span className="mono text-[12px] text-[var(--fg-muted)]">{temp.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min={0}
                max={1.2}
                step={0.05}
                value={temp}
                onChange={(e) => setTemp(Number(e.target.value))}
                className="w-full accent-[var(--accent)]"
              />
            </div>
            <button onClick={run} disabled={busy} className="btn-primary mt-auto">
              {busy ? "Generating…" : "Ask both models"}
            </button>
          </div>
        </div>

        {err && <p className="panel-inset mt-4 px-4 py-3 text-[13px] text-[var(--fg-muted)]">{err}</p>}

        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {MODELS.map((m) => (
            <div key={m.key} className="panel-inset p-4">
              <div className="mb-2 flex items-baseline justify-between gap-2">
                <span className="text-[13.5px] font-medium text-[var(--fg)]">
                  {m.label}
                  {m.best && (
                    <span className="badge-accent ml-2 rounded-md px-1.5 py-0.5 text-[10px]">
                      better model
                    </span>
                  )}
                </span>
                <span className="mono shrink-0 text-[10.5px] text-[var(--fg-dim)]">{m.note}</span>
              </div>
              <p className="mono min-h-[7rem] whitespace-pre-wrap text-[12.5px] leading-relaxed text-[var(--fg-muted)]">
                {busy ? "…" : (res?.[m.key] ?? "—")}
              </p>
            </div>
          ))}
        </div>

        <p className="mt-3 text-[11.5px] text-[var(--fg-dim)]">
          {res?.seconds
            ? `Both models answered in ${res.seconds}s on a CPU endpoint.`
            : "Runs on a local CPU endpoint via a Cloudflare tunnel; both models answer in ~2s."}{" "}
          Expect fluent, confident, frequently wrong answers — these score ~1.5/5.
        </p>
      </div>
    </section>
  );
}

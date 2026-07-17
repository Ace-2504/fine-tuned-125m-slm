import Link from "next/link";
import Curve from "@/components/Curve";
import Demo from "@/components/Demo";

const STATS = [
  { v: "10×", k: "data scaled", note: "1k → 10k pairs" },
  { v: "+0.04", k: "judge moved", note: "2k → 10k · noise" },
  { v: "+16.3%", k: "forgetting", note: "tripled" },
  { v: "11", k: "training runs", note: "method frozen" },
  { v: "$4.60", k: "total cost", note: "GPU + teacher" },
  { v: "125.8M", k: "parameters", note: "1,024 ctx" },
];

function Section({
  tag,
  title,
  lead,
  children,
}: {
  tag: string;
  title: string;
  lead?: string;
  children?: React.ReactNode;
}) {
  return (
    <section className="mt-16">
      <p className="tag mb-2.5">{tag}</p>
      <h2 className="mb-2 text-[22px] font-semibold tracking-tight">{title}</h2>
      {lead && <p className="mb-5 max-w-[70ch] text-[14.5px] text-[var(--fg-muted)]">{lead}</p>}
      {children}
    </section>
  );
}

export default function Home() {
  return (
    <main className="mx-auto max-w-5xl px-5 py-14">
      {/* hero */}
      <p className="tag mb-4">Research log · supervised fine-tuning</p>
      <h1 className="max-w-[20ch] text-[clamp(30px,5vw,46px)] font-semibold leading-[1.1] tracking-tight">
        We scaled SFT data 10× and quality didn&rsquo;t move.
      </h1>
      <p className="mt-4 max-w-[72ch] text-[16.5px] leading-relaxed text-[var(--fg-muted)]">
        A ten-round data-scaling study on a 125.8M-parameter model{" "}
        <a
          href="https://huggingface.co/Ace-2504/slm-125m-base"
          target="_blank"
          rel="noreferrer"
          className="text-[var(--fg)] underline decoration-[var(--border)] underline-offset-2 hover:decoration-[var(--accent)]"
        >
          pretrained from scratch
        </a>{" "}
        on US case law, SEC filings and educational web text. Each round added 1,000 teacher-written
        QnA pairs and re-fine-tuned from the base. Going from 1,000 to 10,000 pairs left answer
        quality flat at ~1.5/5 — and <strong className="text-[var(--fg)]">tripled catastrophic forgetting</strong>.
      </p>

      {/* stat tiles */}
      <div className="mt-9 grid grid-cols-2 gap-2.5 sm:grid-cols-3 lg:grid-cols-6">
        {STATS.map((s) => (
          <div key={s.k} className="panel px-3.5 py-3.5">
            <div className="mono text-[21px] font-semibold tracking-tight text-[var(--fg)]">{s.v}</div>
            <div className="tag mt-1.5">{s.k}</div>
            <div className="mono mt-0.5 text-[10.5px] text-[var(--fg-dim)]">{s.note}</div>
          </div>
        ))}
      </div>

      <div className="mt-14">
        <Demo />
      </div>

      <Section
        tag="The result"
        title="The scaling curve"
        lead="Every point re-trains from the base model on the cumulative dataset and is scored on the same frozen 100-pair eval and 50-question judge set. The method is frozen across all ten rounds — only dataset size changes — so the curve isolates the effect of data alone."
      >
        <Curve />
      </Section>

      <Section
        tag="Data loss"
        title="The only thing more data reliably bought"
        lead="Retention perplexity is measured on the original pretraining validation set — the same metric that produced the base model's 11.35 — so it's a true catastrophic-forgetting gauge, not a proxy. It rose in every single one of ten rounds."
      >
        <div className="panel p-5 sm:p-6">
          <div className="space-y-2.5">
            {[
              { l: "base", v: 11.35, w: 86 },
              { l: "1k", v: 12.05, w: 91 },
              { l: "3k", v: 12.6, w: 95 },
              { l: "5k", v: 12.9, w: 98 },
              { l: "10k", v: 13.2, w: 100 },
            ].map((r) => (
              <div key={r.l} className="grid grid-cols-[3.5rem_1fr_3.5rem] items-center gap-3">
                <span className="mono text-[12px] text-[var(--fg-dim)]">{r.l}</span>
                <div className="bar-track">
                  <div className="bar-fill" style={{ width: `${r.w}%` }} />
                </div>
                <span className="mono text-right text-[12.5px] text-[var(--fg-muted)]">{r.v}</span>
              </div>
            ))}
          </div>
          <div className="hairline my-5" />
          <p className="text-[13.5px] leading-relaxed text-[var(--fg-muted)]">
            <strong className="text-[var(--fg)]">Forgetting nearly tripled: +6.1% → +16.3%.</strong>{" "}
            Data volume had a large, consistent, monotonic effect on exactly one metric — and it was
            the one we didn&rsquo;t want. Every round past round 2 was pure cost. The round-0 baseline
            reproduced the base perplexity to four significant figures (11.3546 vs the known 11.35),
            which validates the measurement.
          </p>
        </div>
      </Section>

      <Section
        tag="The sharpest evidence"
        title="Quality actually regressed at scale"
        lead="One fixed probe, tracked across all ten rounds:"
      >
        <div className="panel-inset mono overflow-x-auto p-5 text-[12.5px] leading-relaxed">
          <div className="text-[var(--fg-dim)]">Q · What is the standard of proof in a civil lawsuit?</div>
          <div className="mt-3 space-y-1.5">
            <div>
              <span className="text-[var(--fg-dim)]">rounds 1–2 </span>
              <span className="text-[var(--fg-muted)]">circular repetition</span>
            </div>
            <div>
              <span className="text-[var(--fg-dim)]">rounds 3–9 </span>
              <span className="text-[var(--fg)]">
                “…is the preponderance of the evidence standard.” ✓ correct — held seven rounds
              </span>
            </div>
            <div>
              <span className="text-[var(--fg-dim)]">round 10 &nbsp;</span>
              <span className="text-[var(--fg-muted)]">
                “A civil action is a civil action for the recovery of money, which is generally a civil
                action for the recovery of money.” ✗ regressed
              </span>
            </div>
          </div>
        </div>
        <p className="mt-3 max-w-[70ch] text-[13.5px] text-[var(--fg-muted)]">
          <strong className="text-[var(--fg)]">More data made a previously-correct answer worse.</strong>{" "}
          Consistent with accumulating drift: the model is pulled away from its pretrained knowledge
          faster than extra closed-book examples can teach it anything, so earlier wins get overwritten.
        </p>
      </Section>

      <Section
        tag="Why"
        title="It was asked to memorise, not to read"
        lead="~40% of training was closed-book QA: recall a document fact from a single exposure. A 125M model cannot store long-tail facts that way, so no amount of supervision installs them."
      >
        <div className="grid gap-3 sm:grid-cols-3">
          {[
            {
              t: "Common facts land",
              d: "“Preponderance of the evidence” was learned by round 3 — it recurs across the corpus.",
            },
            {
              t: "Long-tail facts never do",
              d: "A single company’s 1997 sales figure, seen once, is unlearnable at this scale.",
            },
            {
              t: "So the judge measures the worst skill",
              d: "The eval is dominated by that recall, while learnable grounded tasks go under-measured.",
            },
          ].map((c) => (
            <div key={c.t} className="panel p-4">
              <div className="mb-1.5 text-[14px] font-medium text-[var(--fg)]">{c.t}</div>
              <p className="text-[13px] leading-relaxed text-[var(--fg-muted)]">{c.d}</p>
            </div>
          ))}
        </div>
        <div className="panel mt-3 p-5">
          <p className="text-[13.5px] leading-relaxed text-[var(--fg-muted)]">
            <strong className="text-[var(--fg)]">Practical takeaway: stop at 2k.</strong> The best
            checkpoint isn&rsquo;t the biggest — round 2 strictly dominates round 10: the same judge
            score (1.50 vs 1.54, identical within the ±0.07 noise band) at half the forgetting, one
            fifth of the data, and with the probe answer still intact. The study&rsquo;s usable output
            is a smaller model, not a bigger one. The one untested lever is the{" "}
            <Link href="/learnings/v2-pivot" className="text-[var(--accent)] hover:underline">
              mix — an open-book redesign
            </Link>
            .
          </p>
        </div>
      </Section>

      <Section tag="Read on" title="The full record">
        <div className="grid gap-3 sm:grid-cols-2">
          <Link href="/reports" className="panel p-5 transition-colors hover:bg-[var(--panel-2)]">
            <div className="mb-1.5 text-[15px] font-medium text-[var(--fg)]">Run reports →</div>
            <p className="text-[13px] leading-relaxed text-[var(--fg-muted)]">
              All 11 runs: every parameter, dataset composition, forgetting analysis, perplexity vs the
              previous checkpoint, judge score, samples and Modal runtime.
            </p>
          </Link>
          <Link href="/learnings" className="panel p-5 transition-colors hover:bg-[var(--panel-2)]">
            <div className="mb-1.5 text-[15px] font-medium text-[var(--fg)]">Learnings →</div>
            <p className="text-[13px] leading-relaxed text-[var(--fg-muted)]">
              Feedback written after each round — including the round-7 scare, when the judge jumped and
              we had to test whether the plateau was wrong.
            </p>
          </Link>
        </div>
      </Section>
    </main>
  );
}

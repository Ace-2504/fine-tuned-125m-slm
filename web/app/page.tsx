import Link from "next/link";
import Curve from "@/components/Curve";
import Demo from "@/components/Demo";
import Pipeline from "@/components/Pipeline";

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
      {lead && (
        <p className="mx-auto mb-5 max-w-[70ch] text-[14.5px] text-[var(--fg-muted)]">{lead}</p>
      )}
      {children}
    </section>
  );
}

export default function Home() {
  return (
    <main className="mx-auto max-w-5xl px-5 py-14 text-center">
      {/* hero */}
      <p className="tag mb-4">Fine-tuned by Harman Sandhu</p>
      <h1 className="mono text-[clamp(34px,6vw,58px)] font-semibold leading-none tracking-tight">
        SFT-SLM-125M
      </h1>
      <p className="mx-auto mt-5 max-w-[68ch] text-[16.5px] leading-relaxed text-[var(--fg-muted)]">
        A supervised fine-tune of a 125.8M-parameter legal model{" "}
        <a
          href="https://huggingface.co/Ace-2504/slm-125m-base"
          target="_blank"
          rel="noreferrer"
          className="text-[var(--fg)] underline decoration-[var(--border)] underline-offset-2 hover:decoration-[var(--accent)]"
        >
          pretrained from scratch
        </a>
        , run as a ten-round data-scaling study — and the headline is a negative result:{" "}
        <strong className="text-[var(--fg)]">
          we scaled the fine-tuning data 10× and answer quality didn&rsquo;t move
        </strong>
        , while catastrophic forgetting tripled.
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
        tag="How it was made"
        title="The teacher, and the pipeline"
        lead="A larger model wrote the training data — knowledge distillation via data. Gemini 3.1 Flash-Lite read passages from the very corpus the base model was pretrained on and wrote question–answer pairs whose answers are stated in that passage. The student never sees the teacher's weights, only its answers."
      >
        <Pipeline />
        <p className="mx-auto mt-4 max-w-[74ch] text-left text-[13.5px] leading-relaxed text-[var(--fg-muted)]">
          <strong className="text-[var(--fg)]">Why this teacher:</strong> the plan called for Gemini
          2.5 Flash, but it is blocked for new accounts, so the study used{" "}
          <code className="mono rounded border border-[var(--border)] bg-[var(--panel-2)] px-1.5 py-0.5 text-[0.86em]">
            gemini-3.1-flash-lite
          </code>{" "}
          — a released model with the request headroom to generate 1,000 pairs a day. Because every
          answer has to be stated in the passage we hand it, the teacher&rsquo;s own knowledge barely
          matters; the grounding does the work.{" "}
          <strong className="text-[var(--fg)]">Every pair is then filtered</strong>: malformed answers
          dropped, each answer checked against its source passage, exact and near-duplicate questions
          removed by embedding similarity, anything overlapping the LexGLUE/CaseHOLD benchmarks
          discarded, and the survivors balanced to a fixed task and domain mix. Roughly 40% of raw
          teacher output never makes it in.{" "}
          <strong className="text-[var(--fg)]">Training then re-starts from the base model every
          round</strong> — never from the previous round — so the only thing that changes across the
          curve is how much data it saw. Loss is computed on the assistant&rsquo;s answer only, never
          on the question.
        </p>
      </Section>

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
        lead="Retention perplexity measures how well the model still predicts the ordinary legal text it was originally pretrained on. It is the same measurement that gave the base model its score of 11.35, so the numbers are directly comparable — higher means more of the original skill has been lost."
      >
        <div className="panel p-5 sm:p-6">
          <div className="mx-auto max-w-xl space-y-2.5">
            {[
              { l: "base", v: 11.35, w: 86 },
              { l: "1k", v: 12.05, w: 91 },
              { l: "3k", v: 12.6, w: 95 },
              { l: "5k", v: 12.9, w: 98 },
              { l: "10k", v: 13.2, w: 100 },
            ].map((r) => (
              <div key={r.l} className="grid grid-cols-[3.5rem_1fr_3.5rem] items-center gap-3">
                <span className="mono text-left text-[12px] text-[var(--fg-dim)]">{r.l}</span>
                <div className="bar-track">
                  <div className="bar-fill" style={{ width: `${r.w}%` }} />
                </div>
                <span className="mono text-right text-[12.5px] text-[var(--fg-muted)]">{r.v}</span>
              </div>
            ))}
          </div>
          <div className="hairline my-5" />
          <div className="mx-auto max-w-[74ch] space-y-3 text-left text-[13.5px] leading-relaxed text-[var(--fg-muted)]">
            <p>
              <strong className="text-[var(--fg)]">The damage roughly tripled.</strong> After 1,000
              pairs the model was about 6% worse at the thing it originally knew. After 10,000 it was
              16% worse. More training data made it steadily worse at its own subject.
            </p>
            <p>
              <strong className="text-[var(--fg)]">
                It got worse every single round — ten out of ten, never once better.
              </strong>{" "}
              Out of everything we measured, more data reliably moved only one number, and it was the
              damage. The number we actually wanted to improve — answer quality — ignored the extra
              data completely. So every round after round 2 was pure cost: no better answers, just
              more forgetting.
            </p>
            <p>
              <strong className="text-[var(--fg)]">Is the measurement trustworthy?</strong> Yes — we
              checked the ruler before using it. Before any fine-tuning, we measured the untouched base
              model with our own tool and got <span className="mono">11.3546</span>, matching its
              known score of <span className="mono">11.35</span>. Since the instrument reproduces a
              number we already knew, the later reading of <span className="mono">13.20</span> is real
              damage, not a broken measurement.
            </p>
          </div>
        </div>
      </Section>

      <Section
        tag="The sharpest evidence"
        title="Quality actually regressed at scale"
        lead="One fixed question, asked after every single round. Watch what happens at the end."
      >
        <div className="panel overflow-hidden text-left">
          <div className="border-b border-[var(--border)] bg-[var(--panel-2)] px-5 py-3">
            <span className="tag">The question</span>
            <p className="mt-1 text-[14px] text-[var(--fg)]">
              What is the standard of proof in a civil lawsuit?
            </p>
          </div>
          <div className="divide-y divide-[var(--border-soft)]">
            {[
              {
                r: "rounds 1–2",
                a: "The standard of proof in a civil lawsuit is the standard of proof in a civil lawsuit.",
                verdict: "repeats itself",
                good: false,
              },
              {
                r: "rounds 3–9",
                a: "The standard of proof in a civil lawsuit is the preponderance of the evidence standard.",
                verdict: "correct — held for seven rounds",
                good: true,
              },
              {
                r: "round 10",
                a: "A civil action is a civil action for the recovery of money, which is generally a civil action for the recovery of money.",
                verdict: "regressed",
                good: false,
              },
            ].map((row) => (
              <div key={row.r} className="grid gap-2 px-5 py-4 sm:grid-cols-[7rem_1fr] sm:gap-4">
                <div className="mono pt-0.5 text-[12px] text-[var(--fg-dim)]">{row.r}</div>
                <div>
                  <p
                    className={`text-[13.5px] leading-relaxed ${
                      row.good ? "text-[var(--fg)]" : "text-[var(--fg-muted)]"
                    }`}
                  >
                    &ldquo;{row.a}&rdquo;
                  </p>
                  <span
                    className={`mono mt-1.5 inline-block text-[11px] ${
                      row.good ? "text-[var(--accent)]" : "text-[var(--fg-dim)]"
                    }`}
                  >
                    {row.good ? "✓" : "✗"} {row.verdict}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
        <p className="mx-auto mt-3 max-w-[70ch] text-left text-[13.5px] leading-relaxed text-[var(--fg-muted)]">
          <strong className="text-[var(--fg)]">More data made a right answer wrong.</strong> It had
          this correct for seven straight rounds, then broke at 10,000 pairs — the model drifts away
          from its pretrained knowledge faster than extra closed-book examples can teach it anything,
          so earlier wins get overwritten.
        </p>
      </Section>

      <Section
        tag="Why"
        title="It was asked to memorise, not to read"
        lead="About 40% of the training asked the model to recall a fact from a document it isn't allowed to see while answering. A 125M model cannot store long-tail facts from a single exposure — fine-tuning teaches behaviour, not knowledge. That portion was unlearnable, and it dragged the score down no matter how much we added."
      >
        <div className="grid gap-3 sm:grid-cols-3">
          {[
            {
              t: "Common facts land",
              d: "“Preponderance of the evidence” was learned by round 3 — it recurs constantly across the corpus.",
            },
            {
              t: "Long-tail facts never do",
              d: "A single company’s 1997 sales figure, seen once in one pair, is unlearnable at this size.",
            },
            {
              t: "So the score measures its worst skill",
              d: "The eval is dominated by that recall, while the tasks it can learn go under-measured.",
            },
          ].map((c) => (
            <div key={c.t} className="panel p-4 text-left">
              <div className="mb-1.5 text-[14px] font-medium text-[var(--fg)]">{c.t}</div>
              <p className="text-[13px] leading-relaxed text-[var(--fg-muted)]">{c.d}</p>
            </div>
          ))}
        </div>
        <div className="panel mt-3 p-5 text-left">
          <p className="text-[13.5px] leading-relaxed text-[var(--fg-muted)]">
            <strong className="text-[var(--fg)]">Practical takeaway: stop at 2k.</strong> The best
            checkpoint isn&rsquo;t the biggest — the 2,000-pair model matches the 10,000-pair one on
            answer quality (1.50 vs 1.54, identical within the ±0.07 noise band) at half the
            forgetting, one fifth of the data, and with the probe answer still intact. The
            study&rsquo;s usable output is a smaller model, not a bigger one. The one untested lever is
            the{" "}
            <Link href="/learnings/v2-pivot" className="text-[var(--accent)] hover:underline">
              mix — an open-book redesign
            </Link>
            .
          </p>
        </div>
      </Section>

      <Section tag="Read on" title="The full record">
        <div className="grid gap-3 sm:grid-cols-2">
          <Link href="/reports" className="panel p-5 text-left transition-colors hover:bg-[var(--panel-2)]">
            <div className="mb-1.5 text-[15px] font-medium text-[var(--fg)]">Run reports →</div>
            <p className="text-[13px] leading-relaxed text-[var(--fg-muted)]">
              All 11 runs: every parameter, dataset composition, forgetting analysis, perplexity vs the
              previous checkpoint, judge score, samples and Modal runtime.
            </p>
          </Link>
          <Link href="/learnings" className="panel p-5 text-left transition-colors hover:bg-[var(--panel-2)]">
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

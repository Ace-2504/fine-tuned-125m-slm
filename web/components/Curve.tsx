import Link from "next/link";
import { CURVE } from "@/lib/content";

/** The scaling curve: a table plus a single-accent judge bar — the study's whole story. */
export default function Curve() {
  const maxJudge = 2.0; // bar scale: judge is /5 but never exceeds 1.6 — scale to keep it readable
  return (
    <div className="panel overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-[13.5px]">
          <thead>
            <tr className="bg-[var(--panel-2)]">
              {["Round", "Pairs", "Judge /5", "", "Forgetting", "Ppl"].map((h, i) => (
                <th
                  key={i}
                  className={`mono border-b border-[var(--border)] px-4 py-2.5 text-[11px] font-medium uppercase tracking-wider text-[var(--fg-muted)] ${
                    i === 0 ? "text-left" : "text-right"
                  } ${i === 3 ? "w-[26%]" : ""}`}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {CURVE.map((c) => {
              const gainEnds = c.round === 2;
              const last = c.round === 10;
              return (
                <tr
                  key={c.round}
                  className={`border-b border-[var(--border-soft)] last:border-0 ${
                    gainEnds || last ? "bg-[color-mix(in_srgb,var(--accent)_6%,transparent)]" : ""
                  }`}
                >
                  <td className="mono px-4 py-2.5 text-[var(--fg)]">
                    {c.round === 0 ? "0 · base" : c.round}
                    {gainEnds && (
                      <span className="ml-2 text-[10.5px] text-[var(--accent)]">gain ends here</span>
                    )}
                  </td>
                  <td className="mono px-4 py-2.5 text-right text-[var(--fg-muted)]">
                    {c.pairs.toLocaleString()}
                  </td>
                  <td className="mono px-4 py-2.5 text-right font-medium text-[var(--fg)]">
                    {c.judge.toFixed(2)}
                  </td>
                  <td className="px-4 py-2.5">
                    <div className="bar-track">
                      <div className="bar-fill" style={{ width: `${(c.judge / maxJudge) * 100}%` }} />
                    </div>
                  </td>
                  <td className="mono px-4 py-2.5 text-right text-[var(--fg-muted)]">
                    {c.forget == null ? "—" : `+${c.forget.toFixed(1)}%`}
                  </td>
                  <td className="mono px-4 py-2.5 text-right text-[var(--fg-dim)]">
                    {c.ppl.toFixed(2)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="hairline" />
      <p className="px-4 py-3 text-[12.5px] text-[var(--fg-dim)]">
        Judge deltas by round: +0.32, +0.18, −0.04, +0.04, +0.02, +0.02, +0.06, 0.00, −0.06, 0.00 —
        a flat line with noise. Every round has a{" "}
        <Link href="/reports" className="text-[var(--accent)] hover:underline">
          full report
        </Link>
        .
      </p>
    </div>
  );
}

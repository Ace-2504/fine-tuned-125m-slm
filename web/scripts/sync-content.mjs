/**
 * Copy the study's markdown into web/content/ so the Next app can statically render it.
 *
 * Why copy instead of reading ../sft directly: Vercel builds with Root Directory = web/,
 * so anything outside web/ is not reliably in the build context. The copies are committed.
 *
 *   node scripts/sync-content.mjs      (re-run whenever a report or feedback file changes)
 */
import { cp, mkdir, readdir, rm } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const repo = join(here, "..", "..");

const JOBS = [
  { from: join(repo, "sft", "reports"), to: join(here, "..", "content", "reports") },
  { from: join(repo, "sft", "training-feedback"), to: join(here, "..", "content", "learnings") },
];

for (const { from, to } of JOBS) {
  await rm(to, { recursive: true, force: true });
  await mkdir(to, { recursive: true });
  const files = (await readdir(from)).filter((f) => f.endsWith(".md"));
  for (const f of files) await cp(join(from, f), join(to, f));
  console.log(`synced ${files.length.toString().padStart(2)} md -> ${to.replace(repo, ".")}`);
}

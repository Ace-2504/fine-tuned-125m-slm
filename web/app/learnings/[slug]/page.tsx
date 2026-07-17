import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import Markdown from "@/components/Markdown";
import { getDoc, getDocs } from "@/lib/content";

export function generateStaticParams() {
  return getDocs("learnings").map((d) => ({ slug: d.slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const doc = getDoc("learnings", slug);
  return { title: doc ? `${doc.title} · SLM-125M learnings` : "Learnings" };
}

export default async function LearningPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const doc = getDoc("learnings", slug);
  if (!doc) notFound();

  const all = getDocs("learnings");
  const i = all.findIndex((d) => d.slug === slug);
  const prev = all[i - 1];
  const next = all[i + 1];

  return (
    <main className="mx-auto max-w-3xl px-5 py-12">
      <p className="tag mb-3">
        <Link href="/learnings" className="hover:text-[var(--fg)]">
          Learnings
        </Link>{" "}
        / {doc.subtitle}
      </p>
      <article className="panel px-6 py-7 sm:px-9 sm:py-9">
        <Markdown>{doc.body}</Markdown>
      </article>

      <nav className="mt-6 flex items-center justify-between gap-3 text-[13px]">
        {prev ? (
          <Link href={`/learnings/${prev.slug}`} className="btn">
            ← {prev.title}
          </Link>
        ) : (
          <span />
        )}
        {next ? (
          <Link href={`/learnings/${next.slug}`} className="btn">
            {next.title} →
          </Link>
        ) : (
          <span />
        )}
      </nav>
    </main>
  );
}

import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import Link from "next/link";
import Nav from "@/components/Nav";
import { getDocs } from "@/lib/content";
import "./globals.css";

const sans = Inter({ subsets: ["latin"], variable: "--font-sans", display: "swap" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono", display: "swap" });

export const metadata: Metadata = {
  title: "SLM-125M · we scaled SFT data 10× and quality didn't move",
  description:
    "A ten-round supervised fine-tuning data-scaling study on a 125M from-scratch legal model. Scaling data 10× left answer quality flat at ~1.5/5 and tripled catastrophic forgetting.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  // Apply the saved theme before first paint — otherwise the default flashes first.
  const themeScript = `(function(){try{var t=localStorage.getItem('slm-theme');if(t){document.documentElement.setAttribute('data-theme',t);}}catch(e){}})();`;

  const reports = getDocs("reports").map(({ slug, title, subtitle }) => ({ slug, title, subtitle }));
  const learnings = getDocs("learnings").map(({ slug, title, subtitle }) => ({ slug, title, subtitle }));

  return (
    <html lang="en" data-theme="cobalt">
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className={`${sans.variable} ${mono.variable}`}>
        <Nav reports={reports} learnings={learnings} />
        {children}
        <footer className="mt-24 border-t border-[var(--border)]">
          <div className="mx-auto max-w-5xl px-5 py-10">
            <div className="grad-divider mb-7" />
            <div className="flex flex-wrap items-center justify-between gap-4 text-[12.5px] text-[var(--fg-dim)]">
              <p>
                A research project by{" "}
                <a
                  href="https://github.com/Ace-2504"
                  target="_blank"
                  rel="noreferrer"
                  className="text-[var(--fg-muted)] hover:text-[var(--fg)]"
                >
                  Harman Sandhu
                </a>
                . Base pretrained from scratch on Modal; completions run live on a CPU endpoint.
              </p>
              <div className="flex gap-4">
                <Link href="/reports" className="hover:text-[var(--fg)]">
                  reports
                </Link>
                <Link href="/learnings" className="hover:text-[var(--fg)]">
                  learnings
                </Link>
                <a
                  href="https://huggingface.co/Ace-2504/fine-tuned-125m-slm"
                  target="_blank"
                  rel="noreferrer"
                  className="hover:text-[var(--fg)]"
                >
                  model
                </a>
              </div>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}

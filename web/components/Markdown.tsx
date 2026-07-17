import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/**
 * Renders a study markdown doc with the theme tokens. Numbers/tables get the mono
 * treatment; tables scroll on their own so the page body never scrolls sideways.
 */
export default function Markdown({ children }: { children: string }) {
  return (
    <div className="md">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: (p) => <h1 className="mb-3 text-[26px] font-semibold tracking-tight" {...p} />,
          h2: (p) => (
            <h2 className="mt-10 mb-3 text-[19px] font-semibold tracking-tight" {...p} />
          ),
          h3: (p) => <h3 className="mt-7 mb-2 text-[15px] font-semibold" {...p} />,
          p: (p) => <p className="my-3 leading-relaxed text-[var(--fg-muted)]" {...p} />,
          ul: (p) => <ul className="my-3 list-disc space-y-1.5 pl-5 text-[var(--fg-muted)]" {...p} />,
          ol: (p) => <ol className="my-3 list-decimal space-y-1.5 pl-5 text-[var(--fg-muted)]" {...p} />,
          li: (p) => <li className="leading-relaxed" {...p} />,
          strong: (p) => <strong className="font-semibold text-[var(--fg)]" {...p} />,
          a: (p) => (
            <a
              className="text-[var(--accent)] underline decoration-[var(--border)] underline-offset-2 hover:decoration-[var(--accent)]"
              {...p}
            />
          ),
          blockquote: (p) => (
            <blockquote
              className="panel-inset my-4 border-l-2 !border-l-[var(--accent)] px-4 py-3 text-[var(--fg-muted)]"
              {...p}
            />
          ),
          code: ({ children, ...rest }) => (
            <code
              className="mono rounded-md border border-[var(--border)] bg-[var(--panel-2)] px-1.5 py-0.5 text-[0.86em]"
              {...rest}
            >
              {children}
            </code>
          ),
          pre: (p) => (
            <pre
              className="panel-inset mono my-4 overflow-x-auto p-4 text-[12.5px] leading-relaxed text-[var(--fg-muted)]"
              {...p}
            />
          ),
          table: (p) => (
            <div className="my-5 overflow-x-auto">
              <table className="w-full border-collapse overflow-hidden rounded-xl border border-[var(--border)] text-[13.5px]" {...p} />
            </div>
          ),
          thead: (p) => <thead className="bg-[var(--panel-2)]" {...p} />,
          th: (p) => (
            <th
              className="mono border-b border-[var(--border)] px-3 py-2 text-left text-[11px] uppercase tracking-wider text-[var(--fg-muted)] font-medium"
              {...p}
            />
          ),
          td: (p) => (
            <td className="border-b border-[var(--border-soft)] px-3 py-2 align-top" {...p} />
          ),
          hr: () => <div className="hairline my-8" />,
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}

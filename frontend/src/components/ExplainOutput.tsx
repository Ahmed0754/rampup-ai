import type { ReactNode } from "react"
import type { ExplainResponse } from "../lib/api"

const TYPE_LABELS: Record<string, string> = {
  error: "Terminal Error",
  code: "Code",
  slack: "Slack Message",
  email: "Email",
  jira: "Jira Ticket",
  pr: "Pull Request",
  meeting_note: "Meeting Note",
  other: "Message",
}

// Code and errors get a debugging-oriented explanation; the section headings follow suit.
const HEADINGS: Record<string, { meaning: string; next: string; items: string }> = {
  code: { meaning: "What this code does", next: "Check this first", items: "Steps to dig in" },
  error: { meaning: "What this error means", next: "Check this first", items: "Debugging steps" },
}
const DEFAULT_HEADINGS = { meaning: "What this means", next: "What to do next", items: "Action items" }

// Code explanations wrap identifiers in `backticks`; show those as inline code.
function withInlineCode(text: string): ReactNode[] {
  return text.split(/`([^`\n]+)`/).map((part, i) =>
    i % 2 === 1 ? (
      <code key={i} className="rounded bg-white/10 px-1 py-0.5 font-mono text-[0.9em]">
        {part}
      </code>
    ) : (
      part
    ),
  )
}

interface ExplainOutputProps {
  result: ExplainResponse
  onGenerateReply: () => void
}

export default function ExplainOutput({ result, onGenerateReply }: ExplainOutputProps) {
  const headings = HEADINGS[result.input_type] ?? DEFAULT_HEADINGS
  const isCode = result.input_type in HEADINGS

  return (
    <div className="mt-6 space-y-4">
      <span className="inline-block rounded-full bg-accent/20 px-3 py-1 text-xs font-medium text-accent">
        {TYPE_LABELS[result.input_type] ?? result.input_type}
      </span>

      <div className="rounded-xl border border-border bg-panel p-5">
        <h3 className="mb-2 text-sm font-medium text-neutral-400">{headings.meaning}</h3>
        <p className="text-white">{withInlineCode(result.explanation)}</p>
        {isCode ? (
          <>
            <h3 className="mb-2 mt-4 text-sm font-medium text-neutral-400">
              {result.input_type === "error" ? "Most likely cause" : "Where it could break"}
            </h3>
            <p className="text-sm text-neutral-300">{withInlineCode(result.what_they_mean)}</p>
          </>
        ) : (
          <p className="mt-3 text-sm text-neutral-300">{withInlineCode(result.what_they_mean)}</p>
        )}
      </div>

      <div className="rounded-xl border border-accent/40 bg-accent/10 p-5">
        <h3 className="mb-2 text-sm font-medium text-accent">{headings.next}</h3>
        <p className="text-white">{withInlineCode(result.what_to_do_next)}</p>
      </div>

      <div className="rounded-xl border border-border bg-panel p-5">
        <h3 className="mb-3 text-sm font-medium text-neutral-400">{headings.items}</h3>
        <ul className="space-y-2">
          {result.action_items.map((item, i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-white">
              <input type="checkbox" className="mt-1 accent-accent" />
              {withInlineCode(item)}
            </li>
          ))}
        </ul>
      </div>

      <button
        type="button"
        onClick={onGenerateReply}
        className="w-full rounded-xl border border-accent px-4 py-3 font-medium text-accent transition hover:bg-accent hover:text-white"
      >
        Generate a reply
      </button>
    </div>
  )
}

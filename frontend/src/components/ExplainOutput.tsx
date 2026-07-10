import type { ExplainResponse } from "../lib/api"

const TYPE_LABELS: Record<string, string> = {
  error: "Terminal Error",
  slack: "Slack Message",
  email: "Email",
  jira: "Jira Ticket",
  pr: "Pull Request",
  meeting_note: "Meeting Note",
  other: "Message",
}

interface ExplainOutputProps {
  result: ExplainResponse
  onGenerateReply: () => void
}

export default function ExplainOutput({ result, onGenerateReply }: ExplainOutputProps) {
  return (
    <div className="mt-6 space-y-4">
      <span className="inline-block rounded-full bg-accent/20 px-3 py-1 text-xs font-medium text-accent">
        {TYPE_LABELS[result.input_type] ?? result.input_type}
      </span>

      <div className="rounded-xl border border-border bg-panel p-5">
        <h3 className="mb-2 text-sm font-medium text-neutral-400">What this means</h3>
        <p className="text-white">{result.explanation}</p>
        <p className="mt-3 text-sm text-neutral-300">{result.what_they_mean}</p>
      </div>

      <div className="rounded-xl border border-accent/40 bg-accent/10 p-5">
        <h3 className="mb-2 text-sm font-medium text-accent">What to do next</h3>
        <p className="text-white">{result.what_to_do_next}</p>
      </div>

      <div className="rounded-xl border border-border bg-panel p-5">
        <h3 className="mb-3 text-sm font-medium text-neutral-400">Action items</h3>
        <ul className="space-y-2">
          {result.action_items.map((item, i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-white">
              <input type="checkbox" className="mt-1 accent-accent" />
              {item}
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

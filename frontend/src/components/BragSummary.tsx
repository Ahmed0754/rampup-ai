import { useNavigate } from "react-router-dom"
import type { WeeklySummary } from "../lib/api"

interface BragSummaryProps {
  summary: WeeklySummary
}

export default function BragSummary({ summary }: BragSummaryProps) {
  const navigate = useNavigate()

  return (
    <div className="mt-6 space-y-4">
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-border bg-panel p-4">
          <h3 className="mb-2 text-sm font-medium text-neutral-400">What I worked on</h3>
          <p className="text-sm text-white">{summary.what_i_worked_on}</p>
        </div>
        <div className="rounded-xl border border-border bg-panel p-4">
          <h3 className="mb-2 text-sm font-medium text-neutral-400">What I learned</h3>
          <p className="text-sm text-white">{summary.what_i_learned}</p>
        </div>
        <div className="rounded-xl border border-border bg-panel p-4">
          <h3 className="mb-2 text-sm font-medium text-neutral-400">Blockers</h3>
          <p className="text-sm text-white">{summary.blockers}</p>
        </div>
      </div>

      <div className="rounded-xl border border-border bg-panel p-4">
        <h3 className="mb-2 text-sm font-medium text-neutral-400">Talking points for your review</h3>
        <p className="whitespace-pre-wrap text-sm text-white">{summary.talking_points}</p>
      </div>

      <div className="rounded-xl border border-accent/40 bg-accent/10 p-4">
        <h3 className="mb-2 text-sm font-medium text-accent">Resume bullets</h3>
        <ul className="list-disc space-y-1 pl-5 text-sm text-white">
          {summary.resume_bullets.map((bullet, i) => (
            <li key={i}>{bullet}</li>
          ))}
        </ul>
      </div>

      <button
        type="button"
        onClick={() => navigate("/resume", { state: { notes: summary.what_i_worked_on } })}
        className="w-full rounded-xl border border-accent px-4 py-3 font-medium text-accent transition hover:bg-accent hover:text-white"
      >
        Generate Resume Bullets
      </button>
    </div>
  )
}

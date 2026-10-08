import { useState } from "react"
import toast from "react-hot-toast"
import { errorDetail, generateStandup } from "../lib/api"
import type { StandupResponse } from "../lib/api"
import { getPreviousWorkdayStart } from "../lib/date"

const SECTIONS: { key: "yesterday" | "today" | "blockers"; title: string; empty: string }[] = [
  { key: "yesterday", title: "Yesterday", empty: "Nothing logged" },
  { key: "today", title: "Today", empty: "Nothing planned yet" },
  { key: "blockers", title: "Blockers", empty: "None" },
]

// Slack renders *bold*, and "•" bullets paste cleanly into Slack, Teams, and email alike.
function toPlainText(standup: StandupResponse): string {
  return SECTIONS.map(({ key, title, empty }) => {
    const items = standup[key].length ? standup[key] : [empty]
    return `*${title}*\n${items.map((item) => `• ${item}`).join("\n")}`
  }).join("\n\n")
}

export default function Standup() {
  const since = getPreviousWorkdayStart()
  const sinceLabel = since.toLocaleDateString(undefined, { weekday: "long" })

  const [notes, setNotes] = useState("")
  const [standup, setStandup] = useState<StandupResponse | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleGenerate() {
    setLoading(true)
    try {
      setStandup(await generateStandup(since, notes))
    } catch (err) {
      toast.error(errorDetail(err))
    } finally {
      setLoading(false)
    }
  }

  async function handleCopy() {
    if (!standup) return
    try {
      await navigator.clipboard.writeText(toPlainText(standup))
      toast.success("Copied — paste it into Slack")
    } catch {
      toast.error("Couldn't copy to clipboard")
    }
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="mb-2 text-2xl font-semibold text-white">Daily Standup</h1>
      <p className="mb-6 text-sm text-neutral-400">
        Built from what you've logged and had explained since {sinceLabel}. Add anything else you're planning
        today.
      </p>

      <textarea
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        placeholder="Optional: what are you working on today? Anything blocking you?"
        rows={3}
        maxLength={2000}
        className="w-full rounded-xl border border-border bg-panel px-4 py-3 text-sm text-white placeholder-neutral-600 outline-none focus:border-accent"
      />

      <button
        type="button"
        onClick={handleGenerate}
        disabled={loading}
        className="mt-3 w-full rounded-xl bg-accent px-4 py-3 font-medium text-white transition hover:bg-accent-hover disabled:opacity-60"
      >
        {loading ? "Writing your standup..." : standup ? "Regenerate" : "Generate Standup"}
      </button>

      {standup && (
        <div className="mt-6 space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-xs text-neutral-500">
              From {standup.entry_count} progress entr{standup.entry_count === 1 ? "y" : "ies"} and{" "}
              {standup.paste_count} explained message{standup.paste_count === 1 ? "" : "s"}
            </p>
            <button
              type="button"
              onClick={handleCopy}
              className="rounded-lg border border-border px-3 py-1.5 text-xs text-neutral-300 hover:text-white"
            >
              Copy for Slack
            </button>
          </div>

          {SECTIONS.map(({ key, title, empty }) => (
            <div
              key={key}
              className={`rounded-xl border p-4 ${
                key === "blockers" && standup.blockers.length
                  ? "border-red-400/40 bg-red-400/5"
                  : "border-border bg-panel"
              }`}
            >
              <h3 className="mb-2 text-sm font-medium text-neutral-400">{title}</h3>
              {standup[key].length ? (
                <ul className="list-disc space-y-1 pl-5 text-sm text-white">
                  {standup[key].map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-neutral-500">{empty}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

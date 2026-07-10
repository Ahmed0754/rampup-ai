import { useState } from "react"
import toast from "react-hot-toast"
import ProgressTracker from "../components/ProgressTracker.tsx"
import BragSummary from "../components/BragSummary.tsx"
import { generateWeeklySummary } from "../lib/api"
import type { WeeklySummary } from "../lib/api"
import { getCurrentWeekStart } from "../lib/date"

export default function Progress() {
  const [weekStart, setWeekStart] = useState(getCurrentWeekStart())
  const [summary, setSummary] = useState<WeeklySummary | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleGenerateSummary() {
    setLoading(true)
    setSummary(null)
    try {
      const data = await generateWeeklySummary(weekStart)
      setSummary(data)
    } catch (err) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Something went wrong"
      toast.error(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="mb-6 text-2xl font-semibold text-white">Progress Tracker</h1>
      <ProgressTracker weekStart={weekStart} onWeekStartChange={setWeekStart} />

      <button
        type="button"
        onClick={handleGenerateSummary}
        disabled={loading}
        className="mt-6 w-full rounded-xl bg-accent px-4 py-3 font-medium text-white transition hover:bg-accent-hover disabled:opacity-60"
      >
        {loading ? "Generating..." : "Generate Weekly Summary"}
      </button>

      {summary && <BragSummary summary={summary} />}
    </div>
  )
}

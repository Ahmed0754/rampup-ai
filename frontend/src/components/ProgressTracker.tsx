import { useEffect, useState } from "react"
import toast from "react-hot-toast"
import { createProgressEntry, listProgressEntries } from "../lib/api"
import type { EntryType, ProgressEntry } from "../lib/api"

const ENTRY_TYPES: { value: EntryType; label: string }[] = [
  { value: "win", label: "Win" },
  { value: "learned", label: "Learned" },
  { value: "blocker", label: "Blocker" },
  { value: "task_completed", label: "Task Completed" },
]

interface ProgressTrackerProps {
  weekStart: string
  onWeekStartChange: (weekStart: string) => void
  onEntriesChange?: (entries: ProgressEntry[]) => void
}

export default function ProgressTracker({ weekStart, onWeekStartChange, onEntriesChange }: ProgressTrackerProps) {
  const [entries, setEntries] = useState<ProgressEntry[]>([])
  const [entryText, setEntryText] = useState("")
  const [entryType, setEntryType] = useState<EntryType>("win")
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadEntries()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [weekStart])

  async function loadEntries() {
    try {
      const data = await listProgressEntries(weekStart)
      setEntries(data)
      onEntriesChange?.(data)
    } catch {
      toast.error("Could not load progress entries")
    }
  }

  async function handleAdd() {
    if (!entryText.trim()) {
      toast.error("Please paste some text first")
      return
    }
    setLoading(true)
    try {
      await createProgressEntry(entryText, entryType, weekStart)
      setEntryText("")
      await loadEntries()
    } catch {
      toast.error("Could not save entry")
    } finally {
      setLoading(false)
    }
  }

  const grouped = ENTRY_TYPES.map((t) => ({
    ...t,
    items: entries.filter((e) => e.entry_type === t.value),
  }))

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <label className="text-sm text-neutral-400">Week of</label>
        <input
          type="date"
          value={weekStart}
          onChange={(e) => onWeekStartChange(e.target.value)}
          className="rounded-lg border border-border bg-panel px-3 py-2 text-white outline-none focus:border-accent"
        />
      </div>

      <div className="flex flex-col gap-2 sm:flex-row">
        <input
          type="text"
          value={entryText}
          onChange={(e) => setEntryText(e.target.value)}
          placeholder="What happened?"
          className="flex-1 rounded-lg border border-border bg-panel px-3 py-2 text-white outline-none focus:border-accent"
        />
        <select
          value={entryType}
          onChange={(e) => setEntryType(e.target.value as EntryType)}
          className="rounded-lg border border-border bg-panel px-3 py-2 text-white outline-none focus:border-accent"
        >
          {ENTRY_TYPES.map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={handleAdd}
          disabled={loading}
          className="rounded-lg bg-accent px-4 py-2 font-medium text-white transition hover:bg-accent-hover disabled:opacity-60"
        >
          Add
        </button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {grouped.map((group) => (
          <div key={group.value} className="rounded-xl border border-border bg-panel p-4">
            <h3 className="mb-2 text-sm font-medium text-neutral-400">{group.label}</h3>
            {group.items.length === 0 ? (
              <p className="text-sm text-neutral-600">No entries yet</p>
            ) : (
              <ul className="space-y-2">
                {group.items.map((item) => (
                  <li key={item.id} className="text-sm text-white">
                    {item.entry_text}
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

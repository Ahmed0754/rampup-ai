import { useState } from "react"
import { Link } from "react-router-dom"
import toast from "react-hot-toast"
import { addMentorQuestions, errorDetail, suggestMentorQuestions } from "../lib/api"
import type { MentorQuestionInput } from "../lib/api"

interface MentorQuestionSuggestionsProps {
  pasteId: string
}

export default function MentorQuestionSuggestions({ pasteId }: MentorQuestionSuggestionsProps) {
  const [suggestions, setSuggestions] = useState<MentorQuestionInput[] | null>(null)
  const [selected, setSelected] = useState<Set<number>>(new Set())
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [savedCount, setSavedCount] = useState<number | null>(null)

  async function handleSuggest() {
    setLoading(true)
    try {
      const questions = await suggestMentorQuestions(pasteId)
      setSuggestions(questions)
      setSelected(new Set(questions.map((_, i) => i)))
    } catch (err) {
      toast.error(errorDetail(err))
    } finally {
      setLoading(false)
    }
  }

  function toggle(index: number) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(index)) next.delete(index)
      else next.add(index)
      return next
    })
  }

  async function handleSave() {
    if (!suggestions) return
    const questions = suggestions.filter((_, i) => selected.has(i)).map((q) => ({ ...q, paste_id: pasteId }))
    setSaving(true)
    try {
      const saved = await addMentorQuestions(questions)
      setSavedCount(saved.length)
    } catch (err) {
      toast.error(errorDetail(err))
    } finally {
      setSaving(false)
    }
  }

  if (savedCount !== null) {
    return (
      <p className="text-center text-sm text-neutral-400">
        Saved {savedCount} question{savedCount === 1 ? "" : "s"} to{" "}
        <Link to="/questions" className="text-accent hover:underline">
          Mentor Questions
        </Link>
        .
      </p>
    )
  }

  if (suggestions === null) {
    return (
      <button
        type="button"
        onClick={handleSuggest}
        disabled={loading}
        className="w-full rounded-xl border border-border px-4 py-3 text-sm text-neutral-300 transition hover:text-white disabled:opacity-60"
      >
        {loading ? "Thinking about what to ask..." : "Questions to ask my mentor"}
      </button>
    )
  }

  if (suggestions.length === 0) {
    return (
      <p className="text-center text-sm text-neutral-500">
        Nothing here needs a human — the explanation should cover it.
      </p>
    )
  }

  return (
    <div className="rounded-xl border border-border bg-panel p-5">
      <h3 className="mb-3 text-sm font-medium text-neutral-400">Save for your next 1:1</h3>
      <ul className="space-y-3">
        {suggestions.map((q, i) => (
          <li key={i}>
            <label className="flex cursor-pointer items-start gap-3">
              <input
                type="checkbox"
                checked={selected.has(i)}
                onChange={() => toggle(i)}
                className="mt-1 accent-accent"
              />
              <span>
                <span className="text-white">{q.question}</span>
                {q.context && <span className="block text-xs text-neutral-500">{q.context}</span>}
              </span>
            </label>
          </li>
        ))}
      </ul>
      <button
        type="button"
        onClick={handleSave}
        disabled={saving || selected.size === 0}
        className="mt-4 w-full rounded-xl bg-accent px-4 py-2.5 text-sm font-medium text-white transition hover:bg-accent-hover disabled:opacity-60"
      >
        {saving ? "Saving..." : `Save ${selected.size} question${selected.size === 1 ? "" : "s"}`}
      </button>
    </div>
  )
}

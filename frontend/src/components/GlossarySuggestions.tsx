import { useState } from "react"
import { Link } from "react-router-dom"
import toast from "react-hot-toast"
import { addGlossaryTerms, errorDetail, suggestGlossaryTerms } from "../lib/api"
import type { GlossaryTermInput } from "../lib/api"

interface GlossarySuggestionsProps {
  pasteId: string
}

export default function GlossarySuggestions({ pasteId }: GlossarySuggestionsProps) {
  const [suggestions, setSuggestions] = useState<GlossaryTermInput[] | null>(null)
  const [selected, setSelected] = useState<Set<number>>(new Set())
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [savedCount, setSavedCount] = useState<number | null>(null)

  async function handleFind() {
    setLoading(true)
    try {
      const terms = await suggestGlossaryTerms(pasteId)
      setSuggestions(terms)
      setSelected(new Set(terms.map((_, i) => i)))
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
    const terms = suggestions.filter((_, i) => selected.has(i)).map((t) => ({ ...t, paste_id: pasteId }))
    setSaving(true)
    try {
      const { saved } = await addGlossaryTerms(terms)
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
        Saved {savedCount} term{savedCount === 1 ? "" : "s"} to your{" "}
        <Link to="/glossary" className="text-accent hover:underline">
          glossary
        </Link>
        .
      </p>
    )
  }

  if (suggestions === null) {
    return (
      <button
        type="button"
        onClick={handleFind}
        disabled={loading}
        className="w-full rounded-xl border border-border px-4 py-3 text-sm text-neutral-300 transition hover:text-white disabled:opacity-60"
      >
        {loading ? "Looking for jargon..." : "Find jargon to save to my glossary"}
      </button>
    )
  }

  if (suggestions.length === 0) {
    return <p className="text-center text-sm text-neutral-500">No new jargon here — it's all in your glossary already.</p>
  }

  return (
    <div className="rounded-xl border border-border bg-panel p-5">
      <h3 className="mb-3 text-sm font-medium text-neutral-400">Save to your glossary</h3>
      <ul className="space-y-3">
        {suggestions.map((s, i) => (
          <li key={i}>
            <label className="flex cursor-pointer items-start gap-3">
              <input
                type="checkbox"
                checked={selected.has(i)}
                onChange={() => toggle(i)}
                className="mt-1 accent-accent"
              />
              <span>
                <span className="font-medium text-white">{s.term}</span>
                <span className="block text-sm text-neutral-300">{s.definition}</span>
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
        {saving ? "Saving..." : `Save ${selected.size} term${selected.size === 1 ? "" : "s"}`}
      </button>
    </div>
  )
}

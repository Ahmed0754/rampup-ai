import { useEffect, useState } from "react"
import toast from "react-hot-toast"
import { addGlossaryTerms, deleteGlossaryTerm, errorDetail, listGlossary, updateGlossaryTerm } from "../lib/api"
import type { GlossaryTerm } from "../lib/api"

const inputClass =
  "w-full rounded-lg border border-border bg-base px-3 py-2 text-sm text-white placeholder-neutral-600 focus:border-accent focus:outline-none"

function shuffle<T>(items: T[]): T[] {
  const copy = [...items]
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[copy[i], copy[j]] = [copy[j], copy[i]]
  }
  return copy
}

function Quiz({ terms, onExit }: { terms: GlossaryTerm[]; onExit: () => void }) {
  const [deck, setDeck] = useState(() => shuffle(terms))
  const [index, setIndex] = useState(0)
  const [revealed, setRevealed] = useState(false)
  const card = deck[index]
  const finished = index >= deck.length

  function next() {
    setRevealed(false)
    setIndex((i) => i + 1)
  }

  function restart() {
    setDeck(shuffle(terms))
    setIndex(0)
    setRevealed(false)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between text-sm text-neutral-500">
        <span>{finished ? "Done" : `Card ${index + 1} of ${deck.length}`}</span>
        <button type="button" onClick={onExit} className="hover:text-white">
          Back to glossary
        </button>
      </div>

      {finished ? (
        <div className="rounded-xl border border-border bg-panel p-8 text-center">
          <p className="mb-4 text-white">You went through all {deck.length} terms.</p>
          <button
            type="button"
            onClick={restart}
            className="rounded-xl bg-accent px-4 py-2.5 text-sm font-medium text-white hover:bg-accent-hover"
          >
            Shuffle and go again
          </button>
        </div>
      ) : (
        <div className="rounded-xl border border-border bg-panel p-8 text-center">
          <p className="text-2xl font-semibold text-white">{card.term}</p>
          {revealed ? (
            <>
              <p className="mt-4 text-neutral-300">{card.definition}</p>
              {card.context && <p className="mt-2 text-xs italic text-neutral-500">“{card.context}”</p>}
              <button
                type="button"
                onClick={next}
                className="mt-6 rounded-xl bg-accent px-4 py-2.5 text-sm font-medium text-white hover:bg-accent-hover"
              >
                Next
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={() => setRevealed(true)}
              className="mt-6 rounded-xl border border-accent px-4 py-2.5 text-sm font-medium text-accent hover:bg-accent hover:text-white"
            >
              Show definition
            </button>
          )}
        </div>
      )}
    </div>
  )
}

function TermRow({
  term,
  onChange,
  onDelete,
}: {
  term: GlossaryTerm
  onChange: (updated: GlossaryTerm) => void
  onDelete: () => void
}) {
  const [editing, setEditing] = useState(false)
  const [draftTerm, setDraftTerm] = useState(term.term)
  const [draftDefinition, setDraftDefinition] = useState(term.definition)
  const [busy, setBusy] = useState(false)

  async function handleSave() {
    const changes: { term?: string; definition?: string } = {}
    if (draftTerm.trim() !== term.term) changes.term = draftTerm
    if (draftDefinition.trim() !== term.definition) changes.definition = draftDefinition
    if (!Object.keys(changes).length) {
      setEditing(false)
      return
    }
    setBusy(true)
    try {
      onChange(await updateGlossaryTerm(term.id, changes))
      setEditing(false)
    } catch (err) {
      toast.error(errorDetail(err))
    } finally {
      setBusy(false)
    }
  }

  async function handleDelete() {
    if (!window.confirm(`Delete "${term.term}" from your glossary?`)) return
    setBusy(true)
    try {
      await deleteGlossaryTerm(term.id)
      onDelete()
    } catch (err) {
      toast.error(errorDetail(err))
      setBusy(false)
    }
  }

  if (editing) {
    return (
      <li className="space-y-2 rounded-xl border border-accent/40 bg-panel p-4">
        <input value={draftTerm} onChange={(e) => setDraftTerm(e.target.value)} className={inputClass} />
        <textarea
          value={draftDefinition}
          onChange={(e) => setDraftDefinition(e.target.value)}
          rows={3}
          className={inputClass}
        />
        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={() => {
              setDraftTerm(term.term)
              setDraftDefinition(term.definition)
              setEditing(false)
            }}
            className="rounded-lg px-3 py-1.5 text-xs text-neutral-400 hover:text-white"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={busy || !draftTerm.trim() || !draftDefinition.trim()}
            className="rounded-lg bg-accent px-3 py-1.5 text-xs font-medium text-white hover:bg-accent-hover disabled:opacity-60"
          >
            Save
          </button>
        </div>
      </li>
    )
  }

  return (
    <li className="group rounded-xl border border-border bg-panel p-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-medium text-white">{term.term}</p>
          <p className="mt-1 text-sm text-neutral-300">{term.definition}</p>
          {term.context && <p className="mt-2 text-xs italic text-neutral-500">“{term.context}”</p>}
        </div>
        <div className="flex flex-shrink-0 gap-2 text-xs text-neutral-500">
          <button type="button" onClick={() => setEditing(true)} className="hover:text-white">
            Edit
          </button>
          <button type="button" onClick={handleDelete} disabled={busy} className="hover:text-red-400">
            Delete
          </button>
        </div>
      </div>
    </li>
  )
}

export default function Glossary() {
  const [terms, setTerms] = useState<GlossaryTerm[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")
  const [newTerm, setNewTerm] = useState("")
  const [newDefinition, setNewDefinition] = useState("")
  const [adding, setAdding] = useState(false)
  const [quizzing, setQuizzing] = useState(false)

  useEffect(() => {
    listGlossary()
      .then(setTerms)
      .catch((err) => toast.error(errorDetail(err)))
      .finally(() => setLoading(false))
  }, [])

  const query = search.trim().toLowerCase()
  const visible = query
    ? terms.filter((t) => `${t.term} ${t.definition}`.toLowerCase().includes(query))
    : terms

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault()
    if (!newTerm.trim() || !newDefinition.trim()) return
    setAdding(true)
    try {
      const { saved } = await addGlossaryTerms([{ term: newTerm, definition: newDefinition }])
      if (!saved.length) {
        toast.error(`"${newTerm.trim()}" is already in your glossary`)
        return
      }
      setTerms((prev) => [...prev, ...saved].sort((a, b) => a.term.localeCompare(b.term)))
      setNewTerm("")
      setNewDefinition("")
    } catch (err) {
      toast.error(errorDetail(err))
    } finally {
      setAdding(false)
    }
  }

  if (quizzing) {
    return (
      <div className="mx-auto max-w-2xl">
        <h1 className="mb-6 text-2xl font-semibold text-white">Glossary quiz</h1>
        <Quiz terms={terms} onExit={() => setQuizzing(false)} />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-2xl">
      <div className="mb-2 flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-white">Glossary</h1>
        {terms.length > 0 && (
          <button
            type="button"
            onClick={() => setQuizzing(true)}
            className="rounded-lg border border-accent px-3 py-1.5 text-sm text-accent transition hover:bg-accent hover:text-white"
          >
            Quiz me
          </button>
        )}
      </div>
      <p className="mb-6 text-sm text-neutral-400">
        Jargon you've run into, in plain English. Save terms from any explanation with “Find jargon”, or add your
        own.
      </p>

      <form onSubmit={handleAdd} className="mb-6 space-y-2 rounded-xl border border-border bg-panel p-4">
        <input
          value={newTerm}
          onChange={(e) => setNewTerm(e.target.value)}
          placeholder="Term (e.g. LGTM)"
          className={inputClass}
        />
        <textarea
          value={newDefinition}
          onChange={(e) => setNewDefinition(e.target.value)}
          placeholder="What it means"
          rows={2}
          className={inputClass}
        />
        <button
          type="submit"
          disabled={adding || !newTerm.trim() || !newDefinition.trim()}
          className="w-full rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white transition hover:bg-accent-hover disabled:opacity-60"
        >
          {adding ? "Adding..." : "Add term"}
        </button>
      </form>

      {terms.length > 0 && (
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder={`Search ${terms.length} term${terms.length === 1 ? "" : "s"}...`}
          className={`${inputClass} mb-4`}
        />
      )}

      {loading ? (
        <p className="text-sm text-neutral-500">Loading...</p>
      ) : terms.length === 0 ? (
        <p className="text-center text-sm text-neutral-500">
          Nothing here yet. Explain something on the Explain This page, then click “Find jargon”.
        </p>
      ) : visible.length === 0 ? (
        <p className="text-center text-sm text-neutral-500">No terms match “{search}”.</p>
      ) : (
        <ul className="space-y-3">
          {visible.map((term) => (
            <TermRow
              key={term.id}
              term={term}
              onChange={(updated) =>
                setTerms((prev) =>
                  prev.map((t) => (t.id === updated.id ? updated : t)).sort((a, b) => a.term.localeCompare(b.term)),
                )
              }
              onDelete={() => setTerms((prev) => prev.filter((t) => t.id !== term.id))}
            />
          ))}
        </ul>
      )}
    </div>
  )
}

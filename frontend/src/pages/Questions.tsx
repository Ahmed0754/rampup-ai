import { useEffect, useState } from "react"
import toast from "react-hot-toast"
import {
  addMentorQuestions,
  deleteMentorQuestion,
  errorDetail,
  listMentorQuestions,
  updateMentorQuestion,
} from "../lib/api"
import type { MentorQuestion } from "../lib/api"
import { formatDateTime } from "../lib/date"

const inputClass =
  "w-full rounded-lg border border-border bg-base px-3 py-2 text-sm text-white placeholder-neutral-600 focus:border-accent focus:outline-none"

function OpenQuestion({
  question,
  onChange,
  onDelete,
}: {
  question: MentorQuestion
  onChange: (updated: MentorQuestion) => void
  onDelete: () => void
}) {
  const [mode, setMode] = useState<"view" | "edit" | "answer">("view")
  const [draft, setDraft] = useState(question.question)
  const [answer, setAnswer] = useState("")
  const [busy, setBusy] = useState(false)

  async function save(changes: { question?: string; answered?: boolean; answer?: string }) {
    setBusy(true)
    try {
      onChange(await updateMentorQuestion(question.id, changes))
      setMode("view")
    } catch (err) {
      toast.error(errorDetail(err))
    } finally {
      setBusy(false)
    }
  }

  async function handleDelete() {
    if (!window.confirm("Delete this question?")) return
    setBusy(true)
    try {
      await deleteMentorQuestion(question.id)
      onDelete()
    } catch (err) {
      toast.error(errorDetail(err))
      setBusy(false)
    }
  }

  if (mode === "edit") {
    return (
      <li className="space-y-2 rounded-xl border border-accent/40 bg-panel p-4">
        <textarea value={draft} onChange={(e) => setDraft(e.target.value)} rows={2} className={inputClass} />
        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={() => {
              setDraft(question.question)
              setMode("view")
            }}
            className="rounded-lg px-3 py-1.5 text-xs text-neutral-400 hover:text-white"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={() => save({ question: draft })}
            disabled={busy || !draft.trim()}
            className="rounded-lg bg-accent px-3 py-1.5 text-xs font-medium text-white hover:bg-accent-hover disabled:opacity-60"
          >
            Save
          </button>
        </div>
      </li>
    )
  }

  return (
    <li className="rounded-xl border border-border bg-panel p-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-white">{question.question}</p>
          {question.context && <p className="mt-1 text-xs text-neutral-500">{question.context}</p>}
        </div>
        {mode === "view" && (
          <div className="flex flex-shrink-0 gap-3 text-xs text-neutral-500">
            <button type="button" onClick={() => setMode("answer")} className="text-accent hover:underline">
              Answered
            </button>
            <button type="button" onClick={() => setMode("edit")} className="hover:text-white">
              Edit
            </button>
            <button type="button" onClick={handleDelete} disabled={busy} className="hover:text-red-400">
              Delete
            </button>
          </div>
        )}
      </div>

      {mode === "answer" && (
        <div className="mt-3 space-y-2">
          <textarea
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder="Optional: what did you learn? Future you will want this."
            rows={2}
            autoFocus
            className={inputClass}
          />
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setMode("view")}
              className="rounded-lg px-3 py-1.5 text-xs text-neutral-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={() => save({ answered: true, answer })}
              disabled={busy}
              className="rounded-lg bg-accent px-3 py-1.5 text-xs font-medium text-white hover:bg-accent-hover disabled:opacity-60"
            >
              Mark answered
            </button>
          </div>
        </div>
      )}
    </li>
  )
}

function AnsweredQuestion({
  question,
  onChange,
  onDelete,
}: {
  question: MentorQuestion
  onChange: (updated: MentorQuestion) => void
  onDelete: () => void
}) {
  const [busy, setBusy] = useState(false)

  async function handleReopen() {
    setBusy(true)
    try {
      onChange(await updateMentorQuestion(question.id, { answered: false }))
    } catch (err) {
      toast.error(errorDetail(err))
    } finally {
      setBusy(false)
    }
  }

  async function handleDelete() {
    if (!window.confirm("Delete this question?")) return
    setBusy(true)
    try {
      await deleteMentorQuestion(question.id)
      onDelete()
    } catch (err) {
      toast.error(errorDetail(err))
      setBusy(false)
    }
  }

  return (
    <li className="rounded-xl border border-border bg-panel/50 p-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-neutral-300">{question.question}</p>
          {question.answer && <p className="mt-2 text-sm text-white">{question.answer}</p>}
          {question.answered_at && (
            <p className="mt-1 text-xs text-neutral-600">Answered {formatDateTime(question.answered_at)}</p>
          )}
        </div>
        <div className="flex flex-shrink-0 gap-3 text-xs text-neutral-500">
          <button type="button" onClick={handleReopen} disabled={busy} className="hover:text-white">
            Reopen
          </button>
          <button type="button" onClick={handleDelete} disabled={busy} className="hover:text-red-400">
            Delete
          </button>
        </div>
      </div>
    </li>
  )
}

export default function Questions() {
  const [questions, setQuestions] = useState<MentorQuestion[]>([])
  const [loading, setLoading] = useState(true)
  const [newQuestion, setNewQuestion] = useState("")
  const [adding, setAdding] = useState(false)
  const [showAnswered, setShowAnswered] = useState(false)

  useEffect(() => {
    listMentorQuestions()
      .then(setQuestions)
      .catch((err) => toast.error(errorDetail(err)))
      .finally(() => setLoading(false))
  }, [])

  const open = questions.filter((q) => !q.answered_at)
  const answered = questions
    .filter((q) => q.answered_at)
    .sort((a, b) => (b.answered_at ?? "").localeCompare(a.answered_at ?? ""))

  function replace(updated: MentorQuestion) {
    setQuestions((prev) => prev.map((q) => (q.id === updated.id ? updated : q)))
  }

  function remove(id: string) {
    setQuestions((prev) => prev.filter((q) => q.id !== id))
  }

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault()
    if (!newQuestion.trim()) return
    setAdding(true)
    try {
      const saved = await addMentorQuestions([{ question: newQuestion }])
      setQuestions((prev) => [...prev, ...saved])
      setNewQuestion("")
    } catch (err) {
      toast.error(errorDetail(err))
    } finally {
      setAdding(false)
    }
  }

  async function handleCopyAgenda() {
    const agenda = open.map((q, i) => `${i + 1}. ${q.question}`).join("\n")
    try {
      await navigator.clipboard.writeText(agenda)
      toast.success("Copied your 1:1 agenda")
    } catch {
      toast.error("Couldn't copy to clipboard")
    }
  }

  return (
    <div className="mx-auto max-w-2xl">
      <div className="mb-2 flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-white">Mentor Questions</h1>
        {open.length > 0 && (
          <button
            type="button"
            onClick={handleCopyAgenda}
            className="rounded-lg border border-border px-3 py-1.5 text-xs text-neutral-300 hover:text-white"
          >
            Copy 1:1 agenda
          </button>
        )}
      </div>
      <p className="mb-6 text-sm text-neutral-400">
        Questions to bring to your next 1:1 — the ones only someone on your team can answer. Save them from any
        explanation, or jot them down here.
      </p>

      <form onSubmit={handleAdd} className="mb-6 flex gap-2">
        <input
          value={newQuestion}
          onChange={(e) => setNewQuestion(e.target.value)}
          placeholder="e.g. Who should I ask about the deploy pipeline?"
          maxLength={1000}
          className={inputClass}
        />
        <button
          type="submit"
          disabled={adding || !newQuestion.trim()}
          className="flex-shrink-0 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white transition hover:bg-accent-hover disabled:opacity-60"
        >
          Add
        </button>
      </form>

      {loading ? (
        <p className="text-sm text-neutral-500">Loading...</p>
      ) : (
        <>
          <h2 className="mb-3 text-sm font-medium text-neutral-400">Open ({open.length})</h2>
          {open.length === 0 ? (
            <p className="mb-6 text-sm text-neutral-500">
              No open questions. After an explanation on Explain This, click “Questions to ask my mentor”.
            </p>
          ) : (
            <ul className="mb-6 space-y-3">
              {open.map((q) => (
                <OpenQuestion key={q.id} question={q} onChange={replace} onDelete={() => remove(q.id)} />
              ))}
            </ul>
          )}

          {answered.length > 0 && (
            <>
              <button
                type="button"
                onClick={() => setShowAnswered((v) => !v)}
                className="mb-3 text-sm font-medium text-neutral-400 hover:text-white"
              >
                {showAnswered ? "▾" : "▸"} Answered ({answered.length})
              </button>
              {showAnswered && (
                <ul className="space-y-3">
                  {answered.map((q) => (
                    <AnsweredQuestion key={q.id} question={q} onChange={replace} onDelete={() => remove(q.id)} />
                  ))}
                </ul>
              )}
            </>
          )}
        </>
      )}
    </div>
  )
}

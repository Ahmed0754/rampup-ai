import { useState } from "react"
import toast from "react-hot-toast"
import { explainChatStream } from "../lib/api"

interface ChatMessage {
  role: "user" | "assistant"
  content: string
}

interface ExplainChatProps {
  pasteId: string
}

export default function ExplainChat({ pasteId }: ExplainChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [question, setQuestion] = useState("")
  const [loading, setLoading] = useState(false)

  async function handleAsk() {
    const trimmed = question.trim()
    if (!trimmed) {
      toast.error("Please enter a question")
      return
    }

    setMessages((prev) => [...prev, { role: "user", content: trimmed }, { role: "assistant", content: "" }])
    setQuestion("")
    setLoading(true)
    try {
      const data = await explainChatStream(pasteId, trimmed, (chunk) => {
        setMessages((prev) => {
          const next = [...prev]
          next[next.length - 1] = { role: "assistant", content: next[next.length - 1].content + chunk }
          return next
        })
      })
      if (!data.saved) {
        toast("Couldn't save this to your history", { icon: "⚠️" })
      }
    } catch (err) {
      setMessages((prev) => prev.slice(0, -1)) // drop the empty assistant bubble
      toast.error(err instanceof Error ? err.message : "Something went wrong")
    } finally {
      setLoading(false)
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" && !loading) {
      e.preventDefault()
      void handleAsk()
    }
  }

  return (
    <div className="rounded-xl border border-border bg-panel p-5">
      <h3 className="mb-3 text-sm font-medium text-neutral-400">Ask a follow-up</h3>

      {messages.length > 0 && (
        <div className="mb-4 space-y-3">
          {messages.map((m, i) => (
            <div
              key={i}
              className={
                m.role === "user"
                  ? "ml-8 rounded-lg bg-accent/20 px-3 py-2 text-sm text-white"
                  : "mr-8 rounded-lg bg-white/5 px-3 py-2 text-sm text-neutral-200"
              }
            >
              {m.content || (loading && i === messages.length - 1 ? "…" : "")}
            </div>
          ))}
        </div>
      )}

      <div className="flex gap-2">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Wait, what does that mean?"
          disabled={loading}
          className="flex-1 rounded-lg border border-border bg-base px-3 py-2 text-sm text-white outline-none focus:border-accent disabled:opacity-60"
        />
        <button
          type="button"
          onClick={handleAsk}
          disabled={loading}
          className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white transition hover:bg-accent-hover disabled:opacity-60"
        >
          {loading ? "…" : "Ask"}
        </button>
      </div>
    </div>
  )
}

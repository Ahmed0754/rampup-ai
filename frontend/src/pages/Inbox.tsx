import { useState } from "react"
import { useNavigate } from "react-router-dom"
import toast from "react-hot-toast"
import PasteInbox from "../components/PasteInbox.tsx"
import ExplainOutput from "../components/ExplainOutput.tsx"
import { explainTextStream } from "../lib/api"
import type { ExplainResponse } from "../lib/api"

export default function Inbox() {
  const navigate = useNavigate()
  const [text, setText] = useState("")
  const [loading, setLoading] = useState(false)
  const [streamText, setStreamText] = useState("")
  const [result, setResult] = useState<ExplainResponse | null>(null)

  async function handleSubmit() {
    if (!text.trim()) {
      toast.error("Please paste some text first")
      return
    }
    setLoading(true)
    setResult(null)
    setStreamText("")
    try {
      const data = await explainTextStream(text, (chunk) => setStreamText((s) => s + chunk))
      setResult(data)
      if (!data.saved) {
        toast("Couldn't save this to your history", { icon: "⚠️" })
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Something went wrong")
    } finally {
      setLoading(false)
    }
  }

  function handleGenerateReply() {
    navigate("/reply", { state: { originalText: text, pasteId: result?.paste_id } })
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="mb-6 text-2xl font-semibold text-white">Explain This</h1>
      <PasteInbox text={text} onTextChange={setText} onSubmit={handleSubmit} loading={loading} />
      {loading && !result && streamText && (
        <pre className="mt-6 whitespace-pre-wrap rounded-xl border border-border bg-panel p-4 font-sans text-sm text-neutral-400">
          {streamText}
        </pre>
      )}
      {result && <ExplainOutput result={result} onGenerateReply={handleGenerateReply} />}
    </div>
  )
}

import { useState } from "react"
import { useNavigate } from "react-router-dom"
import toast from "react-hot-toast"
import PasteInbox from "../components/PasteInbox.tsx"
import ExplainOutput from "../components/ExplainOutput.tsx"
import { explainText } from "../lib/api"
import type { ExplainResponse } from "../lib/api"

export default function Inbox() {
  const navigate = useNavigate()
  const [text, setText] = useState("")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ExplainResponse | null>(null)

  async function handleSubmit() {
    if (!text.trim()) {
      toast.error("Please paste some text first")
      return
    }
    setLoading(true)
    setResult(null)
    try {
      const data = await explainText(text)
      setResult(data)
    } catch (err) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Something went wrong"
      toast.error(message)
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
      {result && <ExplainOutput result={result} onGenerateReply={handleGenerateReply} />}
    </div>
  )
}

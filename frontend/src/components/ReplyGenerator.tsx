import { useState } from "react"
import toast from "react-hot-toast"
import { generateReply } from "../lib/api"
import type { Tone } from "../lib/api"

const TONES: { value: Tone; label: string }[] = [
  { value: "casual", label: "Casual" },
  { value: "professional", label: "Professional" },
  { value: "manager-safe", label: "Manager-Safe" },
  { value: "confused-but-trying", label: "Confused But Trying" },
]

interface ReplyGeneratorProps {
  originalText: string
  pasteId?: string
}

export default function ReplyGenerator({ originalText, pasteId }: ReplyGeneratorProps) {
  const [tone, setTone] = useState<Tone>("professional")
  const [loading, setLoading] = useState(false)
  const [reply, setReply] = useState("")

  async function handleGenerate() {
    if (!originalText.trim()) {
      toast.error("Please paste some text first")
      return
    }
    setLoading(true)
    try {
      const data = await generateReply(originalText, tone, pasteId)
      setReply(data.reply)
      if (!data.saved) {
        toast("Couldn't save this to your history", { icon: "⚠️" })
      }
    } catch (err) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Something went wrong"
      toast.error(message)
    } finally {
      setLoading(false)
    }
  }

  async function handleCopy() {
    await navigator.clipboard.writeText(reply)
    toast.success("Copied to clipboard")
  }

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-border bg-panel p-4">
        <h3 className="mb-2 text-sm font-medium text-neutral-400">Original message</h3>
        <p className="whitespace-pre-wrap text-sm text-neutral-200">{originalText || "No message provided"}</p>
      </div>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        {TONES.map((t) => (
          <button
            key={t.value}
            type="button"
            onClick={() => setTone(t.value)}
            className={`rounded-lg px-3 py-2 text-sm transition ${
              tone === t.value
                ? "bg-accent font-medium text-white"
                : "border border-border bg-panel text-neutral-300 hover:text-white"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <button
        type="button"
        onClick={handleGenerate}
        disabled={loading}
        className="w-full rounded-xl bg-accent px-4 py-3 font-medium text-white transition hover:bg-accent-hover disabled:opacity-60"
      >
        {loading ? "Generating..." : "Generate Reply"}
      </button>

      {reply && (
        <div className="rounded-xl border border-border bg-panel p-4">
          <p className="mb-4 whitespace-pre-wrap text-white">{reply}</p>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleCopy}
              className="rounded-lg border border-border px-3 py-2 text-sm text-neutral-300 hover:text-white"
            >
              Copy
            </button>
            <button
              type="button"
              onClick={handleGenerate}
              disabled={loading}
              className="rounded-lg border border-border px-3 py-2 text-sm text-neutral-300 hover:text-white"
            >
              Regenerate
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

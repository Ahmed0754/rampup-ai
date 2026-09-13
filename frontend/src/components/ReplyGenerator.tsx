import { useState } from "react"
import toast from "react-hot-toast"
import { generateReplyStream } from "../lib/api"
import type { Tone } from "../lib/api"

const TONES: { value: Tone; label: string }[] = [
  { value: "casual", label: "Casual" },
  { value: "professional", label: "Professional" },
  { value: "manager-safe", label: "Manager-Safe" },
  { value: "confused-but-trying", label: "Confused But Trying" },
]

interface ToneResult {
  tone: Tone
  text: string
  loading: boolean
  error?: string
}

interface ReplyGeneratorProps {
  originalText: string
  pasteId?: string
}

export default function ReplyGenerator({ originalText, pasteId }: ReplyGeneratorProps) {
  const [tone, setTone] = useState<Tone>("professional")
  const [loading, setLoading] = useState(false)
  const [reply, setReply] = useState("")
  const [compareResults, setCompareResults] = useState<ToneResult[] | null>(null)
  const [compareLoading, setCompareLoading] = useState(false)

  async function handleGenerate() {
    if (!originalText.trim()) {
      toast.error("Please paste some text first")
      return
    }
    setCompareResults(null)
    setLoading(true)
    setReply("")
    try {
      const data = await generateReplyStream(originalText, tone, pasteId, (chunk) => setReply((r) => r + chunk))
      setReply(data.reply)
      if (!data.saved) {
        toast("Couldn't save this to your history", { icon: "⚠️" })
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Something went wrong")
    } finally {
      setLoading(false)
    }
  }

  async function handleCompareAll() {
    if (!originalText.trim()) {
      toast.error("Please paste some text first")
      return
    }
    setReply("")
    setCompareLoading(true)
    setCompareResults(TONES.map((t) => ({ tone: t.value, text: "", loading: true })))

    let failedToSave = 0
    await Promise.all(
      TONES.map(async (t, i) => {
        try {
          const data = await generateReplyStream(originalText, t.value, pasteId, (chunk) => {
            setCompareResults((prev) => {
              if (!prev) return prev
              const next = [...prev]
              next[i] = { ...next[i], text: next[i].text + chunk }
              return next
            })
          })
          if (!data.saved) failedToSave += 1
          setCompareResults((prev) => {
            if (!prev) return prev
            const next = [...prev]
            next[i] = { ...next[i], text: data.reply, loading: false }
            return next
          })
        } catch (err) {
          setCompareResults((prev) => {
            if (!prev) return prev
            const next = [...prev]
            next[i] = {
              ...next[i],
              loading: false,
              error: err instanceof Error ? err.message : "Something went wrong",
            }
            return next
          })
        }
      }),
    )
    setCompareLoading(false)
    if (failedToSave > 0) {
      toast(`${failedToSave} repl${failedToSave === 1 ? "y" : "ies"} couldn't be saved to your history`, {
        icon: "⚠️",
      })
    }
  }

  async function handleCopy(text: string) {
    await navigator.clipboard.writeText(text)
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

      <div className="flex gap-2">
        <button
          type="button"
          onClick={handleGenerate}
          disabled={loading || compareLoading}
          className="flex-1 rounded-xl bg-accent px-4 py-3 font-medium text-white transition hover:bg-accent-hover disabled:opacity-60"
        >
          {loading ? "Generating..." : "Generate Reply"}
        </button>
        <button
          type="button"
          onClick={handleCompareAll}
          disabled={loading || compareLoading}
          className="flex-1 rounded-xl border border-accent px-4 py-3 font-medium text-accent transition hover:bg-accent hover:text-white disabled:opacity-60"
        >
          {compareLoading ? "Comparing..." : "Compare All Tones"}
        </button>
      </div>

      {reply && (
        <div className="rounded-xl border border-border bg-panel p-4">
          <p className="mb-4 whitespace-pre-wrap text-white">{reply}</p>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => handleCopy(reply)}
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

      {compareResults && (
        <div className="grid gap-4 sm:grid-cols-2">
          {compareResults.map((r) => {
            const label = TONES.find((t) => t.value === r.tone)?.label ?? r.tone
            return (
              <div key={r.tone} className="rounded-xl border border-border bg-panel p-4">
                <div className="mb-2 flex items-center justify-between">
                  <span className="rounded-full bg-accent/20 px-2 py-0.5 text-xs font-medium text-accent">
                    {label}
                  </span>
                  {r.loading && (
                    <span className="h-3 w-3 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                  )}
                </div>
                {r.error ? (
                  <p className="text-sm text-red-400">{r.error}</p>
                ) : (
                  <>
                    <p className="mb-3 whitespace-pre-wrap text-sm text-white">{r.text}</p>
                    {!r.loading && r.text && (
                      <button
                        type="button"
                        onClick={() => handleCopy(r.text)}
                        className="rounded-lg border border-border px-3 py-1.5 text-xs text-neutral-300 hover:text-white"
                      >
                        Copy
                      </button>
                    )}
                  </>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

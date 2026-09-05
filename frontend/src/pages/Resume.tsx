import { useState } from "react"
import { useLocation } from "react-router-dom"
import toast from "react-hot-toast"
import ResumeBullet from "../components/ResumeBullet.tsx"
import { generateResumeBulletsStream } from "../lib/api"

interface ResumeLocationState {
  notes?: string
}

export default function Resume() {
  const location = useLocation()
  const state = (location.state as ResumeLocationState) ?? {}

  const [description, setDescription] = useState(state.notes ?? "")
  const [loading, setLoading] = useState(false)
  const [streamText, setStreamText] = useState("")
  const [bullets, setBullets] = useState<string[]>([])

  async function handleGenerate() {
    if (!description.trim()) {
      toast.error("Please paste some text first")
      return
    }
    setLoading(true)
    setBullets([])
    setStreamText("")
    try {
      const data = await generateResumeBulletsStream(description, (chunk) => setStreamText((s) => s + chunk))
      setBullets(data.bullets)
      if (!data.saved) {
        toast("Couldn't save this to your history", { icon: "⚠️" })
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Something went wrong")
    } finally {
      setLoading(false)
    }
  }

  async function handleCopyAll() {
    await navigator.clipboard.writeText(bullets.join("\n"))
    toast.success("Copied all bullets")
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="mb-6 text-2xl font-semibold text-white">Resume Bullets</h1>

      <textarea
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        placeholder="Jot down rough notes about what you worked on..."
        rows={8}
        className="w-full resize-none rounded-xl border border-border bg-panel p-4 text-white outline-none focus:border-accent"
      />

      <button
        type="button"
        onClick={handleGenerate}
        disabled={loading}
        className="mt-4 w-full rounded-xl bg-accent px-4 py-3 font-medium text-white transition hover:bg-accent-hover disabled:opacity-60"
      >
        {loading ? "Generating..." : "Generate Bullets"}
      </button>

      {loading && bullets.length === 0 && streamText && (
        <pre className="mt-6 whitespace-pre-wrap rounded-xl border border-border bg-panel p-4 font-sans text-sm text-neutral-400">
          {streamText}
        </pre>
      )}

      {bullets.length > 0 && (
        <div className="mt-6 space-y-4">
          <ul className="space-y-2">
            {bullets.map((bullet, i) => (
              <ResumeBullet key={i} bullet={bullet} />
            ))}
          </ul>
          <button
            type="button"
            onClick={handleCopyAll}
            className="w-full rounded-xl border border-accent px-4 py-3 font-medium text-accent transition hover:bg-accent hover:text-white"
          >
            Copy All
          </button>
        </div>
      )}
    </div>
  )
}

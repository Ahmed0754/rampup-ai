import { useState } from "react"
import toast from "react-hot-toast"
import { generateInternshipRecap } from "../lib/api"
import type { InternshipRecapResponse } from "../lib/api"
import { buildInternshipRecapMarkdown, downloadTextFile } from "../lib/export"

function RecapList({ title, items }: { title: string; items: string[] }) {
  if (!items.length) return null
  return (
    <div className="rounded-xl border border-border bg-panel p-4">
      <h3 className="mb-2 text-sm font-medium text-neutral-400">{title}</h3>
      <ul className="list-disc space-y-1 pl-5 text-sm text-white">
        {items.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>
    </div>
  )
}

export default function Recap() {
  const [result, setResult] = useState<InternshipRecapResponse | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleGenerate() {
    setLoading(true)
    try {
      setResult(await generateInternshipRecap())
    } catch (err) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Something went wrong"
      toast.error(message)
    } finally {
      setLoading(false)
    }
  }

  function handleExportMarkdown() {
    if (!result) return
    downloadTextFile(`internship-recap-${result.last_week}.md`, buildInternshipRecapMarkdown(result))
  }

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="mb-2 text-2xl font-semibold text-white">Internship Recap</h1>
      <p className="mb-6 text-sm text-neutral-400">
        Turn everything you've logged in the Progress Tracker into one summary of your whole internship — for your
        final review, a return-offer conversation, or your resume.
      </p>

      <button
        type="button"
        onClick={handleGenerate}
        disabled={loading}
        className="w-full rounded-xl bg-accent px-4 py-3 font-medium text-white transition hover:bg-accent-hover disabled:opacity-60"
      >
        {loading ? "Reading your progress log..." : result ? "Regenerate Recap" : "Generate Recap"}
      </button>

      {result && (
        <div className="mt-6 space-y-4">
          <div className="flex items-center justify-between gap-2">
            <p className="text-xs text-neutral-500">
              {result.entry_count} entries across {result.weeks_covered} week{result.weeks_covered === 1 ? "" : "s"}{" "}
              ({result.first_week} to {result.last_week})
            </p>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={handleExportMarkdown}
                className="rounded-lg border border-border px-3 py-1.5 text-xs text-neutral-300 hover:text-white"
              >
                Export Markdown
              </button>
              <button
                type="button"
                onClick={() => window.print()}
                className="rounded-lg border border-border px-3 py-1.5 text-xs text-neutral-300 hover:text-white"
              >
                Print / Save as PDF
              </button>
            </div>
          </div>

          <div id="printable-area" className="space-y-4">
            <div className="rounded-xl border border-border bg-panel p-4">
              <h3 className="mb-2 text-sm font-medium text-neutral-400">Overview</h3>
              <p className="whitespace-pre-wrap text-sm text-white">{result.recap.headline}</p>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <RecapList title="Highlights" items={result.recap.highlights} />
              <RecapList title="Skills I picked up" items={result.recap.skills_learned} />
            </div>

            <RecapList title="Challenges I worked through" items={result.recap.challenges_overcome} />
            <RecapList title="Talking points for your final review" items={result.recap.talking_points} />

            <div className="rounded-xl border border-accent/40 bg-accent/10 p-4">
              <h3 className="mb-2 text-sm font-medium text-accent">Resume bullets</h3>
              <ul className="list-disc space-y-1 pl-5 text-sm text-white">
                {result.recap.resume_bullets.map((bullet, i) => (
                  <li key={i}>{bullet}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

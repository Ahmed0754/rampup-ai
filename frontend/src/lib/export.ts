import type { WeeklySummary } from "./api"

export function downloadTextFile(filename: string, content: string, mimeType = "text/markdown;charset=utf-8"): void {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export function buildWeeklySummaryMarkdown(weekStart: string, summary: WeeklySummary): string {
  const bullets = summary.resume_bullets.map((b) => `- ${b}`).join("\n")
  return `# Weekly Summary — Week of ${weekStart}

## What I worked on
${summary.what_i_worked_on}

## What I learned
${summary.what_i_learned}

## Blockers
${summary.blockers}

## Talking points for my check-in
${summary.talking_points}

## Resume bullets
${bullets}
`
}

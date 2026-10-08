import type { InternshipRecapResponse, WeeklySummary } from "./api"

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

export function buildInternshipRecapMarkdown({ recap, first_week, last_week }: InternshipRecapResponse): string {
  const list = (items: string[]) => items.map((item) => `- ${item}`).join("\n")
  const challenges = recap.challenges_overcome.length
    ? `\n## Challenges I worked through\n${list(recap.challenges_overcome)}\n`
    : ""
  return `# Internship Recap — ${first_week} to ${last_week}

${recap.headline}

## Highlights
${list(recap.highlights)}

## Skills I picked up
${list(recap.skills_learned)}
${challenges}
## Talking points for my final review
${list(recap.talking_points)}

## Resume bullets
${list(recap.resume_bullets)}
`
}

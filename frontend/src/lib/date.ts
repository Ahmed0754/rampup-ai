export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  })
}

/** YYYY-MM-DD in the user's local timezone. (toISOString() is UTC, which
 * shifts the date by a day in the evening west of UTC / early morning east of it.) */
export function toLocalDateString(d: Date): string {
  const month = String(d.getMonth() + 1).padStart(2, "0")
  const day = String(d.getDate()).padStart(2, "0")
  return `${d.getFullYear()}-${month}-${day}`
}

export function getCurrentWeekStart(): string {
  const now = new Date()
  const day = now.getDay()
  const diff = (day === 0 ? -6 : 1) - day
  const monday = new Date(now)
  monday.setDate(now.getDate() + diff)
  return toLocalDateString(monday)
}

function addDaysToWeekStart(weekStart: string, days: number): string {
  const d = new Date(`${weekStart}T00:00:00Z`)
  d.setUTCDate(d.getUTCDate() + days)
  return d.toISOString().slice(0, 10)
}

/**
 * Consecutive weeks (ending at this week or last week) with at least one
 * progress entry. A streak stays "alive" through the current week even
 * before you've logged anything for it yet - it only breaks once a full
 * week passes with nothing logged.
 */
export function computeStreak(weekStartsWithEntries: string[]): number {
  const weeks = new Set(weekStartsWithEntries)
  const current = getCurrentWeekStart()
  const previous = addDaysToWeekStart(current, -7)

  let cursor: string
  if (weeks.has(current)) {
    cursor = current
  } else if (weeks.has(previous)) {
    cursor = previous
  } else {
    return 0
  }

  let count = 0
  while (weeks.has(cursor)) {
    count += 1
    cursor = addDaysToWeekStart(cursor, -7)
  }
  return count
}

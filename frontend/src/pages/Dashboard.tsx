import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../lib/auth.tsx"
import { supabase } from "../lib/supabase"
import { getCurrentWeekStart } from "../lib/date"

interface RecentPaste {
  id: string
  input_type: string
  raw_text: string
  created_at: string
}

interface Stats {
  pastesThisWeek: number
  repliesGenerated: number
  progressEntries: number
  internshipWeek: number
}

export default function Dashboard() {
  const { session } = useAuth()
  const navigate = useNavigate()
  const [stats, setStats] = useState<Stats>({
    pastesThisWeek: 0,
    repliesGenerated: 0,
    progressEntries: 0,
    internshipWeek: 1,
  })
  const [recentPastes, setRecentPastes] = useState<RecentPaste[]>([])

  const name = session?.user.email?.split("@")[0] ?? "there"

  useEffect(() => {
    if (!session) return
    void loadDashboard(session.user.id, session.user.created_at)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session])

  async function loadDashboard(userId: string, createdAt: string) {
    const weekStart = getCurrentWeekStart()

    const [pastesRes, repliesRes, progressRes, recentRes] = await Promise.all([
      supabase
        .from("pastes")
        .select("id", { count: "exact", head: true })
        .eq("user_id", userId)
        .gte("created_at", weekStart),
      supabase.from("replies").select("id", { count: "exact", head: true }).eq("user_id", userId),
      supabase
        .from("progress_entries")
        .select("id", { count: "exact", head: true })
        .eq("user_id", userId)
        .eq("week_start", weekStart),
      supabase
        .from("pastes")
        .select("id, input_type, raw_text, created_at")
        .eq("user_id", userId)
        .order("created_at", { ascending: false })
        .limit(5),
    ])

    const weeksSinceStart = Math.max(
      1,
      Math.ceil((Date.now() - new Date(createdAt).getTime()) / (7 * 24 * 60 * 60 * 1000)) + 1,
    )

    setStats({
      pastesThisWeek: pastesRes.count ?? 0,
      repliesGenerated: repliesRes.count ?? 0,
      progressEntries: progressRes.count ?? 0,
      internshipWeek: weeksSinceStart,
    })
    setRecentPastes(recentRes.data ?? [])
  }

  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="mb-8 text-2xl font-semibold text-white">Good morning, {name}</h1>

      <div className="mb-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard label="Pastes this week" value={stats.pastesThisWeek} />
        <StatCard label="Replies generated" value={stats.repliesGenerated} />
        <StatCard label="Progress entries" value={stats.progressEntries} />
        <StatCard label="Internship week" value={stats.internshipWeek} />
      </div>

      <div className="mb-8 grid gap-3 sm:grid-cols-3">
        <QuickAction label="Explain Something" onClick={() => navigate("/inbox")} />
        <QuickAction label="Log a Win" onClick={() => navigate("/progress")} />
        <QuickAction label="Generate Weekly Summary" onClick={() => navigate("/progress")} />
      </div>

      <div className="rounded-xl border border-border bg-panel p-5">
        <h2 className="mb-4 text-sm font-medium text-neutral-400">Recent activity</h2>
        {recentPastes.length === 0 ? (
          <p className="text-sm text-neutral-600">Nothing yet — paste something to get started.</p>
        ) : (
          <ul className="space-y-3">
            {recentPastes.map((paste) => (
              <li key={paste.id} className="flex items-center justify-between gap-3 text-sm">
                <div className="flex items-center gap-3 overflow-hidden">
                  <span className="flex-shrink-0 rounded-full bg-accent/20 px-2 py-0.5 text-xs text-accent">
                    {paste.input_type}
                  </span>
                  <span className="truncate text-neutral-300">{paste.raw_text}</span>
                </div>
                <span className="flex-shrink-0 text-xs text-neutral-500">
                  {new Date(paste.created_at).toLocaleString()}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-border bg-panel p-4">
      <p className="text-2xl font-semibold text-white">{value}</p>
      <p className="mt-1 text-xs text-neutral-400">{label}</p>
    </div>
  )
}

function QuickAction({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="rounded-xl border border-border bg-panel px-4 py-3 text-sm font-medium text-white transition hover:border-accent hover:text-accent"
    >
      {label}
    </button>
  )
}

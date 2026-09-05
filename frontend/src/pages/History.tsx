import { useEffect, useState } from "react"
import type { ReactNode } from "react"
import toast from "react-hot-toast"
import { useAuth } from "../lib/auth.tsx"
import { supabase } from "../lib/supabase"
import { formatDateTime } from "../lib/date"

type TabKey = "explained" | "replies" | "summaries" | "resume"

const TABS: { key: TabKey; label: string; table: string }[] = [
  { key: "explained", label: "Explained", table: "pastes" },
  { key: "replies", label: "Replies", table: "replies" },
  { key: "summaries", label: "Weekly Summaries", table: "weekly_summaries" },
  { key: "resume", label: "Resume Bullets", table: "resume_bullets" },
]

const TYPE_LABELS: Record<string, string> = {
  error: "Terminal Error",
  slack: "Slack Message",
  email: "Email",
  jira: "Jira Ticket",
  pr: "Pull Request",
  meeting_note: "Meeting Note",
  other: "Message",
}

interface Row {
  id: string
  created_at: string
  [key: string]: unknown
}

export default function History() {
  const { session } = useAuth()
  const [tab, setTab] = useState<TabKey>("explained")
  const [rows, setRows] = useState<Row[]>([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState<string | null>(null)

  const table = TABS.find((t) => t.key === tab)!.table

  useEffect(() => {
    if (!session) return
    let active = true
    setLoading(true)
    setExpanded(null)
    supabase
      .from(table)
      .select("*")
      .eq("user_id", session.user.id)
      .order("created_at", { ascending: false })
      .limit(50)
      .then(({ data, error }) => {
        if (!active) return
        if (error) toast.error("Could not load history")
        setRows((data as Row[]) ?? [])
        setLoading(false)
      })
    return () => {
      active = false
    }
  }, [table, session])

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="mb-6 text-2xl font-semibold text-white">History</h1>

      <div className="mb-6 flex flex-wrap gap-2">
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            onClick={() => setTab(t.key)}
            className={`rounded-lg px-3 py-2 text-sm transition ${
              tab === t.key
                ? "bg-accent font-medium text-white"
                : "border border-border bg-panel text-neutral-300 hover:text-white"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {loading ? (
        <p className="text-sm text-neutral-500">Loading...</p>
      ) : rows.length === 0 ? (
        <p className="text-sm text-neutral-600">Nothing here yet.</p>
      ) : (
        <ul className="space-y-3">
          {rows.map((row) => (
            <HistoryCard
              key={row.id}
              row={row}
              tab={tab}
              open={expanded === row.id}
              onToggle={() => setExpanded(expanded === row.id ? null : row.id)}
            />
          ))}
        </ul>
      )}
    </div>
  )
}

function HistoryCard({
  row,
  tab,
  open,
  onToggle,
}: {
  row: Row
  tab: TabKey
  open: boolean
  onToggle: () => void
}) {
  const { title, tag } = summarize(row, tab)

  return (
    <li className="overflow-hidden rounded-xl border border-border bg-panel">
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left"
      >
        <div className="flex min-w-0 items-center gap-3">
          {tag && (
            <span className="flex-shrink-0 rounded-full bg-accent/20 px-2 py-0.5 text-xs text-accent">
              {tag}
            </span>
          )}
          <span className="truncate text-sm text-neutral-200">{title}</span>
        </div>
        <span className="flex-shrink-0 text-xs text-neutral-500">{formatDateTime(row.created_at)}</span>
      </button>
      {open && <div className="space-y-3 border-t border-border px-4 py-4 text-sm">{renderDetail(row, tab)}</div>}
    </li>
  )
}

function summarize(row: Row, tab: TabKey): { title: string; tag?: string } {
  switch (tab) {
    case "explained":
      return { title: String(row.raw_text ?? ""), tag: TYPE_LABELS[String(row.input_type)] ?? String(row.input_type) }
    case "replies":
      return { title: String(row.original_text ?? ""), tag: String(row.tone) }
    case "summaries":
      return { title: `Week of ${row.week_start}` }
    case "resume":
      return { title: String(row.description ?? "") }
  }
}

function renderDetail(row: Row, tab: TabKey): ReactNode {
  switch (tab) {
    case "explained":
      return (
        <>
          <Field label="Pasted">{String(row.raw_text ?? "")}</Field>
          <Field label="Explanation">{String(row.explanation ?? "")}</Field>
          <BulletField label="Action items" items={toStringArray(row.action_items)} />
          <ExplainChatThread pasteId={String(row.id)} />
        </>
      )
    case "replies":
      return (
        <>
          <Field label="Original message">{String(row.original_text ?? "")}</Field>
          <Field label={`Reply (${row.tone})`}>{String(row.reply_text ?? "")}</Field>
        </>
      )
    case "summaries":
      return (
        <>
          <Field label="What I worked on">{String(row.what_i_worked_on ?? "")}</Field>
          <Field label="What I learned">{String(row.what_i_learned ?? "")}</Field>
          <Field label="Blockers">{String(row.blockers ?? "")}</Field>
          <BulletField label="Resume bullets" items={toStringArray(row.resume_bullets)} />
          <Field label="Talking points">{String(row.talking_points ?? "")}</Field>
        </>
      )
    case "resume":
      return (
        <>
          <Field label="Notes">{String(row.description ?? "")}</Field>
          <BulletField label="Bullets" items={toStringArray(row.bullets)} />
        </>
      )
  }
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  if (!children) return null
  return (
    <div>
      <p className="mb-1 text-xs font-medium uppercase tracking-wide text-neutral-500">{label}</p>
      <p className="whitespace-pre-wrap text-neutral-200">{children}</p>
    </div>
  )
}

function BulletField({ label, items }: { label: string; items: string[] }) {
  if (items.length === 0) return null
  return (
    <div>
      <p className="mb-1 text-xs font-medium uppercase tracking-wide text-neutral-500">{label}</p>
      <ul className="list-disc space-y-1 pl-5 text-neutral-200">
        {items.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>
    </div>
  )
}

function toStringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.map(String) : []
}

interface ChatMessageRow {
  role: string
  content: string
}

function ExplainChatThread({ pasteId }: { pasteId: string }) {
  const { session } = useAuth()
  const [messages, setMessages] = useState<ChatMessageRow[]>([])

  useEffect(() => {
    if (!session) return
    let active = true
    supabase
      .from("explain_chat_messages")
      .select("role, content")
      .eq("paste_id", pasteId)
      .eq("user_id", session.user.id)
      .order("created_at", { ascending: true })
      .then(({ data }) => {
        if (active) setMessages((data as ChatMessageRow[]) ?? [])
      })
    return () => {
      active = false
    }
  }, [pasteId, session])

  if (messages.length === 0) return null

  return (
    <div>
      <p className="mb-1 text-xs font-medium uppercase tracking-wide text-neutral-500">Follow-up questions</p>
      <div className="space-y-2">
        {messages.map((m, i) => (
          <p key={i} className={m.role === "user" ? "text-neutral-200" : "pl-3 text-neutral-400"}>
            <span className="font-medium">{m.role === "user" ? "You: " : "Answer: "}</span>
            {m.content}
          </p>
        ))}
      </div>
    </div>
  )
}

import axios from "axios"
import { supabase } from "./supabase"

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
})

api.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession()
  const token = data.session?.access_token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export interface ExplainResponse {
  input_type: string
  explanation: string
  what_they_mean: string
  what_to_do_next: string
  action_items: string[]
  paste_id: string | null
  saved: boolean
}

export type Tone = "casual" | "professional" | "manager-safe" | "confused-but-trying"

export interface ReplyResponse {
  reply: string
  tone: Tone
  saved: boolean
}

export type EntryType = "win" | "learned" | "blocker" | "task_completed"

export interface ProgressEntry {
  id: string
  entry_text: string
  entry_type: EntryType
  week_start: string
  created_at: string
}

export interface ProgressEntryCreated {
  id: string
  created_at: string
}

export interface WeeklySummary {
  what_i_worked_on: string
  what_i_learned: string
  blockers: string
  resume_bullets: string[]
  talking_points: string
}

// Streaming endpoints (explain/reply/resume-bullets) return newline-delimited
// JSON: {"type":"chunk","text":"..."} pieces as the model generates them,
// then one {"type":"done", ...fields} with the final parsed/saved result, or
// {"type":"error","message":"..."} if generation failed partway through.
// axios doesn't expose a readable stream in the browser, so these use fetch
// directly and attach the same Supabase bearer token the axios interceptor
// adds elsewhere.
async function streamNdjson<T>(path: string, body: unknown, onChunk: (text: string) => void): Promise<T> {
  const { data } = await supabase.auth.getSession()
  const token = data.session?.access_token

  const res = await fetch(`${import.meta.env.VITE_API_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  })

  if (!res.ok || !res.body) {
    let message = "Something went wrong"
    try {
      message = (await res.json()).detail ?? message
    } catch {
      // response wasn't JSON - keep the generic message
    }
    throw new Error(message)
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""
  let done: T | null = null

  while (true) {
    const { value, done: streamDone } = await reader.read()
    if (streamDone) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split("\n")
    buffer = lines.pop() ?? ""
    for (const line of lines) {
      if (!line.trim()) continue
      const event = JSON.parse(line) as { type: string; [key: string]: unknown }
      if (event.type === "chunk") onChunk(event.text as string)
      else if (event.type === "error") throw new Error(event.message as string)
      else if (event.type === "done") done = event as T
    }
  }

  if (!done) throw new Error("Something went wrong")
  return done
}

export async function explainTextStream(text: string, onChunk: (text: string) => void): Promise<ExplainResponse> {
  return streamNdjson<ExplainResponse>("/api/explain", { text }, onChunk)
}

export async function generateReplyStream(
  text: string,
  tone: Tone,
  pasteId: string | undefined,
  onChunk: (text: string) => void,
): Promise<ReplyResponse> {
  return streamNdjson<ReplyResponse>("/api/reply", { text, tone, paste_id: pasteId }, onChunk)
}

export interface ExplainChatResponse {
  reply: string
  saved: boolean
}

export async function explainChatStream(
  pasteId: string,
  message: string,
  onChunk: (text: string) => void,
): Promise<ExplainChatResponse> {
  return streamNdjson<ExplainChatResponse>("/api/explain/chat", { paste_id: pasteId, message }, onChunk)
}

export async function createProgressEntry(
  entryText: string,
  entryType: EntryType,
  weekStart: string,
): Promise<ProgressEntryCreated> {
  const { data } = await api.post<ProgressEntryCreated>("/api/progress", {
    entry_text: entryText,
    entry_type: entryType,
    week_start: weekStart,
  })
  return data
}

export async function listProgressEntries(weekStart: string): Promise<ProgressEntry[]> {
  const { data } = await api.get<{ entries: ProgressEntry[] }>("/api/progress", {
    params: { week_start: weekStart },
  })
  return data.entries
}

export async function generateWeeklySummary(weekStart: string): Promise<WeeklySummary> {
  const { data } = await api.post<{ summary: WeeklySummary }>("/api/progress/summary", {
    week_start: weekStart,
  })
  return data.summary
}

export interface ResumeBulletsResponse {
  bullets: string[]
  saved: boolean
}

export async function generateResumeBulletsStream(
  description: string,
  onChunk: (text: string) => void,
): Promise<ResumeBulletsResponse> {
  return streamNdjson<ResumeBulletsResponse>("/api/resume-bullets", { description }, onChunk)
}

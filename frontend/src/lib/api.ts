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

export async function explainText(text: string): Promise<ExplainResponse> {
  const { data } = await api.post<ExplainResponse>("/api/explain", { text })
  return data
}

export async function generateReply(text: string, tone: Tone, pasteId?: string): Promise<ReplyResponse> {
  const { data } = await api.post<ReplyResponse>("/api/reply", { text, tone, paste_id: pasteId })
  return data
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

export async function generateResumeBullets(description: string): Promise<string[]> {
  const { data } = await api.post<{ bullets: string[] }>("/api/resume-bullets", { description })
  return data.bullets
}

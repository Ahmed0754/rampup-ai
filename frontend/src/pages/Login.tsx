import { useState } from "react"
import type { FormEvent } from "react"
import { Navigate } from "react-router-dom"
import toast from "react-hot-toast"
import { supabase } from "../lib/supabase"
import { useAuth } from "../lib/auth.tsx"

export default function Login() {
  const { session } = useAuth()
  const [mode, setMode] = useState<"sign-in" | "sign-up">("sign-in")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [submitting, setSubmitting] = useState(false)

  if (session) {
    return <Navigate to="/" replace />
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setSubmitting(true)
    try {
      if (mode === "sign-in") {
        const { error } = await supabase.auth.signInWithPassword({ email, password })
        if (error) throw error
      } else {
        const { error } = await supabase.auth.signUp({ email, password })
        if (error) throw error
        toast.success("Account created! You can now sign in.")
        setMode("sign-in")
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Something went wrong"
      toast.error(message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-base px-4">
      <div className="w-full max-w-sm rounded-xl border border-border bg-panel p-8">
        <h1 className="mb-1 text-2xl font-semibold text-white">RampUp AI</h1>
        <p className="mb-6 text-sm text-neutral-400">
          {mode === "sign-in" ? "Sign in to your account" : "Create an account"}
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm text-neutral-300">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-border bg-base px-3 py-2 text-white outline-none focus:border-accent"
              placeholder="you@company.com"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm text-neutral-300">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-border bg-base px-3 py-2 text-white outline-none focus:border-accent"
              placeholder="••••••••"
            />
          </div>
          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-accent px-4 py-2 font-medium text-white transition hover:bg-accent-hover disabled:opacity-60"
          >
            {submitting ? "Please wait..." : mode === "sign-in" ? "Sign In" : "Sign Up"}
          </button>
        </form>
        <button
          type="button"
          onClick={() => setMode(mode === "sign-in" ? "sign-up" : "sign-in")}
          className="mt-4 w-full text-center text-sm text-neutral-400 hover:text-white"
        >
          {mode === "sign-in" ? "Need an account? Sign up" : "Already have an account? Sign in"}
        </button>
      </div>
    </div>
  )
}

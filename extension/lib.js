// Shared helpers used by popup.js and result.js. Loaded as a plain classic
// script (no bundler / ES modules) so it works unmodified as an unpacked
// extension - every function here is just a global.

function getConfig() {
  return new Promise((resolve) => {
    chrome.storage.local.get(["apiBaseUrl", "supabaseUrl", "supabaseAnonKey"], resolve)
  })
}

function setConfig(cfg) {
  return new Promise((resolve) => {
    chrome.storage.local.set(cfg, resolve)
  })
}

function getStoredSession() {
  return new Promise((resolve) => {
    chrome.storage.local.get(["session"], (r) => resolve(r.session || null))
  })
}

function setStoredSession(session) {
  return new Promise((resolve) => {
    chrome.storage.local.set({ session }, resolve)
  })
}

// Talks to Supabase Auth's REST API directly (no supabase-js) to keep the
// extension dependency-free - it's a handful of fetch calls.

async function login(email, password) {
  const { supabaseUrl, supabaseAnonKey } = await getConfig()
  const res = await fetch(`${supabaseUrl}/auth/v1/token?grant_type=password`, {
    method: "POST",
    headers: { apikey: supabaseAnonKey, "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error_description || data.msg || "Login failed")
  const session = {
    access_token: data.access_token,
    refresh_token: data.refresh_token,
    expires_at: Date.now() + data.expires_in * 1000,
    email: data.user && data.user.email,
  }
  await setStoredSession(session)
  return session
}

async function logout() {
  await setStoredSession(null)
}

async function refreshSession(session) {
  const { supabaseUrl, supabaseAnonKey } = await getConfig()
  const res = await fetch(`${supabaseUrl}/auth/v1/token?grant_type=refresh_token`, {
    method: "POST",
    headers: { apikey: supabaseAnonKey, "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: session.refresh_token }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error("Session expired - please log in again")
  const next = {
    access_token: data.access_token,
    refresh_token: data.refresh_token,
    expires_at: Date.now() + data.expires_in * 1000,
    email: (data.user && data.user.email) || session.email,
  }
  await setStoredSession(next)
  return next
}

async function getValidSession() {
  let session = await getStoredSession()
  if (!session) return null
  if (Date.now() > session.expires_at - 60_000) {
    session = await refreshSession(session)
  }
  return session
}

// Same newline-delimited-JSON streaming contract the web app's api.ts uses:
// {"type":"chunk","text":"..."} pieces, then one {"type":"done", ...fields}.
async function streamExplain(text, onChunk) {
  const { apiBaseUrl } = await getConfig()
  const session = await getValidSession()
  if (!session) throw new Error("NOT_LOGGED_IN")

  const res = await fetch(`${apiBaseUrl}/api/explain`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${session.access_token}`,
    },
    body: JSON.stringify({ text }),
  })

  if (!res.ok) {
    let message = "Something went wrong"
    try {
      message = (await res.json()).detail || message
    } catch (e) {
      // response wasn't JSON - keep the generic message
    }
    throw new Error(message)
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""
  let done = null
  while (true) {
    const { value, done: streamDone } = await reader.read()
    if (streamDone) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split("\n")
    buffer = lines.pop() || ""
    for (const line of lines) {
      if (!line.trim()) continue
      const event = JSON.parse(line)
      if (event.type === "chunk") onChunk(event.text)
      else if (event.type === "error") throw new Error(event.message)
      else if (event.type === "done") done = event
    }
  }
  if (!done) throw new Error("Something went wrong")
  return done
}

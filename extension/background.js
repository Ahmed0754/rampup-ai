const DEFAULT_CONFIG = {
  apiBaseUrl: "http://localhost:8000",
  supabaseUrl: "https://ldoraumqmaixpfuucniv.supabase.co",
  // Supabase's anon/publishable key - meant to be public (it ships in every
  // browser bundle of the deployed frontend too), safe to commit. Swap it in
  // the popup's Settings panel if you point this at a different project.
  supabaseAnonKey:
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imxkb3JhdW1xbWFpeHBmdXVjbml2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg0OTEzOTMsImV4cCI6MjEwNDA2NzM5M30.N9qNinBlOa8XjKIjERB9nm74O5xp2Zj7M3aYeVJN2VI",
}

const MENU_ITEMS = {
  "rampup-explain": { title: "Explain with RampUp AI", mode: "explain" },
  "rampup-reply": { title: "Draft a reply with RampUp AI", mode: "reply" },
}

chrome.runtime.onInstalled.addListener(() => {
  // onInstalled also fires on every extension update/reload, and creating an
  // item whose id already exists errors - so start from a clean menu.
  chrome.contextMenus.removeAll(() => {
    for (const [id, { title }] of Object.entries(MENU_ITEMS)) {
      chrome.contextMenus.create({ id, title, contexts: ["selection"] })
    }
  })

  chrome.storage.local.get(["apiBaseUrl", "supabaseUrl", "supabaseAnonKey"], (existing) => {
    const missing = {}
    for (const key of Object.keys(DEFAULT_CONFIG)) {
      if (!existing[key]) missing[key] = DEFAULT_CONFIG[key]
    }
    if (Object.keys(missing).length > 0) chrome.storage.local.set(missing)
  })
})

chrome.contextMenus.onClicked.addListener((info) => {
  const item = MENU_ITEMS[info.menuItemId]
  if (!item || !info.selectionText) return
  const params = new URLSearchParams({ mode: item.mode, text: info.selectionText })
  const url = chrome.runtime.getURL("result.html") + "?" + params
  chrome.windows.create({ url, type: "popup", width: 420, height: 640 })
})

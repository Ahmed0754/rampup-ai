async function refreshView() {
  const session = await getStoredSession()
  document.getElementById("loggedOut").style.display = session ? "none" : "block"
  document.getElementById("loggedIn").style.display = session ? "block" : "none"
  if (session) {
    document.getElementById("whoami").textContent = `Signed in as ${session.email}`
  }

  const cfg = await getConfig()
  document.getElementById("apiBaseUrl").value = cfg.apiBaseUrl || ""
  document.getElementById("supabaseUrl").value = cfg.supabaseUrl || ""
  document.getElementById("supabaseAnonKey").value = cfg.supabaseAnonKey || ""
}

document.getElementById("loginBtn").addEventListener("click", async () => {
  const email = document.getElementById("email").value.trim()
  const password = document.getElementById("password").value
  const errorEl = document.getElementById("loginError")
  errorEl.textContent = ""
  try {
    await login(email, password)
    await refreshView()
  } catch (err) {
    errorEl.textContent = err.message
  }
})

document.getElementById("logoutBtn").addEventListener("click", async () => {
  await logout()
  await refreshView()
})

document.getElementById("saveSettingsBtn").addEventListener("click", async () => {
  await setConfig({
    apiBaseUrl: document.getElementById("apiBaseUrl").value.trim(),
    supabaseUrl: document.getElementById("supabaseUrl").value.trim(),
    supabaseAnonKey: document.getElementById("supabaseAnonKey").value.trim(),
  })
})

refreshView()

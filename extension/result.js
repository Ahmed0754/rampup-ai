const params = new URLSearchParams(location.search)
const text = params.get("text") || ""
const contentEl = document.getElementById("content")

function escapeHtml(s) {
  const div = document.createElement("div")
  div.textContent = s
  return div.innerHTML
}

function render(result) {
  const items = (result.action_items || []).map((i) => `<li>${escapeHtml(i)}</li>`).join("")
  contentEl.innerHTML = `
    <span class="tag">${escapeHtml(result.input_type || "")}</span>
    <h2>What this means</h2>
    <p>${escapeHtml(result.explanation || "")}</p>
    <h2>What to do next</h2>
    <p>${escapeHtml(result.what_to_do_next || "")}</p>
    <h2>Action items</h2>
    <ul>${items}</ul>
  `
}

async function run() {
  if (!text.trim()) {
    contentEl.innerHTML = '<p class="error">No text selected.</p>'
    return
  }

  contentEl.innerHTML = '<p id="stream" class="loading"></p>'
  const streamEl = document.getElementById("stream")
  let streamed = ""

  try {
    const result = await streamExplain(text, (chunk) => {
      streamed += chunk
      streamEl.textContent = streamed
    })
    render(result)
  } catch (err) {
    if (err.message === "NOT_LOGGED_IN") {
      contentEl.innerHTML =
        '<p class="error">Not logged in.</p>' +
        '<p style="margin-top:8px;font-size:12px;color:#888">Click the RampUp AI icon in your toolbar to log in, then try again.</p>'
    } else {
      contentEl.innerHTML = `<p class="error">${escapeHtml(err.message)}</p>`
    }
  }
}

run()

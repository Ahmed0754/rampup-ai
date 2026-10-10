const params = new URLSearchParams(location.search)
const text = params.get("text") || ""
// "explain" (default): explain first, then offer a reply. "reply": straight to the reply panel.
const mode = params.get("mode") === "reply" ? "reply" : "explain"
const contentEl = document.getElementById("content")
const replyEl = document.getElementById("reply")

const TONES = [
  { value: "casual", label: "Casual" },
  { value: "professional", label: "Professional" },
  { value: "manager-safe", label: "Manager-Safe" },
  { value: "confused-but-trying", label: "Confused But Trying" },
]

function escapeHtml(s) {
  const div = document.createElement("div")
  div.textContent = s
  return div.innerHTML
}

// Same headings the web app uses: code and errors get a debugging-oriented layout.
const HEADINGS = {
  code: { meaning: "What this code does", cause: "Where it could break", next: "Check this first", items: "Steps to dig in" },
  error: { meaning: "What this error means", cause: "Most likely cause", next: "Check this first", items: "Debugging steps" },
}
const DEFAULT_HEADINGS = { meaning: "What this means", cause: null, next: "What to do next", items: "Action items" }

// Escape first, then turn `identifiers` into <code> - backticks survive escaping.
function formatText(s) {
  return escapeHtml(s || "").replace(/`([^`\n]+)`/g, "<code>$1</code>")
}

function render(result) {
  const h = HEADINGS[result.input_type] || DEFAULT_HEADINGS
  const items = (result.action_items || []).map((i) => `<li>${formatText(i)}</li>`).join("")
  const cause = h.cause ? `<h2>${h.cause}</h2><p>${formatText(result.what_they_mean)}</p>` : ""
  contentEl.innerHTML = `
    <span class="tag">${escapeHtml(result.input_type || "")}</span>
    <h2>${h.meaning}</h2>
    <p>${formatText(result.explanation)}</p>
    ${cause}
    <h2>${h.next}</h2>
    <p>${formatText(result.what_to_do_next)}</p>
    <h2>${h.items}</h2>
    <ul>${items}</ul>
  `
}

function showError(el, err) {
  if (err.message === "NOT_LOGGED_IN") {
    el.innerHTML =
      '<p class="error">Not logged in.</p>' +
      '<p style="margin-top:8px;font-size:12px;color:#888">Click the RampUp AI icon in your toolbar to log in, then try again.</p>'
  } else {
    el.innerHTML = `<p class="error">${escapeHtml(err.message)}</p>`
  }
}

function renderReplyPanel(pasteId) {
  replyEl.innerHTML = `
    <h2>Draft a reply</h2>
    <div class="tones"></div>
    <div id="reply-text" class="reply-box" hidden></div>
    <button id="copy" class="copy" type="button" hidden>Copy reply</button>
  `
  const tonesEl = replyEl.querySelector(".tones")
  const replyTextEl = replyEl.querySelector("#reply-text")
  const copyEl = replyEl.querySelector("#copy")

  const buttons = TONES.map(({ value, label }) => {
    const button = document.createElement("button")
    button.type = "button"
    button.textContent = label
    button.addEventListener("click", () => draft(value, button))
    tonesEl.appendChild(button)
    return button
  })

  async function draft(tone, activeButton) {
    buttons.forEach((b) => {
      b.disabled = true
      b.classList.toggle("active", b === activeButton)
    })
    copyEl.hidden = true
    replyTextEl.hidden = false
    replyTextEl.className = "reply-box loading"
    replyTextEl.textContent = "Writing…"
    let streamed = ""
    try {
      const result = await streamReply(text, tone, pasteId, (chunk) => {
        streamed += chunk
        replyTextEl.className = "reply-box"
        replyTextEl.textContent = streamed
      })
      replyTextEl.textContent = result.reply
      copyEl.hidden = false
    } catch (err) {
      replyTextEl.className = "reply-box"
      showError(replyTextEl, err)
    } finally {
      buttons.forEach((b) => (b.disabled = false))
    }
  }

  copyEl.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(replyTextEl.textContent)
      copyEl.textContent = "Copied!"
    } catch (e) {
      copyEl.textContent = "Couldn't copy"
    }
    setTimeout(() => (copyEl.textContent = "Copy reply"), 1500)
  })
}

async function run() {
  if (!text.trim()) {
    contentEl.innerHTML = '<p class="error">No text selected.</p>'
    return
  }

  if (mode === "reply") {
    document.title = "RampUp AI - Reply"
    contentEl.innerHTML = '<h2>Replying to</h2><p class="quote"></p>'
    contentEl.querySelector(".quote").textContent = text.length > 400 ? `${text.slice(0, 400)}…` : text
    renderReplyPanel(null)
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
    renderReplyPanel(result.paste_id || null)
  } catch (err) {
    showError(contentEl, err)
  }
}

run()

# RampUp AI browser extension

Select any text on a page, right-click, and choose **"Explain with RampUp AI"** — no
copy-pasting into the app. Chrome/Edge (Manifest V3). Talks straight to your backend and
Supabase project; there's no separate server for the extension itself.

## Install (unpacked)

1. `chrome://extensions` (or `edge://extensions`) → enable **Developer mode**.
2. **Load unpacked** → select this `extension/` folder.
3. Click the RampUp AI icon in the toolbar and log in with your RampUp AI account.
4. Select text on any page → right-click → **Explain with RampUp AI**.

The explanation streams into a small popup window, and it's saved to your History exactly
like using the web app.

## Configuration

The extension ships pre-configured for this project's Supabase instance and
`http://localhost:8000` as the backend. Open the extension popup → **Settings** to change
either:

- **API base URL** — point this at your deployed backend instead of localhost.
- **Supabase URL** / **Supabase anon key** — only needed if you've pointed this repo at a
  different Supabase project. The anon key is meant to be public (same one already ships in
  the web app's JS bundle), so it's fine to have a default committed here.

## How it works

- `background.js` registers the right-click menu item and opens `result.html` in a small
  popup window with the selected text in the URL.
- `popup.html`/`popup.js` is a small login form. It calls Supabase Auth's REST API directly
  (no supabase-js dependency) and stores the session in `chrome.storage.local`, refreshing
  it automatically when it's close to expiring.
- `result.html`/`result.js` calls the backend's streamed `/api/explain` endpoint with the
  stored session's access token and renders the same newline-delimited-JSON stream the web
  app consumes, live, then swaps to the formatted result once it's done.
- `lib.js` holds the shared auth/streaming logic, loaded as a plain script by both pages —
  no build step, no bundler, no dependencies.

Not logged in? Selecting text and using the context menu still opens the result window; it
tells you to log in via the toolbar icon first instead of silently failing.

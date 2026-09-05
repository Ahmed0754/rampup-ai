# RampUp AI

[![CI](https://github.com/Ahmed0754/rampup-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/Ahmed0754/rampup-ai/actions/workflows/ci.yml)

An AI-powered productivity assistant for interns and junior developers. Paste a Slack message,
terminal error, email, or Jira ticket and get a plain-English explanation, action items, a
ready-to-send reply draft, and — over time — a weekly progress summary with resume-ready bullet
points.

## Tech stack

- **Frontend:** React + TypeScript + Tailwind CSS (Vite)
- **Backend:** FastAPI (Python)
- **Database / Auth:** Supabase (Postgres + email/password auth)
- **AI:** Google Gemini API (`gemini-flash-lite-latest`) — free tier, no credit card required

## Project structure

```
rampup-ai/
├── frontend/     React + TypeScript + Tailwind (Vite)
├── backend/      FastAPI app, routers, services, tests
├── supabase/     Postgres schema + RLS policies
├── vercel.json   Frontend deployment config
└── backend/Dockerfile
```

## Features

- **Explain This** — paste anything and get a plain-English explanation, what the sender actually
  wants, the single most important next step, and a checklist of action items. Streams in as it
  generates, and you can ask follow-up questions right there ("wait, what does that mean?").
- **Reply Generator** — turn any message into a draft reply in one of four tones: casual,
  professional, manager-safe, or confused-but-trying.
- **Progress Tracker** — log wins, things learned, blockers, and completed tasks per week.
- **Weekly Summary** — turn a week of progress entries into a status update, talking points for
  your check-in, and resume bullets.
- **Resume Bullets** — turn rough notes about your work into strong, metric-driven resume bullets.
- **Weekly nudge** — an automated email to anyone who hasn't logged progress yet that week, so
  Weekly Summary always has something to work with.
- **History** — browse everything you've explained, replied to, summarized, or turned into resume
  bullets, scoped to your account.

## Getting started

### 1. Supabase

Create a Supabase project and run `supabase/schema.sql` in the SQL editor. This creates the
`pastes`, `replies`, `progress_entries`, `weekly_summaries`, `resume_bullets`, and
`explain_chat_messages` tables with row-level security scoped to `auth.uid()`.

If you set the project up earlier, apply new tables by running the files in
`supabase/migrations/` in order.

### 2. Backend

Get a free Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)
(sign in with a Google account — no credit card, generous free tier).

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in GEMINI_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY
uvicorn app.main:app --reload
```

The API is served at `http://localhost:8000`, with a health check at `GET /health`.

Two more `.env` vars are optional locally but matter once you deploy:

- `CORS_ORIGINS` - comma-separated frontend origins allowed to call the API. Defaults to the
  local Vite dev ports; set it to your deployed frontend's URL (e.g. `https://your-app.vercel.app`)
  in production.
- `SUPABASE_JWT_SECRET` - from **Settings -> API -> JWT Settings -> JWT Secret**. Lets the backend
  verify session tokens locally instead of calling Supabase Auth on every request. Falls back to
  that network check if unset.

Run the tests:

```bash
pytest
```

### 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env   # fill in VITE_API_URL, VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY
npm run dev
```

The app is served at `http://localhost:5173`.

## API reference

| Method | Path                    | Description                                   |
| ------ | ----------------------- | ---------------------------------------------- |
| GET    | `/health`               | Health check                                   |
| POST   | `/api/explain`          | Classify + explain pasted text (streamed)      |
| POST   | `/api/explain/chat`     | Ask a follow-up question about an explanation (streamed) |
| POST   | `/api/reply`            | Generate a toned reply draft (streamed)        |
| POST   | `/api/progress`         | Log a progress entry                           |
| GET    | `/api/progress`         | List progress entries for a given week         |
| POST   | `/api/progress/summary` | Generate a weekly summary from progress entries|
| POST   | `/api/resume-bullets`   | Generate resume bullets from rough notes (streamed) |

Streamed endpoints return newline-delimited JSON: `{"type":"chunk","text":"..."}` pieces as the
model generates, then one `{"type":"done", ...}` with the final saved result (or `{"type":"error"}`
if generation fails partway through).

## Weekly nudge

`backend/scripts/weekly_nudge.py` emails anyone who hasn't logged a progress entry for the current
week yet. It's independent of the running API — it runs as a scheduled GitHub Actions workflow
(`.github/workflows/weekly-nudge.yml`, Mondays by default) using a free
[Resend](https://resend.com) account for sending.

To enable it:

1. Sign up at [resend.com](https://resend.com) (free tier, no card) and grab an API key from
   **API Keys**.
2. Add repo secrets under **Settings -> Secrets and variables -> Actions**: `SUPABASE_URL`,
   `SUPABASE_SERVICE_KEY`, `RESEND_API_KEY`, and optionally `FRONTEND_URL` (linked from the email).
3. Test it on demand from the **Actions** tab -> "Weekly progress nudge" -> **Run workflow**,
   before waiting for Monday.

Run it locally with `cd backend && python -m scripts.weekly_nudge` (needs the same vars in
`backend/.env`).

## Deployment

- **Frontend:** deploy `frontend/` to Vercel using the root `vercel.json`.
- **Backend:** build and run `backend/Dockerfile` on any container host (Fly.io, Render, Railway,
  ECS, etc.), with the same environment variables as `backend/.env.example`.

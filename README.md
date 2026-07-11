# RampUp AI

An AI-powered productivity assistant for interns and junior developers. Paste a Slack message,
terminal error, email, or Jira ticket and get a plain-English explanation, action items, a
ready-to-send reply draft, and — over time — a weekly progress summary with resume-ready bullet
points.

## Tech stack

- **Frontend:** React + TypeScript + Tailwind CSS (Vite)
- **Backend:** FastAPI (Python)
- **Database / Auth:** Supabase (Postgres + email/password auth)
- **AI:** Anthropic Claude (`claude-sonnet-4-6`)

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
  wants, the single most important next step, and a checklist of action items.
- **Reply Generator** — turn any message into a draft reply in one of four tones: casual,
  professional, manager-safe, or confused-but-trying.
- **Progress Tracker** — log wins, things learned, blockers, and completed tasks per week.
- **Weekly Summary** — turn a week of progress entries into a status update, talking points for
  your check-in, and resume bullets.
- **Resume Bullets** — turn rough notes about your work into strong, metric-driven resume bullets.

## Getting started

### 1. Supabase

Create a Supabase project and run `supabase/schema.sql` in the SQL editor. This creates the
`pastes`, `replies`, `progress_entries`, and `weekly_summaries` tables with row-level security
scoped to `auth.uid()`.

### 2. Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY
uvicorn app.main:app --reload
```

The API is served at `http://localhost:8000`, with a health check at `GET /health`.

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
| POST   | `/api/explain`          | Classify + explain pasted text                 |
| POST   | `/api/reply`            | Generate a toned reply draft                   |
| POST   | `/api/progress`         | Log a progress entry                           |
| GET    | `/api/progress`         | List progress entries for a given week         |
| POST   | `/api/progress/summary` | Generate a weekly summary from progress entries|
| POST   | `/api/resume-bullets`   | Generate resume bullets from rough notes       |

## Deployment

- **Frontend:** deploy `frontend/` to Vercel using the root `vercel.json`.
- **Backend:** build and run `backend/Dockerfile` on any container host (Fly.io, Render, Railway,
  ECS, etc.), with the same environment variables as `backend/.env.example`.

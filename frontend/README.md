# TalentLens Frontend (Next.js)

React/Next.js dashboard that replaces `backend/static/index.html`. The Python FastAPI backend is kept as the API — resume parsing, scoring, GitHub enrichment, and exports all still run in Python.

## Architecture

```
Browser (:3000) ──rewrites──▶ FastAPI (:8000)
  /screen, /upload_and_screen, /results, /clear,
  /resumes/*, /api/resume/*, /export_filtered_*, /download_*, /health, /me
```

- App Router + TypeScript + Tailwind (`src/app`, `src/components`, `src/lib`).
- `src/lib/types.ts` mirrors `backend/src/models.py` — keep in sync.
- `src/lib/api.ts` is the typed client for every FastAPI endpoint.
- Supabase Auth via `@supabase/supabase-js` (optional; blank keys = local-dev bypass, same as before).

## UI kit (`src/components/ui`)

Shared primitives reused across the dashboard — import from `@/components/ui`:

| Component | Use |
|-----------|-----|
| `Button` (`primary`/`secondary`/`soft`/`dark`/`link`, `xs`–`lg`) | All buttons; weight/rounding via `className` |
| `Card` | Dark panel container |
| `Badge` (`neutral`/`bright`/`muted`/`faint`, `pill`) | Skill chips, cohorts, status pills |
| `Tabs` | Ranked Eligible / Disqualified switcher |
| `SegmentedControl` | Top-N filter pills |
| `Slider` | Min-passing-score dial with marks |
| `SearchInput` | Candidate/skill search field |
| `Modal` | Overlay + panel shell with Escape-to-close (resume + auth modals) |
| `Spinner` | Loading indicator |
| `Stat` | Batch summary metric cell |
| `EmptyState` | Dashed placeholder for empty results |

## Run

```bash
# 1. Backend (terminal 1, from repo root)
cd backend
pip install -r requirements.txt
python main.py --serve --port 8000

# 2. Frontend (terminal 2, from repo root)
cd frontend
cp .env.example .env.local   # optional; defaults point at 127.0.0.1:8000
npm install
npm run dev                  # http://localhost:3000
```

Production:

```bash
cd frontend
npm run build
npm start
```

## Env

| Var | Purpose | Default |
|-----|---------|---------|
| `NEXT_PUBLIC_API_URL` / `API_URL` | FastAPI target for rewrites | `http://127.0.0.1:8000` |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL (optional) | — |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key (optional) | — |

## Parity with old dashboard

Ingest (folder/files, 100 cap) • sample screening • batch summary + passing-score slider + avg + GitHub cohorts • eligible/rejected tabs • Top 5/10/20 • search • score breakdown • GitHub metrics • 50–100 word justification • resume modal + new-tab/download • Excel/Word/CSV/JSON filtered exports • Supabase sign-in modal • clear session • loading overlay.

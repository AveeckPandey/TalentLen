# TalentLens Deployment (future)

Ship shape for later — nothing here is wired up yet.

## Planned layout

```
deployment/
  backend.Dockerfile      # python:3.11-slim, installs backend/requirements.txt,
                          # runs `python main.py --serve --port $PORT`
  docker-compose.yml      # api (backend) + web (frontend) for local prod parity
  render.yaml             # Render blueprint: backend web service (Python) with
                          # REQUIRE_AUTH=true + Supabase env vars
  VERCEL.md               # frontend deploy notes: set API_URL to the backend
                          # public URL so /screen, /upload_and_screen, … proxy
                          # correctly; add NEXT_PUBLIC_SUPABASE_* for auth
```

## Current manual path (until this is built)

- Backend → Render/Railway/Fly: Python service, start command
  `python main.py --serve --port $PORT`, env from `backend/.env.example`.
- Frontend → Vercel: import `frontend/`, set `API_URL` + `NEXT_PUBLIC_API_URL`
  to the backend URL.

Keep CORS in mind: `backend/src/api.py` already allows `*.vercel.app`
plus local dev origins.

# Supabase Auth Setup (Phase 1)

Local dev works with **zero setup** (open mode as `local-dev` user).
Do this once to enable real recruiter login:

## 1. Create Supabase project
1. https://supabase.com/dashboard > New project
2. Project Settings > API: copy `Project URL`, `publishable` key (`sb_publishable_...`), `secret` key (`sb_secret_...`)
3. Project Settings > API > JWKS URL: copy `.../auth/v1/.well-known/jwks.json` (backend verifies JWTs with this, no shared secret needed)
4. Legacy `anon` / `service_role` + `JWT Secret` also work if your project still shows them.

## 2. Run profiles migration
Dashboard > SQL Editor > paste + Run `supabase/migrations/0001_auth_profiles.sql`.

## 3. Configure auth providers
Authentication > Providers:
- Email: ON (confirm email OFF for quick testing, ON for prod)
- Google: ON with your OAuth client ID/secret, redirect `http://localhost:8000` + your Render URL

Authentication > URL Configuration: add `http://localhost:8000` and `https://<your-app>.onrender.com`.

## 4. Local .env
```bash
cp .env.example .env
```
Fill (create `.env` yourself — never commit it):
```
SUPABASE_URL=https://xyzcompany.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_...
SUPABASE_SECRET_KEY=sb_secret_...   # backend only, never expose
SUPABASE_JWKS_URL=https://xyzcompany.supabase.co/auth/v1/.well-known/jwks.json
REQUIRE_AUTH=false                   # keep false locally, true on Render
# Optional for Phase 2 jobs tables:
# DATABASE_URL=postgresql://postgres:***@db.<ref>.supabase.co:5432/postgres
```

## 5. Run + test
```bash
cd backend
pip install -r requirements.txt
python main.py --serve
# open http://localhost:8000/config.js -> should show your URL
# Sign up in dashboard header -> /me should return your user id
```

## 6. Render prod
Set the same env vars on the Web Service, with `REQUIRE_AUTH=true`.

## Notes
- Publishable key is public (frontend). Secret key stays server-side.
- If you pasted keys in chat, rotate them after setup (API > Roll keys) and update `backend/.env`/Render.
- All `/screen`, `/upload_and_screen`, `/results`, `/download_*`, `/export_*`, `/resumes/*` require `Authorization: Bearer <supabase access_token>` when `REQUIRE_AUTH=true`.
- Tests run in open local-dev mode, no Supabase needed.

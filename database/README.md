# TalentLens Database (Supabase)

Auth + persistence layer. The backend verifies Supabase JWTs (`backend/src/auth.py`);
the Next.js frontend signs in via `@supabase/supabase-js`.

## Layout

```
database/
  supabase/
    migrations/
      0001_auth_profiles.sql   # profiles table + RLS (apply in order)
```

## Apply migrations

```bash
# Option A — Supabase SQL editor: paste each file in numeric order.
# Option B — Supabase CLI (run from database/ so the CLI finds supabase/):
cd database
supabase link --project-ref <ref>
supabase db push
```

## Env (backend/.env)

```
SUPABASE_URL=https://xyzcompany.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_…   # also NEXT_PUBLIC_SUPABASE_URL/ANON_KEY in frontend/.env.local
SUPABASE_SECRET_KEY=sb_secret_…             # backend only, never expose
REQUIRE_AUTH=false                          # true on Render/prod
```

Local dev works with auth unconfigured (requests pass through as a dev user).
See `../docs/SUPABASE_AUTH_SETUP.md` for the full setup walkthrough.

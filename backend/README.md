# TalentLens Backend (FastAPI)

Python service: resume ingestion (PDF/DOCX/TXT), rule-based eligibility filters,
GitHub enrichment, 100-point explainable scoring, narrative justifications,
multi-format exports, and the legacy `static/` dashboard. The Next.js app in
`../frontend` talks to this API over HTTP.

## Layout

```
backend/
  main.py            # entrypoint: CLI (`--input …`) or web server (`--serve`)
  requirements.txt
  .env               # local secrets (gitignored) — copy from .env.example
  .env.example
  src/               # api, cli, config, models, pipeline, parsers, filters,
                     # scoring, enrichment, llm
  tests/             # pytest suite (36 tests)
  resumes/           # 50 bundled sample resumes
  static/            # legacy single-file dashboard (served at GET /)
  output/            # generated reports (gitignored, recreated on each run)
  uploads/           # uploaded batches (gitignored, recreated on each run)
```

`src/config.py` sets `BASE_DIR` to this folder, so **always run from `backend/`**.

## Run

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # optional: GITHUB_TOKEN, LLM keys, Supabase auth

# Web API + legacy dashboard → http://localhost:8000
python main.py --serve

# CLI batch screening
python main.py --input ./resumes --output ./output/results.json
python -m pytest -q    # full suite, run from backend/
```

## API surface

`GET /` (legacy dashboard) · `GET /health` · `POST /screen` ·
`POST /upload_and_screen` · `GET /results` · `POST /clear` ·
`GET /resumes/{file}` · `GET /download_csv|excel|docx` (legacy full exports) ·
`POST /export_filtered_excel|docx` (current-view exports).

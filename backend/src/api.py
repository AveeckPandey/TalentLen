"""FastAPI web service providing screening endpoints and interactive web interface."""

import shutil
import tempfile
from pathlib import Path
from typing import Optional, List
from fastapi import Depends, FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.auth import AuthUser, get_current_user, is_auth_configured
from src.config import settings
from src.models import ScreeningReport, FilterPreferences, CandidateResult
from src.pipeline import ScreeningPipeline

app = FastAPI(
    title="TalentLens Resume Screening System",
    description="Automated candidate screening and ranking for SDE AI internship.",
    version="1.0.0",
)

# CORS for the Next.js frontend (dev :3000 + prod). Direct same-origin
# rewrites are preferred (see frontend/next.config.mjs), this covers
# NEXT_PUBLIC_API_URL cross-origin usage.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pipeline instance
pipeline = ScreeningPipeline()

# Cache latest report in memory
latest_report: Optional[ScreeningReport] = None


class ScreenRequest(BaseModel):
    input_dir: str = "./resumes"
    min_cgpa: Optional[float] = None
    require_ai: bool = True
    require_experience: bool = False
    require_github_link: bool = False


@app.get("/", response_class=HTMLResponse)
def get_dashboard() -> HTMLResponse:
    """Serve the interactive single-page dashboard."""
    index_file = settings.BASE_DIR / "static" / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Dashboard index.html not found")
    with open(index_file, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "TalentLens Candidate Screening",
        "auth_configured": is_auth_configured(),
        "auth_enforced": settings.REQUIRE_AUTH,
    }


@app.get("/config.js", response_class=PlainTextResponse)
def frontend_config():
    """Public runtime config for the dashboard (only publishable-safe keys)."""
    url = (settings.SUPABASE_URL or "").replace('"', "")
    pub = ((settings.frontend_key or "")).replace('"', "")
    return (
        "window.KASPARRO_CONFIG = {"
        f'SUPABASE_URL: "{url}", SUPABASE_ANON_KEY: "{pub}", '
        f'SUPABASE_PUBLISHABLE_KEY: "{pub}", '
        f'AUTH_ENFORCED: {"true" if settings.REQUIRE_AUTH else "false"}'
        "};"
    )


@app.get("/me")
def get_me(user: AuthUser = Depends(get_current_user)):
    """Return the current authenticated principal."""
    return {"id": user.id, "email": user.email, "role": user.role, "is_dev": user.is_dev}


@app.post("/screen", response_model=ScreeningReport)
def screen_resumes(req: ScreenRequest, user: AuthUser = Depends(get_current_user)):
    """Run batch screening on specified resumes directory."""
    global latest_report
    preferences = FilterPreferences(
        min_cgpa=req.min_cgpa,
        require_ai_project=req.require_ai,
        require_experience=req.require_experience,
        require_github_link=req.require_github_link,
    )

    try:
        report = pipeline.process_directory(
            input_dir=req.input_dir,
            preferences=preferences,
            max_workers=settings.CONCURRENCY_LIMIT,
        )
        latest_report = report

        # Persist results
        pipeline.export_json(report, settings.OUTPUT_FILE)
        csv_file = settings.OUTPUT_FILE.with_suffix(".csv")
        pipeline.export_csv(report, csv_file)
        xlsx_file = settings.OUTPUT_FILE.with_suffix(".xlsx")
        pipeline.export_excel(report, xlsx_file)
        docx_file = settings.OUTPUT_FILE.with_suffix(".docx")
        pipeline.export_docx(report, docx_file)

        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload_and_screen", response_model=ScreeningReport)
async def upload_and_screen(
    files: List[UploadFile] = File(...),
    min_cgpa: Optional[float] = Form(None),
    require_ai: bool = Form(True),
    require_experience: bool = Form(False),
    require_github_link: bool = Form(False),
    user: AuthUser = Depends(get_current_user),
):
    """Upload up to 100 resume files and run screening immediately (fresh batch)."""
    global latest_report

    if len(files) > 100:
        files = files[:100]

    # Fresh batch: clear previous uploads so results reflect ONLY this upload
    uploads_dir = settings.BASE_DIR / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    for existing in uploads_dir.iterdir():
        try:
            if existing.is_file():
                existing.unlink()
        except Exception:
            pass

    for uploaded_file in files:
        safe_name = Path(uploaded_file.filename).name
        file_destination = uploads_dir / safe_name
        with open(file_destination, "wb") as buffer:
            shutil.copyfileobj(uploaded_file.file, buffer)

    preferences = FilterPreferences(
        min_cgpa=min_cgpa,
        require_ai_project=require_ai,
        require_experience=require_experience,
        require_github_link=require_github_link,
    )

    report = pipeline.process_directory(
        input_dir=uploads_dir,
        preferences=preferences,
        max_workers=settings.CONCURRENCY_LIMIT,
    )
    latest_report = report

    # Persist results
    pipeline.export_json(report, settings.OUTPUT_FILE)
    csv_file = settings.OUTPUT_FILE.with_suffix(".csv")
    pipeline.export_csv(report, csv_file)
    xlsx_file = settings.OUTPUT_FILE.with_suffix(".xlsx")
    pipeline.export_excel(report, xlsx_file)
    docx_file = settings.OUTPUT_FILE.with_suffix(".docx")
    pipeline.export_docx(report, docx_file)

    return report


# Resume file serving paths
resumes_dir = settings.BASE_DIR / "resumes"
uploads_dir = settings.BASE_DIR / "uploads"
uploads_dir.mkdir(parents=True, exist_ok=True)


@app.get("/resumes/{file_name:path}")
@app.get("/api/resume/{file_name:path}")
def serve_resume(file_name: str, user: AuthUser = Depends(get_current_user)):
    """Serve the exact original resume file (checking uploads first, then sample resumes directory)."""
    safe_name = Path(file_name).name

    # Check uploads directory first
    uploaded_path = uploads_dir / safe_name
    if uploaded_path.exists() and uploaded_path.is_file():
        media_type = "application/pdf" if uploaded_path.suffix.lower() == ".pdf" else "application/octet-stream"
        return FileResponse(
            path=str(uploaded_path),
            media_type=media_type,
            filename=safe_name,
            headers={
                "Content-Disposition": f"inline; filename=\"{safe_name}\"",
                "Cache-Control": "no-cache, no-store, must-revalidate",
            },
        )

    # Check base sample resumes directory
    base_path = resumes_dir / safe_name
    if base_path.exists() and base_path.is_file():
        media_type = "application/pdf" if base_path.suffix.lower() == ".pdf" else "application/octet-stream"
        return FileResponse(
            path=str(base_path),
            media_type=media_type,
            filename=safe_name,
            headers={
                "Content-Disposition": f"inline; filename=\"{safe_name}\"",
                "Cache-Control": "no-cache, no-store, must-revalidate",
            },
        )

    raise HTTPException(status_code=404, detail=f"Resume file '{safe_name}' not found.")


@app.get("/results", response_model=ScreeningReport)
def get_results(user: AuthUser = Depends(get_current_user)):
    """Retrieve the latest screening results from current session only (blank on fresh load)."""
    global latest_report
    if latest_report:
        return latest_report

    raise HTTPException(status_code=404, detail="No screening results in this session. Upload resumes first.")


@app.post("/clear")
def clear_session(user: AuthUser = Depends(get_current_user)):
    """Reset to blank state: clear in-memory report and uploaded files."""
    global latest_report
    latest_report = None
    try:
        up_dir = settings.BASE_DIR / "uploads"
        if up_dir.exists():
            for f in up_dir.iterdir():
                try:
                    if f.is_file():
                        f.unlink()
                except Exception:
                    pass
    except Exception:
        pass
    return {"status": "cleared"}


@app.get("/download_csv")
def download_csv(user: AuthUser = Depends(get_current_user)):
    """Download the screening report as CSV file."""
    csv_file = settings.OUTPUT_FILE.with_suffix(".csv")
    if not csv_file.exists():
        raise HTTPException(status_code=404, detail="CSV report not generated yet.")
    return FileResponse(
        path=str(csv_file),
        filename="screening_results.csv",
        media_type="text/csv",
    )


@app.get("/download_excel")
def download_excel(user: AuthUser = Depends(get_current_user)):
    """Download the screening report as an Excel (.xlsx) spreadsheet with contact details."""
    xlsx_file = settings.OUTPUT_FILE.with_suffix(".xlsx")
    if not xlsx_file.exists():
        # Generate on the fly if report available
        if latest_report:
            pipeline.export_excel(latest_report, xlsx_file)
        elif settings.OUTPUT_FILE.exists():
            import json
            with open(settings.OUTPUT_FILE, "r", encoding="utf-8") as f:
                rep = ScreeningReport(**json.load(f))
                pipeline.export_excel(rep, xlsx_file)
        else:
            raise HTTPException(status_code=404, detail="Excel report not generated yet.")
    return FileResponse(
        path=str(xlsx_file),
        filename="screening_shortlist.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.get("/download_docx")
def download_docx(user: AuthUser = Depends(get_current_user)):
    """Download the screening report as a Word document (.docx) with contact details."""
    docx_file = settings.OUTPUT_FILE.with_suffix(".docx")
    if not docx_file.exists():
        if latest_report:
            pipeline.export_docx(latest_report, docx_file)
        elif settings.OUTPUT_FILE.exists():
            import json
            with open(settings.OUTPUT_FILE, "r", encoding="utf-8") as f:
                rep = ScreeningReport(**json.load(f))
                pipeline.export_docx(rep, docx_file)
        else:
            raise HTTPException(status_code=404, detail="Word document report not generated yet.")
    return FileResponse(
        path=str(docx_file),
        filename="screening_report.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


class FilterExportRequest(BaseModel):
    candidates: List[CandidateResult]
    filter_label: str = "Filtered_Shortlist"


@app.post("/export_filtered_excel")
def export_filtered_excel(req: FilterExportRequest, user: AuthUser = Depends(get_current_user)):
    """Generate and download a tailored Excel file containing only the filtered candidates."""
    import re
    temp_file = Path(tempfile.mktemp(suffix=".xlsx"))
    try:
        pipeline.export_excel(req.candidates, temp_file)
        safe_label = re.sub(r'[^\w\-]', '_', req.filter_label.lower().strip()) or "filtered"
        return FileResponse(
            path=str(temp_file),
            filename=f"shortlist_{safe_label}.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/export_filtered_docx")
def export_filtered_docx(req: FilterExportRequest, user: AuthUser = Depends(get_current_user)):
    """Generate and download a tailored Word document containing only the filtered candidates."""
    import re
    temp_file = Path(tempfile.mktemp(suffix=".docx"))
    try:
        pipeline.export_docx(req.candidates, temp_file)
        safe_label = re.sub(r'[^\w\-]', '_', req.filter_label.lower().strip()) or "filtered"
        return FileResponse(
            path=str(temp_file),
            filename=f"shortlist_{safe_label}.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


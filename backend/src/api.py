"""FastAPI web service providing screening endpoints and interactive web interface."""

import shutil
import tempfile
import re
import os
import time
import datetime
import threading
import urllib.request
import logging
from pathlib import Path
from typing import Optional, List, Dict
from fastapi import Depends, FastAPI, UploadFile, File, Form, HTTPException, Request, Header
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger("talentlens.api")

from src.auth import AuthUser, get_current_user, is_auth_configured
from src.config import settings
from src.models import (
    ScreeningReport,
    FilterPreferences,
    CandidateResult,
    UserQuota,
    UpgradeRequest,
    PlanTier,
    CreateOrderRequest,
    CreateOrderResponse,
    VerifyPaymentRequest,
    VerifyPaymentResponse,
    ApiKeyInfo,
    CreateApiKeyRequest,
    CreateApiKeyResponse,
    ScreeningHistoryItem,
)
from src.pipeline import ScreeningPipeline
from src.quota import quota_manager
from src.payments import create_order, verify_payment_signature


def get_rate_limit_key(request: Request) -> str:
    """Identify client by API Key if present, otherwise by IP address."""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        auth = request.headers.get("Authorization", "")
        if auth.lower().startswith("bearer "):
            api_key = auth[7:].strip()
    if api_key:
        return f"key:{api_key[:16]}"
    return get_remote_address(request) or "127.0.0.1"


limiter = Limiter(key_func=get_rate_limit_key)

app = FastAPI(
    title="TalentLens Resume Screening System",
    description="Automated candidate screening and ranking for SDE AI internship.",
    version="1.0.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
        "https://talentlens.buildwithaveeck.com",
        "https://buildwithaveeck.com",
    ],
    allow_origin_regex=r"https://.*(\.vercel\.app|\.buildwithaveeck\.com)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pipeline instance
pipeline = ScreeningPipeline()

# Cache reports per user in memory (and global fallback for backward-compat / CLI tests)
user_reports: Dict[str, ScreeningReport] = {}
latest_report: Optional[ScreeningReport] = None


class ScreenRequest(BaseModel):
    input_dir: str = "./resumes"
    target_role: Optional[str] = "Python Developer"
    required_skills: Optional[List[str]] = None
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


@app.get("/ping")
@app.get("/api/ping")
def ping_endpoint():
    """Lightweight 200 OK ping for keep-alive services and monitoring."""
    return {"status": "pong", "time": time.time()}


@app.get("/keepalive")
@app.get("/api/keepalive")
def keepalive_endpoint():
    """Keepalive heartbeat endpoint called by cron/pingers to prevent idle spin-down."""
    return {
        "status": "awake",
        "service": "TalentLens Candidate Screening",
        "utc_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


def _keepalive_worker():
    """Background worker that periodically pings the public health check to prevent idle shutdown."""
    target_url = os.environ.get("RENDER_EXTERNAL_URL") or "https://backend-talentlens.onrender.com"
    health_url = f"{target_url.rstrip('/')}/health"
    time.sleep(20)  # Initial delay for server startup
    while True:
        try:
            req = urllib.request.Request(
                health_url,
                headers={"User-Agent": "TalentLens-KeepAlive-Worker/1.0"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                logger.info("Keep-alive self ping status: %s", resp.status)
        except Exception as e:
            logger.debug("Keep-alive self ping: %s", e)
        # Sleep for 7 minutes (420 seconds) - well below Render's 15-minute sleep threshold
        time.sleep(420)


@app.on_event("startup")
def startup_keepalive():
    """Launch background self-ping thread on cloud deployments."""
    # Always run keep-alive thread on Render or when deployed
    if os.environ.get("RENDER") or os.environ.get("RENDER_EXTERNAL_URL") or not settings.DEBUG:
        t = threading.Thread(target=_keepalive_worker, daemon=True, name="keepalive-worker")
        t.start()
        logger.info("Background keep-alive self-pinger initialized (every 7 minutes).")


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


@app.get("/api/user/quota", response_model=UserQuota)
def get_user_quota_endpoint(user: AuthUser = Depends(get_current_user)):
    """Return current user's tier, usage count, remaining screenings, and batch resume limit."""
    return quota_manager.get_user_quota(user.id)


@app.post("/api/user/upgrade", response_model=UserQuota)
def upgrade_user_tier_endpoint(req: UpgradeRequest, user: AuthUser = Depends(get_current_user)):
    """Upgrade user subscription tier (restricted to admin or dev environment)."""
    if not user.is_dev and user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Unauthorized. Paid tier upgrades must be completed through payment verification.",
        )
    return quota_manager.upgrade_user_tier(user.id, req.tier)


@app.post("/api/user/reset_quota", response_model=UserQuota)
def reset_user_quota_endpoint(user: AuthUser = Depends(get_current_user)):
    """Reset screenings usage back to 0 for current user (restricted to admin or dev environment)."""
    if not user.is_dev and user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Unauthorized. Resetting quota is restricted to administrators.",
        )
    return quota_manager.reset_user_quota(user.id)


# -------------------------------------------------------------
# Razorpay Payments Endpoints
# -------------------------------------------------------------

@app.post("/api/payments/create-order", response_model=CreateOrderResponse)
def create_payment_order(req: CreateOrderRequest, user: AuthUser = Depends(get_current_user)):
    """Create a new Razorpay checkout order for plan upgrade."""
    order_data = create_order(user_id=user.id, tier=req.tier, currency=req.currency)
    return CreateOrderResponse(**order_data)


@app.post("/api/payments/verify", response_model=VerifyPaymentResponse)
def verify_payment_endpoint(req: VerifyPaymentRequest, user: AuthUser = Depends(get_current_user)):
    """Verify Razorpay payment signature and upgrade user tier."""
    is_valid = verify_payment_signature(
        razorpay_order_id=req.razorpay_order_id,
        razorpay_payment_id=req.razorpay_payment_id,
        razorpay_signature=req.razorpay_signature,
    )
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail="Invalid payment signature. Verification failed.",
        )

    updated_quota = quota_manager.mark_payment_successful(
        order_id=req.razorpay_order_id,
        payment_id=req.razorpay_payment_id,
        signature=req.razorpay_signature,
    )
    if not updated_quota:
        updated_quota = quota_manager.upgrade_user_tier(user.id, req.tier)

    return VerifyPaymentResponse(
        status="success",
        message="Payment verified successfully. Your account has been upgraded!",
        tier=updated_quota.tier,
        quota=updated_quota,
    )


# -------------------------------------------------------------
# API Key Management Endpoints
# -------------------------------------------------------------

@app.get("/api/user/keys", response_model=List[ApiKeyInfo])
def list_user_api_keys(user: AuthUser = Depends(get_current_user)):
    """List all developer API keys belonging to current user (secrets masked)."""
    return quota_manager.list_api_keys(user.id)


@app.post("/api/user/keys", response_model=CreateApiKeyResponse)
def create_user_api_key(req: CreateApiKeyRequest, user: AuthUser = Depends(get_current_user)):
    """Generate a new developer API key."""
    return quota_manager.create_api_key(user.id, req.name)


@app.delete("/api/user/keys/{key_id}")
def delete_user_api_key(key_id: str, user: AuthUser = Depends(get_current_user)):
    """Permanently delete an API key."""
    success = quota_manager.delete_api_key(user.id, key_id)
    if not success:
        raise HTTPException(status_code=404, detail="API key not found.")
    return {"status": "success", "message": f"API key {key_id} deleted."}


# -------------------------------------------------------------
# Previous Shortlistings / Screening History Endpoints
# -------------------------------------------------------------

@app.get("/api/history", response_model=List[ScreeningHistoryItem])
def list_screening_history_endpoint(user: AuthUser = Depends(get_current_user)):
    """List all previous shortlisting runs for the current authenticated user."""
    return quota_manager.list_screening_history(user.id)


@app.get("/api/history/{batch_id}", response_model=ScreeningReport)
def get_screening_history_item_endpoint(batch_id: str, user: AuthUser = Depends(get_current_user)):
    """Load the full candidate shortlist report of a previous screening batch."""
    report = quota_manager.get_screening_history_item(user.id, batch_id)
    if not report:
        raise HTTPException(status_code=404, detail="Historical screening shortlist not found.")
    # Also cache in active user session so they can immediately filter & inspect
    user_reports[user.id] = report
    return report


@app.delete("/api/history/{batch_id}")
def delete_screening_history_endpoint(batch_id: str, user: AuthUser = Depends(get_current_user)):
    """Delete a past shortlisting batch from history."""
    deleted = quota_manager.delete_screening_history_item(user.id, batch_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Shortlisting record not found.")
    return {"status": "deleted", "batch_id": batch_id}


# -------------------------------------------------------------
# Developer Public API (B2B / External Integration)
# -------------------------------------------------------------

@app.post("/api/v1/screen", response_model=ScreeningReport)
@limiter.limit("5/minute")
def screen_resumes_api_v1(
    request: Request,
    files: Optional[List[UploadFile]] = File(default=None),
    target_role: Optional[str] = Form("Python Developer"),
    required_skills: Optional[str] = Form(None),
    min_cgpa: Optional[float] = Form(None),
    require_ai: bool = Form(True),
    require_experience: bool = Form(False),
    require_github_link: bool = Form(False),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None),
):
    """
    Public Developer API: Screen a batch of candidate resumes with rate and quota enforcement.
    Rate limit: 5 requests per minute.
    Requires header: `X-API-Key: tl_test_...` or `Authorization: Bearer tl_test_...`
    """
    raw_key = x_api_key
    if not raw_key and authorization and authorization.lower().startswith("bearer "):
        raw_key = authorization[7:].strip()

    if not raw_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API Key. Provide header 'X-API-Key: <your_key>' or 'Authorization: Bearer <your_key>'."
        )

    auth_info = quota_manager.verify_api_key(raw_key)
    if not auth_info:
        raise HTTPException(status_code=401, detail="Invalid or deactivated API key.")

    user_id = auth_info["user_id"]

    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="No resume files uploaded.")

    # Check quota & batch size atomically
    allowed, rejection_msg, user_quota = quota_manager.reserve_quota(user_id, len(files))
    if not allowed:
        if len(files) > user_quota.max_resumes_per_batch:
            raise HTTPException(status_code=400, detail=rejection_msg)
        raise HTTPException(status_code=403, detail=rejection_msg)

    try:
        # Isolated batch directory for developer request
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            for uploaded_file in files:
                safe_name = Path(uploaded_file.filename).name
                file_destination = temp_path / safe_name
                with open(file_destination, "wb") as buffer:
                    shutil.copyfileobj(uploaded_file.file, buffer)

            parsed_skills = (
                [s.strip() for s in required_skills.split(",") if s.strip()]
                if required_skills
                else ["python"]
            )
            preferences = FilterPreferences(
                target_role=target_role or "Python Developer",
                required_skills=parsed_skills,
                min_cgpa=min_cgpa,
                require_ai_project=require_ai,
                require_experience=require_experience,
                require_github_link=require_github_link,
            )

            report = pipeline.process_directory(
                input_dir=temp_path,
                preferences=preferences,
                max_workers=settings.CONCURRENCY_LIMIT,
            )

        return report
    except HTTPException:
        quota_manager.refund_quota(user_id)
        raise
    except Exception as e:
        quota_manager.refund_quota(user_id)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/screen", response_model=ScreeningReport)
def screen_resumes(req: ScreenRequest, user: AuthUser = Depends(get_current_user)):
    """Run batch screening on specified resumes directory with tier and quota validation."""
    global latest_report

    input_path = Path(req.input_dir)
    file_count = 0
    if input_path.exists():
        supported_exts = {".pdf", ".docx", ".doc", ".txt", ".md"}
        file_count = sum(
            1 for f in input_path.iterdir() if f.is_file() and f.suffix.lower() in supported_exts
        )

    # Validate tier and quota limits atomically
    allowed, rejection_msg, user_quota = quota_manager.reserve_quota(user.id, file_count)
    if not allowed:
        if file_count > user_quota.max_resumes_per_batch:
            raise HTTPException(status_code=400, detail=rejection_msg)
        raise HTTPException(status_code=403, detail=rejection_msg)

    preferences = FilterPreferences(
        target_role=req.target_role or "Python Developer",
        required_skills=req.required_skills or ["python"],
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
        user_reports[user.id] = report

        # Record to persistent previous shortlistings history
        quota_manager.save_screening_history(
            user_id=user.id,
            report=report,
            target_role=req.target_role or "Python Developer",
        )

        # Persist results
        pipeline.export_json(report, settings.OUTPUT_FILE)
        csv_file = settings.OUTPUT_FILE.with_suffix(".csv")
        pipeline.export_csv(report, csv_file)
        xlsx_file = settings.OUTPUT_FILE.with_suffix(".xlsx")
        pipeline.export_excel(report, xlsx_file)
        docx_file = settings.OUTPUT_FILE.with_suffix(".docx")
        pipeline.export_docx(report, docx_file)

        return report
    except HTTPException:
        quota_manager.refund_quota(user.id)
        raise
    except Exception as e:
        quota_manager.refund_quota(user.id)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload_and_screen", response_model=ScreeningReport)
async def upload_and_screen(
    files: List[UploadFile] = File(...),
    target_role: Optional[str] = Form("Python Developer"),
    required_skills: Optional[str] = Form(None),
    min_cgpa: Optional[float] = Form(None),
    require_ai: bool = Form(True),
    require_experience: bool = Form(False),
    require_github_link: bool = Form(False),
    user: AuthUser = Depends(get_current_user),
):
    """Upload up to 100 resume files and run screening immediately (fresh batch)."""
    global latest_report

    # Validate user quota and batch size limits atomically
    allowed, rejection_msg, user_quota = quota_manager.reserve_quota(user.id, len(files))
    if not allowed:
        if len(files) > user_quota.max_resumes_per_batch:
            raise HTTPException(status_code=400, detail=rejection_msg)
        raise HTTPException(status_code=403, detail=rejection_msg)

    try:
        # Fresh batch: isolate uploads by user_id so users never collide
        safe_user_dir = re.sub(r'[^\w\-]', '_', user.id)
        user_uploads_dir = uploads_dir / safe_user_dir
        user_uploads_dir.mkdir(parents=True, exist_ok=True)
        for existing in user_uploads_dir.iterdir():
            try:
                if existing.is_file():
                    existing.unlink()
            except Exception:
                pass

        for uploaded_file in files:
            safe_name = Path(uploaded_file.filename).name
            file_destination = user_uploads_dir / safe_name
            with open(file_destination, "wb") as buffer:
                shutil.copyfileobj(uploaded_file.file, buffer)

        parsed_skills = [s.strip() for s in required_skills.split(",") if s.strip()] if required_skills else ["python"]
        preferences = FilterPreferences(
            target_role=target_role or "Python Developer",
            required_skills=parsed_skills,
            min_cgpa=min_cgpa,
            require_ai_project=require_ai,
            require_experience=require_experience,
            require_github_link=require_github_link,
        )

        report = pipeline.process_directory(
            input_dir=user_uploads_dir,
            preferences=preferences,
            max_workers=settings.CONCURRENCY_LIMIT,
        )
        latest_report = report
        user_reports[user.id] = report

        # Record to persistent previous shortlistings history
        quota_manager.save_screening_history(
            user_id=user.id,
            report=report,
            target_role=target_role or "Python Developer",
        )

        # Persist results
        pipeline.export_json(report, settings.OUTPUT_FILE)
        csv_file = settings.OUTPUT_FILE.with_suffix(".csv")
        pipeline.export_csv(report, csv_file)
        xlsx_file = settings.OUTPUT_FILE.with_suffix(".xlsx")
        pipeline.export_excel(report, xlsx_file)
        docx_file = settings.OUTPUT_FILE.with_suffix(".docx")
        pipeline.export_docx(report, docx_file)

        return report
    except HTTPException:
        quota_manager.refund_quota(user.id)
        raise
    except Exception as e:
        quota_manager.refund_quota(user.id)
        raise HTTPException(status_code=500, detail=str(e))


# Resume file serving paths
resumes_dir = settings.BASE_DIR / "resumes"
uploads_dir = settings.BASE_DIR / "uploads"
uploads_dir.mkdir(parents=True, exist_ok=True)


@app.get("/resumes/{file_name:path}")
@app.get("/api/resume/{file_name:path}")
def serve_resume(file_name: str, user: AuthUser = Depends(get_current_user)):
    """Serve the exact original resume file (checking user's uploads first, then sample resumes)."""
    safe_name = Path(file_name).name
    safe_user_dir = re.sub(r'[^\w\-]', '_', user.id)

    # 1. Check user-isolated uploads directory first
    user_upload_path = uploads_dir / safe_user_dir / safe_name
    if user_upload_path.exists() and user_upload_path.is_file():
        media_type = "application/pdf" if user_upload_path.suffix.lower() == ".pdf" else "application/octet-stream"
        return FileResponse(
            path=str(user_upload_path),
            media_type=media_type,
            filename=safe_name,
            headers={
                "Content-Disposition": f"inline; filename=\"{safe_name}\"",
                "Cache-Control": "no-cache, no-store, must-revalidate",
            },
        )

    # 2. Check legacy root uploads directory
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

    # 3. Check base sample resumes directory
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
    """Retrieve the latest screening results for the current authenticated user."""
    global latest_report
    if user.id in user_reports:
        return user_reports[user.id]
    if latest_report and user.is_dev:
        return latest_report

    raise HTTPException(status_code=404, detail="No screening results in this session. Upload resumes first.")


@app.post("/clear")
def clear_session(user: AuthUser = Depends(get_current_user)):
    """Reset to blank state: clear this user's report and isolated upload folder."""
    global latest_report
    user_reports.pop(user.id, None)
    if user.is_dev:
        latest_report = None

    try:
        safe_user_dir = re.sub(r'[^\w\-]', '_', user.id)
        user_uploads_dir = uploads_dir / safe_user_dir
        if user_uploads_dir.exists():
            for f in user_uploads_dir.iterdir():
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


"""Tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
from src.api import app
from src.quota import quota_manager
from src.models import PlanTier

client = TestClient(app)


@pytest.fixture(autouse=True)
def ensure_quota():
    quota_manager.upgrade_user_tier("local-dev", PlanTier.PRO_29)
    quota_manager.reset_user_quota("local-dev")
    yield
    quota_manager.reset_user_quota("local-dev")


def test_api_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_api_dashboard_html():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "<!DOCTYPE html>" in resp.text
    assert "Kasparro Screening System" in resp.text


def test_api_get_results():
    # Blank-start: fresh session has no results until screening runs
    client.post("/clear")
    resp = client.get("/results")
    assert resp.status_code == 404

    # After screening, results appear
    screen = client.post("/screen", json={"input_dir": "./resumes"})
    assert screen.status_code == 200
    resp = client.get("/results")
    assert resp.status_code == 200
    data = resp.json()
    assert "batch_summary" in data
    assert "ranked_candidates" in data
    assert len(data["ranked_candidates"]) > 0


def test_api_clear_resets_to_blank():
    client.post("/screen", json={"input_dir": "./resumes"})
    assert client.get("/results").status_code == 200
    resp = client.post("/clear")
    assert resp.status_code == 200
    assert client.get("/results").status_code == 404
    # Re-screen so later export tests have data
    client.post("/screen", json={"input_dir": "./resumes"})


def test_api_download_csv():
    resp = client.get("/download_csv")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]


def test_api_download_excel():
    resp = client.get("/download_excel")
    assert resp.status_code == 200
    assert "application/vnd.openxmlformats" in resp.headers["content-type"]


def test_api_download_docx():
    resp = client.get("/download_docx")
    assert resp.status_code == 200
    assert "application/vnd.openxmlformats" in resp.headers["content-type"]


def test_api_serve_resume():
    resp = client.get("/resumes/candidate_30.pdf")
    assert resp.status_code == 200
    assert "application/pdf" in resp.headers["content-type"]
    assert "inline" in resp.headers["content-disposition"]


def test_api_serve_resume_not_found():
    resp = client.get("/resumes/non_existent_file.pdf")
    assert resp.status_code == 404


def test_api_export_filtered_excel():
    # Fetch results first to get sample candidates
    results = client.get("/results").json()
    top5 = results["ranked_candidates"][:5]
    resp = client.post("/export_filtered_excel", json={"candidates": top5, "filter_label": "Top 5"})
    assert resp.status_code == 200
    assert "application/vnd.openxmlformats" in resp.headers["content-type"]
    assert "shortlist_top_5.xlsx" in resp.headers["content-disposition"]


def test_api_export_filtered_docx():
    results = client.get("/results").json()
    top5 = results["ranked_candidates"][:5]
    resp = client.post("/export_filtered_docx", json={"candidates": top5, "filter_label": "Top 5"})
    assert resp.status_code == 200
    assert "application/vnd.openxmlformats" in resp.headers["content-type"]
    assert "shortlist_top_5.docx" in resp.headers["content-disposition"]


"""Tests for user tiers and screening quota enforcement."""

import pytest
from fastapi.testclient import TestClient
from src.api import app
from src.models import PlanTier
from src.quota import quota_manager

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_dev_quota():
    """Ensure clean quota for local-dev user before and after each test."""
    quota_manager.upgrade_user_tier("local-dev", PlanTier.FREE)
    quota_manager.reset_user_quota("local-dev")
    yield
    quota_manager.reset_user_quota("local-dev")


def test_get_user_quota_default_free():
    resp = client.get("/api/user/quota")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tier"] == "free"
    assert data["screenings_limit"] == 3
    assert data["screenings_used"] == 0
    assert data["screenings_remaining"] == 3
    assert data["max_resumes_per_batch"] == 50
    assert data["can_screen"] is True


def test_quota_rejection_when_exceeded():
    # Consume all 3 screenings
    quota_manager.consume_quota("local-dev")
    quota_manager.consume_quota("local-dev")
    quota_manager.consume_quota("local-dev")

    quota = quota_manager.get_user_quota("local-dev")
    assert quota.screenings_remaining == 0
    assert quota.can_screen is False

    # Attempt to screen via API -> should return 403 Forbidden
    resp = client.post("/screen", json={"input_dir": "./resumes"})
    assert resp.status_code == 403
    assert "Free screening limit reached" in resp.json()["detail"]
    assert "Upgrade to Recruiter Pro ($29)" in resp.json()["detail"]


def test_upgrade_to_pro_tier_increases_limits():
    # Upgrade to Paid $29 tier
    resp = client.post("/api/user/upgrade", json={"tier": "pro_29"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["tier"] == "pro_29"
    assert data["tier_display_name"] == "Recruiter Pro"
    assert data["price_usd"] == 29
    assert data["screenings_limit"] == 30
    assert data["max_resumes_per_batch"] == 100
    assert data["can_screen"] is True


def test_batch_size_rejection_over_50_for_free():
    # Generate 51 dummy files for upload
    files = [
        ("files", (f"resume_{i}.txt", b"Python developer with FastAPI experience.", "text/plain"))
        for i in range(51)
    ]
    resp = client.post("/upload_and_screen", files=files)
    assert resp.status_code == 400
    assert "Free plan allows up to 50 resumes per batch" in resp.json()["detail"]


def test_pro_tier_allows_up_to_100_resumes():
    # Upgrade to Pro
    client.post("/api/user/upgrade", json={"tier": "pro_29"})

    # 51 files should now be allowed (below 100)
    files = [
        ("files", (f"resume_{i}.txt", b"Python and Machine Learning developer with LangChain.", "text/plain"))
        for i in range(5)
    ]
    resp = client.post("/upload_and_screen", files=files)
    assert resp.status_code == 200

    # Quota should reflect 1 screening consumed
    quota_resp = client.get("/api/user/quota")
    assert quota_resp.status_code == 200
    quota_data = quota_resp.json()
    assert quota_data["screenings_used"] == 1
    assert quota_data["screenings_remaining"] == 29


def test_reset_quota_endpoint():
    quota_manager.consume_quota("local-dev")
    assert quota_manager.get_user_quota("local-dev").screenings_used == 1

    resp = client.post("/api/user/reset_quota")
    assert resp.status_code == 200
    data = resp.json()
    assert data["screenings_used"] == 0
    assert data["screenings_remaining"] == data["screenings_limit"]

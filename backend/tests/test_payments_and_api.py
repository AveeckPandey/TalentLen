"""Tests for Razorpay payment integration, API Key lifecycle, and Developer Public API."""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from src.api import app
from src.quota import QuotaManager
from src.models import PlanTier

client = TestClient(app)


@pytest.fixture
def temp_quota_mgr(tmp_path):
    """Fixture providing isolated QuotaManager instance with temporary SQLite database."""
    db_file = tmp_path / "test_quotas.db"
    return QuotaManager(db_path=db_file)


def test_api_key_lifecycle(temp_quota_mgr):
    """Test generating, listing, verifying, and permanently deleting API keys."""
    user_id = "recruiter_test_123"

    # 1. Create Key
    created = temp_quota_mgr.create_api_key(user_id, name="Production ATS Key")
    assert created.key_id.startswith("key_")
    assert created.api_key.startswith("tl_test_")
    assert created.name == "Production ATS Key"

    # 2. Verify Key
    auth_info = temp_quota_mgr.verify_api_key(created.api_key)
    assert auth_info is not None
    assert auth_info["user_id"] == user_id
    assert auth_info["tier"] == PlanTier.FREE

    # 3. List Keys
    keys = temp_quota_mgr.list_api_keys(user_id)
    assert len(keys) == 1
    assert keys[0].key_id == created.key_id

    # 4. Delete Key
    deleted = temp_quota_mgr.delete_api_key(user_id, created.key_id)
    assert deleted is True

    # 5. Verify Deleted Key is gone from list and verification fails
    keys_after = temp_quota_mgr.list_api_keys(user_id)
    assert len(keys_after) == 0
    auth_info_deleted = temp_quota_mgr.verify_api_key(created.api_key)
    assert auth_info_deleted is None


def test_delete_api_key_endpoint():
    """Test DELETE /api/user/keys/{key_id} permanently removes the key."""
    # Create key
    created_resp = client.post("/api/user/keys", json={"name": "Disposable Key"})
    assert created_resp.status_code == 200
    key_id = created_resp.json()["key_id"]

    # Delete key
    del_resp = client.delete(f"/api/user/keys/{key_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "success"

    # Verify key no longer exists in list
    list_resp = client.get("/api/user/keys")
    active_ids = [k["key_id"] for k in list_resp.json()]
    assert key_id not in active_ids


def test_razorpay_create_order_endpoint():
    """Test creating a Razorpay order via POST /api/payments/create-order."""
    resp = client.post("/api/payments/create-order", json={"tier": "pro_29", "currency": "INR"})
    assert resp.status_code == 200
    data = resp.json()
    assert "order_id" in data
    assert data["order_id"].startswith("order_")
    assert data["amount"] == 249900  # ₹2,499
    assert data["currency"] == "INR"
    assert data["key_id"].startswith("rzp_test_")


def test_razorpay_verify_invalid_signature():
    """Test that forged or invalid payment signature fails verification."""
    payload = {
        "razorpay_order_id": "order_fake123",
        "razorpay_payment_id": "pay_fake123",
        "razorpay_signature": "invalid_forged_signature_hash",
        "tier": "pro_29",
    }
    resp = client.post("/api/payments/verify", json=payload)
    assert resp.status_code == 400
    assert "Invalid payment signature" in resp.json()["detail"]


def test_developer_api_unauthorized_without_key():
    """Test that calling /api/v1/screen without API key returns 401."""
    resp = client.post("/api/v1/screen")
    assert resp.status_code == 401
    assert "Missing API Key" in resp.json()["detail"]


def test_developer_api_unauthorized_with_bogus_key():
    """Test that calling /api/v1/screen with non-existent API key returns 401."""
    resp = client.post("/api/v1/screen", headers={"X-API-Key": "tl_test_bogus_fake_key_12345"})
    assert resp.status_code == 401
    assert "Invalid or deactivated API key" in resp.json()["detail"]


def test_developer_api_success_with_valid_key(tmp_path):
    """Test screening via public API using an active API key."""
    # Create an API key via the API endpoint
    key_resp = client.post("/api/user/keys", json={"name": "Test Key"})
    assert key_resp.status_code == 200
    api_key = key_resp.json()["api_key"]

    # Create dummy resume text
    resume_file = tmp_path / "alice.txt"
    resume_file.write_text("Alice Smith\nPython Developer with 3 years FastAPI and LangChain experience.\nGPA: 8.5/10")

    with open(resume_file, "rb") as f:
        resp = client.post(
            "/api/v1/screen",
            headers={"X-API-Key": api_key},
            files=[("files", ("alice.txt", f, "text/plain"))],
            data={"target_role": "Python Developer", "require_ai": "false"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["batch_summary"]["total_resumes"] == 1
    all_candidates = data.get("ranked_candidates", []) + data.get("rejected_candidates", [])
    assert len(all_candidates) == 1
    assert all_candidates[0]["candidate_name"] == "Alice Smith"


def test_developer_api_rate_limit_exceeded(tmp_path):
    """Test that exceeding the 5 req/min rate limit triggers HTTP 429."""
    key_resp = client.post("/api/user/keys", json={"name": "Rate Limit Test Key"})
    api_key = key_resp.json()["api_key"]

    resume_file = tmp_path / "bob.txt"
    resume_file.write_text("Bob Vance\nPython Engineer with Django and AWS.")

    status_codes = []
    # Send 7 rapid requests (limit is 5/minute)
    for _ in range(7):
        with open(resume_file, "rb") as f:
            r = client.post(
                "/api/v1/screen",
                headers={"X-API-Key": api_key},
                files=[("files", ("bob.txt", f, "text/plain"))],
                data={"target_role": "Python Developer", "require_ai": "false"},
            )
            status_codes.append(r.status_code)

    assert 429 in status_codes, f"Expected 429 Too Many Requests, got: {status_codes}"

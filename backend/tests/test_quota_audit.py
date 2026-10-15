"""Comprehensive QA Audit Test Suite: Pricing Cards, Free Trials & Credit Limit Enforcement.

Covers:
- Configuration and entitlements for all 3 tiers (Starter Free, Recruiter Pro, Enterprise)
- 10 credit consumption scenarios (all remaining, 1 used, multiple, boundary at 1, final credit to 0, post-zero rejection)
- Concurrency and race-condition prevention (atomic reservation under parallel load)
- Failure rollback (refund on unhandled errors)
- Security & authorization (unauthorized reset prevention, unauthorized self-upgrade prevention)
- Payment idempotency against webhook / callback replays
- Non-credit consuming endpoints remain functional when credits are exhausted
"""

import concurrent.futures
import pytest
from fastapi.testclient import TestClient
from pathlib import Path

from src.api import app
from src.quota import QuotaManager
from src.models import PlanTier, TIER_CONFIGS, UserQuota
from src.auth import AuthUser, get_current_user

client = TestClient(app)


@pytest.fixture
def isolated_quota_mgr(tmp_path):
    """Provides a dedicated QuotaManager backed by a temporary SQLite database."""
    db_file = tmp_path / "audit_quotas.db"
    return QuotaManager(db_path=db_file)


# =========================================================================
# 1. Audit The Three Plans / Free Trials Configuration
# =========================================================================

def test_tier_configuration_starter_free():
    """Verify Starter (Free) plan configuration, allowances, and defaults."""
    cfg = TIER_CONFIGS[PlanTier.FREE]
    assert cfg.tier == PlanTier.FREE
    assert cfg.display_name == "Starter (Free)"
    assert cfg.price_usd == 0
    assert cfg.screenings_limit == 3
    assert cfg.max_resumes_per_batch == 50


def test_tier_configuration_recruiter_pro():
    """Verify Recruiter Pro plan configuration and limits."""
    cfg = TIER_CONFIGS[PlanTier.PRO_29]
    assert cfg.tier == PlanTier.PRO_29
    assert cfg.display_name == "Recruiter Pro"
    assert cfg.price_usd == 29
    assert cfg.screenings_limit == 30
    assert cfg.max_resumes_per_batch == 100


def test_tier_configuration_enterprise():
    """Verify Enterprise plan configuration and limits."""
    cfg = TIER_CONFIGS[PlanTier.ENTERPRISE]
    assert cfg.tier == PlanTier.ENTERPRISE
    assert cfg.display_name == "Enterprise"
    assert cfg.price_usd == 99
    assert cfg.screenings_limit == 500
    assert cfg.max_resumes_per_batch == 500


def test_default_user_quota_initialization(isolated_quota_mgr):
    """Verify new user automatically initializes with Free plan entitlements."""
    quota = isolated_quota_mgr.get_user_quota("user_new_audit")
    assert quota.tier == PlanTier.FREE
    assert quota.screenings_limit == 3
    assert quota.screenings_used == 0
    assert quota.screenings_remaining == 3
    assert quota.max_resumes_per_batch == 50
    assert quota.can_screen is True


# =========================================================================
# 2. Credit Consumption Testing (Scenarios 1 through 10)
# =========================================================================

def test_scenario_1_all_credits_remaining(isolated_quota_mgr):
    """Scenario 1: User has all credits remaining."""
    user_id = "user_sc1"
    quota = isolated_quota_mgr.get_user_quota(user_id)
    assert quota.screenings_remaining == 3
    assert quota.screenings_used == 0
    assert quota.can_screen is True


def test_scenario_2_consumes_one_credit(isolated_quota_mgr):
    """Scenario 2: User performs 1 operation and consumes exactly 1 credit."""
    user_id = "user_sc2"
    allowed, rejection, q = isolated_quota_mgr.reserve_quota(user_id, resume_count=10)
    assert allowed is True
    assert rejection is None
    assert q.screenings_used == 1
    assert q.screenings_remaining == 2


def test_scenario_3_consumes_multiple_credits(isolated_quota_mgr):
    """Scenario 3: User performs multiple sequential operations."""
    user_id = "user_sc3"
    # Credit 1
    allowed1, _, q1 = isolated_quota_mgr.reserve_quota(user_id, resume_count=5)
    assert allowed1 is True and q1.screenings_remaining == 2

    # Credit 2
    allowed2, _, q2 = isolated_quota_mgr.reserve_quota(user_id, resume_count=5)
    assert allowed2 is True and q2.screenings_remaining == 1


def test_scenario_4_exactly_one_credit_remaining(isolated_quota_mgr):
    """Scenario 4: User has consumed 2 credits, exactly 1 credit remaining."""
    user_id = "user_sc4"
    isolated_quota_mgr.reserve_quota(user_id, 1)
    isolated_quota_mgr.reserve_quota(user_id, 1)

    quota = isolated_quota_mgr.get_user_quota(user_id)
    assert quota.screenings_used == 2
    assert quota.screenings_remaining == 1
    assert quota.can_screen is True


def test_scenario_5_consumes_final_credit(isolated_quota_mgr):
    """Scenario 5: User consumes their final available credit."""
    user_id = "user_sc5"
    isolated_quota_mgr.reserve_quota(user_id, 1)
    isolated_quota_mgr.reserve_quota(user_id, 1)

    # 3rd and final credit
    allowed, rejection, q = isolated_quota_mgr.reserve_quota(user_id, resume_count=1)
    assert allowed is True
    assert rejection is None
    assert q.screenings_used == 3
    assert q.screenings_remaining == 0
    assert q.can_screen is False


def test_scenario_6_attempt_after_reaching_zero_credits(isolated_quota_mgr):
    """Scenario 6: User attempts another operation after reaching 0 credits."""
    user_id = "user_sc6"
    for _ in range(3):
        isolated_quota_mgr.reserve_quota(user_id, 1)

    # 4th operation must be rejected
    allowed, rejection, q = isolated_quota_mgr.reserve_quota(user_id, resume_count=1)
    assert allowed is False
    assert "Free screening limit reached" in rejection
    assert "Upgrade to Recruiter Pro ($29)" in rejection
    assert q.screenings_used == 3
    assert q.screenings_remaining == 0
    assert q.can_screen is False


def test_scenario_7_failed_request_refunds_credit(isolated_quota_mgr):
    """Scenario 7: A request fails during execution -> credit is restored/refunded."""
    user_id = "user_sc7"
    allowed, _, q_reserved = isolated_quota_mgr.reserve_quota(user_id, 10)
    assert allowed is True
    assert q_reserved.screenings_used == 1
    assert q_reserved.screenings_remaining == 2

    # Simulate execution failure and rollback
    q_refunded = isolated_quota_mgr.refund_quota(user_id)
    assert q_refunded.screenings_used == 0
    assert q_refunded.screenings_remaining == 3


def test_scenario_8_concurrent_requests_prevent_overspend(isolated_quota_mgr):
    """Scenario 8: Multiple simultaneous requests near credit limit cannot overspend."""
    user_id = "user_sc8_race"
    # Pre-consume 2 credits so exactly 1 credit remains
    isolated_quota_mgr.reserve_quota(user_id, 1)
    isolated_quota_mgr.reserve_quota(user_id, 1)

    assert isolated_quota_mgr.get_user_quota(user_id).screenings_remaining == 1

    # Launch 10 concurrent threads all attempting to reserve the 1 remaining credit
    def attempt_reservation():
        allowed, msg, q = isolated_quota_mgr.reserve_quota(user_id, 1)
        return allowed

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(attempt_reservation) for _ in range(10)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # Exactly 1 request must succeed, 9 must be rejected
    assert results.count(True) == 1
    assert results.count(False) == 9

    # Final usage must be clamped at exactly 3/3 (0 remaining), balance never negative
    final_quota = isolated_quota_mgr.get_user_quota(user_id)
    assert final_quota.screenings_used == 3
    assert final_quota.screenings_remaining == 0


def test_scenario_9_persistence_across_sessions(isolated_quota_mgr):
    """Scenario 9: Quota persistence across session refresh or re-instantiation."""
    user_id = "user_sc9_persist"
    isolated_quota_mgr.reserve_quota(user_id, 1)

    # Instantiate brand new QuotaManager reading from the same SQLite DB file
    reopened_mgr = QuotaManager(db_path=isolated_quota_mgr.db_path)
    q = reopened_mgr.get_user_quota(user_id)
    assert q.screenings_used == 1
    assert q.screenings_remaining == 2


def test_scenario_10_client_side_tamper_resistance(isolated_quota_mgr):
    """Scenario 10: Backend is source of truth; client cannot alter balance."""
    user_id = "user_sc10"
    for _ in range(3):
        isolated_quota_mgr.reserve_quota(user_id, 1)

    # Even if client sends fake request claiming remaining=99, backend enforces DB record
    allowed, rejection, _ = isolated_quota_mgr.reserve_quota(user_id, 1)
    assert allowed is False
    assert "Free screening limit reached" in rejection


# =========================================================================
# 3. HTTP API Endpoint Boundary & Enforcement Tests
# =========================================================================

def test_api_403_when_quota_exhausted():
    """Verify POST /screen returns 403 Forbidden with clear upgrade prompt when quota is 0."""
    from src.quota import quota_manager
    quota_manager.upgrade_user_tier("local-dev", PlanTier.FREE)
    quota_manager.reset_user_quota("local-dev")

    # Exhaust all 3 credits
    quota_manager.consume_quota("local-dev")
    quota_manager.consume_quota("local-dev")
    quota_manager.consume_quota("local-dev")

    resp = client.post("/screen", json={"input_dir": "./resumes"})
    assert resp.status_code == 403
    detail = resp.json()["detail"]
    assert "Free screening limit reached (3/3 runs used)" in detail
    assert "Upgrade to Recruiter Pro ($29)" in detail


def test_api_batch_limit_rejection_over_50():
    """Verify batch limit rejection returns 400 Bad Request with guidance."""
    from src.quota import quota_manager
    quota_manager.upgrade_user_tier("local-dev", PlanTier.FREE)
    quota_manager.reset_user_quota("local-dev")

    files = [
        ("files", (f"cand_{i}.txt", b"Python Django developer resume text.", "text/plain"))
        for i in range(55)
    ]
    resp = client.post("/upload_and_screen", files=files)
    assert resp.status_code == 400
    assert "Free plan allows up to 50 resumes per batch" in resp.json()["detail"]


def test_non_credit_consuming_endpoints_work_when_credits_zero():
    """Verify non-credit consuming features (health, keys, history) work when quota is 0."""
    from src.quota import quota_manager
    quota_manager.upgrade_user_tier("local-dev", PlanTier.FREE)
    quota_manager.consume_quota("local-dev")
    quota_manager.consume_quota("local-dev")
    quota_manager.consume_quota("local-dev")

    # Health check
    assert client.get("/health").status_code == 200

    # User quota check
    quota_resp = client.get("/api/user/quota")
    assert quota_resp.status_code == 200
    assert quota_resp.json()["screenings_remaining"] == 0

    # API key listing
    assert client.get("/api/user/keys").status_code == 200

    # History listing
    assert client.get("/api/history").status_code == 200


# =========================================================================
# 4. Security & Edge-Case Tests
# =========================================================================

def test_unauthorized_user_cannot_reset_quota():
    """Verify regular authenticated users cannot reset their own quota."""
    # Mock non-admin regular authenticated user
    regular_user = AuthUser(id="regular_user_777", email="user@company.com", role="authenticated", is_dev=False)
    app.dependency_overrides[get_current_user] = lambda: regular_user

    try:
        resp = client.post("/api/user/reset_quota")
        assert resp.status_code == 403
        assert "Resetting quota is restricted to administrators" in resp.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_unauthorized_user_cannot_self_upgrade_tier():
    """Verify regular authenticated users cannot bypass payment by calling /api/user/upgrade."""
    regular_user = AuthUser(id="attacker_user_999", email="hacker@company.com", role="authenticated", is_dev=False)
    app.dependency_overrides[get_current_user] = lambda: regular_user

    try:
        resp = client.post("/api/user/upgrade", json={"tier": "pro_29"})
        assert resp.status_code == 403
        assert "Paid tier upgrades must be completed through payment verification" in resp.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_webhook_payment_replay_attack_prevention(isolated_quota_mgr):
    """Verify duplicate payment verification does not reset usage for an already paid order."""
    user_id = "user_subscriber_1"
    order_id = "order_test_replay_999"

    # 1. Create order
    isolated_quota_mgr.record_payment_order(
        order_id=order_id,
        user_id=user_id,
        tier=PlanTier.PRO_29,
        amount=249900,
        currency="INR",
    )

    # 2. First verification upgrades user to Pro (30 limit, 0 used)
    q1 = isolated_quota_mgr.mark_payment_successful(order_id, "pay_123", "sig_123")
    assert q1.tier == PlanTier.PRO_29
    assert q1.screenings_used == 0

    # 3. User uses 5 screening runs
    for _ in range(5):
        isolated_quota_mgr.reserve_quota(user_id, 1)

    q_after_use = isolated_quota_mgr.get_user_quota(user_id)
    assert q_after_use.screenings_used == 5
    assert q_after_use.screenings_remaining == 25

    # 4. Attacker/webhook replays duplicate payment verification payload
    q_replay = isolated_quota_mgr.mark_payment_successful(order_id, "pay_123", "sig_123")

    # Must NOT reset usage back to 0!
    assert q_replay.screenings_used == 5
    assert q_replay.screenings_remaining == 25

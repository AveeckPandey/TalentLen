"""Tier and quota management with persistent storage and usage tracking."""

import json
import sqlite3
import logging
import secrets
import hashlib
import uuid
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from src.config import settings
from src.models import (
    PlanTier,
    TierConfig,
    TIER_CONFIGS,
    UserQuota,
    ApiKeyInfo,
    CreateApiKeyResponse,
    ScreeningHistoryItem,
    ScreeningReport,
)

logger = logging.getLogger(__name__)


class QuotaManager:
    """Manages persistent user tiers, screening runs, batch limits, API keys, and payments."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            output_dir = settings.BASE_DIR / "output"
            output_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = output_dir / "quotas.db"
        else:
            self.db_path = db_path

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=20.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _init_db(self) -> None:
        """Create user quotas, api_keys, and payments tables if they do not exist."""
        try:
            with self._get_connection() as conn:
                # 1. User Quotas
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS user_quotas (
                        user_id TEXT PRIMARY KEY,
                        tier TEXT NOT NULL DEFAULT 'free',
                        screenings_used INTEGER NOT NULL DEFAULT 0,
                        custom_limit INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )

                # 2. API Keys for external developers / ATS integrations
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS api_keys (
                        key_id TEXT PRIMARY KEY,
                        key_hash TEXT NOT NULL UNIQUE,
                        key_prefix TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        name TEXT NOT NULL DEFAULT 'Default API Key',
                        is_active INTEGER NOT NULL DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_used_at TIMESTAMP
                    )
                    """
                )
                conn.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys(user_id)")

                # 3. Payments (Razorpay Orders & Transactions)
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS payments (
                        order_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        tier TEXT NOT NULL,
                        amount INTEGER NOT NULL,
                        currency TEXT NOT NULL DEFAULT 'INR',
                        status TEXT NOT NULL DEFAULT 'created',
                        payment_id TEXT,
                        signature TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                conn.execute("CREATE INDEX IF NOT EXISTS idx_payments_user ON payments(user_id)")

                # 4. Screening History for previous shortlistings
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS screening_history (
                        batch_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        target_role TEXT NOT NULL DEFAULT 'Python Developer',
                        total_resumes INTEGER NOT NULL DEFAULT 0,
                        eligible_count INTEGER NOT NULL DEFAULT 0,
                        rejected_count INTEGER NOT NULL DEFAULT 0,
                        avg_score REAL NOT NULL DEFAULT 0.0,
                        top_score REAL NOT NULL DEFAULT 0.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        report_json TEXT NOT NULL
                    )
                    """
                )
                conn.execute("CREATE INDEX IF NOT EXISTS idx_screening_history_user ON screening_history(user_id, created_at DESC)")

                conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize quotas DB: {e}")

    def get_user_quota(self, user_id: str) -> UserQuota:
        """Retrieve the quota details for a given user ID. Defaults to Free tier."""
        user_id = str(user_id or "anonymous").strip()

        try:
            with self._get_connection() as conn:
                row = conn.execute(
                    "SELECT tier, screenings_used, custom_limit FROM user_quotas WHERE user_id = ?",
                    (user_id,),
                ).fetchone()

                if not row:
                    # Initialize default Free tier record
                    conn.execute(
                        "INSERT INTO user_quotas (user_id, tier, screenings_used) VALUES (?, 'free', 0)",
                        (user_id,),
                    )
                    conn.commit()
                    tier_str = "free"
                    used = 0
                    custom_limit = None
                else:
                    tier_str = row["tier"] or "free"
                    used = int(row["screenings_used"] or 0)
                    custom_limit = row["custom_limit"]
        except Exception as e:
            logger.warning(f"Error querying user quota for {user_id}, using fallback: {e}")
            tier_str = "free"
            used = 0
            custom_limit = None

        try:
            tier = PlanTier(tier_str)
        except ValueError:
            tier = PlanTier.FREE

        config = TIER_CONFIGS.get(tier, TIER_CONFIGS[PlanTier.FREE])
        limit = custom_limit if custom_limit is not None else config.screenings_limit
        remaining = max(0, limit - used)

        return UserQuota(
            user_id=user_id,
            tier=tier,
            tier_display_name=config.display_name,
            price_usd=config.price_usd,
            screenings_limit=limit,
            screenings_used=used,
            screenings_remaining=remaining,
            max_resumes_per_batch=config.max_resumes_per_batch,
            can_screen=(remaining > 0),
        )

    def check_quota(self, user_id: str, resume_count: int) -> Tuple[bool, Optional[str]]:
        """
        Validate whether a candidate screening request is allowed under current user quota.
        Returns:
            (allowed: bool, rejection_message: Optional[str])
        """
        quota = self.get_user_quota(user_id)

        # 1. Batch size limit check
        if resume_count > quota.max_resumes_per_batch:
            if quota.tier == PlanTier.FREE:
                return (
                    False,
                    f"Free plan allows up to {quota.max_resumes_per_batch} resumes per batch "
                    f"(uploaded {resume_count}). Upgrade to Recruiter Pro ($29) for up to 100 resumes.",
                )
            return (
                False,
                f"Your {quota.tier_display_name} tier limit is {quota.max_resumes_per_batch} resumes per batch "
                f"(received {resume_count}). Please reduce the batch size.",
            )

        # 2. Screening run count check
        if quota.screenings_remaining <= 0:
            if quota.tier == PlanTier.FREE:
                return (
                    False,
                    f"Free screening limit reached ({quota.screenings_used}/{quota.screenings_limit} runs used). "
                    f"Upgrade to Recruiter Pro ($29) to get 30 screening runs and 100 resumes/batch.",
                )
            return (
                False,
                f"Screening limit reached for {quota.tier_display_name} "
                f"({quota.screenings_used}/{quota.screenings_limit} used).",
            )

        return True, None

    def reserve_quota(self, user_id: str, resume_count: int) -> Tuple[bool, Optional[str], UserQuota]:
        """
        Atomically check and reserve 1 screening credit for the user.
        Prevents concurrency race conditions / overspending by using an atomic SQL UPDATE.
        Returns:
            (allowed: bool, rejection_message: Optional[str], quota: UserQuota)
        """
        user_id = str(user_id or "anonymous").strip()
        quota = self.get_user_quota(user_id)

        # 1. Validate batch size
        if resume_count > quota.max_resumes_per_batch:
            if quota.tier == PlanTier.FREE:
                return (
                    False,
                    f"Free plan allows up to {quota.max_resumes_per_batch} resumes per batch "
                    f"(uploaded {resume_count}). Upgrade to Recruiter Pro ($29) for up to 100 resumes.",
                    quota,
                )
            return (
                False,
                f"Your {quota.tier_display_name} tier limit is {quota.max_resumes_per_batch} resumes per batch "
                f"(received {resume_count}). Please reduce the batch size.",
                quota,
            )

        # 2. Atomic reservation with strictly bounded limit
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """
                    UPDATE user_quotas
                    SET screenings_used = screenings_used + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                      AND screenings_used < (
                          CASE
                              WHEN custom_limit IS NOT NULL THEN custom_limit
                              WHEN tier = 'enterprise' THEN 500
                              WHEN tier = 'pro_29' THEN 30
                              ELSE 3
                          END
                      )
                    """,
                    (user_id,),
                )
                conn.commit()

                if cursor.rowcount > 0:
                    updated = self.get_user_quota(user_id)
                    return True, None, updated
        except Exception as e:
            logger.error(f"Error executing atomic reserve_quota for user {user_id}: {e}")

        # Limit was already reached (cursor.rowcount == 0)
        curr = self.get_user_quota(user_id)
        if curr.tier == PlanTier.FREE:
            msg = (
                f"Free screening limit reached ({curr.screenings_used}/{curr.screenings_limit} runs used). "
                f"Upgrade to Recruiter Pro ($29) to get 30 screening runs and 100 resumes/batch."
            )
        else:
            msg = (
                f"Screening limit reached for {curr.tier_display_name} "
                f"({curr.screenings_used}/{curr.screenings_limit} used)."
            )
        return False, msg, curr

    def refund_quota(self, user_id: str) -> UserQuota:
        """Rollback 1 screening run if execution failed, ensuring user is never billed for failed runs."""
        user_id = str(user_id or "anonymous").strip()
        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    UPDATE user_quotas
                    SET screenings_used = MAX(0, screenings_used - 1),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                    """,
                    (user_id,),
                )
                conn.commit()
                logger.info(f"Refunded 1 screening credit for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to refund quota for user {user_id}: {e}")

        return self.get_user_quota(user_id)

    def consume_quota(self, user_id: str) -> UserQuota:
        """Increment screenings_used by 1 upon successful execution."""
        user_id = str(user_id or "anonymous").strip()

        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO user_quotas (user_id, tier, screenings_used, updated_at)
                    VALUES (?, 'free', 1, CURRENT_TIMESTAMP)
                    ON CONFLICT(user_id) DO UPDATE SET
                        screenings_used = user_quotas.screenings_used + 1,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (user_id,),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to consume quota for user {user_id}: {e}")

        return self.get_user_quota(user_id)

    def upgrade_user_tier(self, user_id: str, new_tier: PlanTier) -> UserQuota:
        """Upgrade a user's subscription tier (e.g. from free to pro_29)."""
        user_id = str(user_id or "anonymous").strip()

        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO user_quotas (user_id, tier, screenings_used, updated_at)
                    VALUES (?, ?, 0, CURRENT_TIMESTAMP)
                    ON CONFLICT(user_id) DO UPDATE SET
                        tier = excluded.tier,
                        screenings_used = 0,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (user_id, new_tier.value),
                )
                conn.commit()
            logger.info(f"User {user_id} upgraded to tier {new_tier.value}")
        except Exception as e:
            logger.error(f"Failed to upgrade tier for user {user_id}: {e}")

        return self.get_user_quota(user_id)

    def reset_user_quota(self, user_id: str) -> UserQuota:
        """Reset screenings_used back to 0 (useful for testing or billing cycles)."""
        user_id = str(user_id or "anonymous").strip()

        try:
            with self._get_connection() as conn:
                conn.execute(
                    "UPDATE user_quotas SET screenings_used = 0, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (user_id,),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to reset quota for user {user_id}: {e}")

        return self.get_user_quota(user_id)

    # -------------------------------------------------------------
    # API Key Management
    # -------------------------------------------------------------

    def create_api_key(self, user_id: str, name: str = "Default API Key") -> CreateApiKeyResponse:
        """Generate and store a new API key. Returns raw secret only once."""
        user_id = str(user_id or "anonymous").strip()
        name = (name or "Default API Key").strip()
        raw_secret = f"tl_test_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_secret.encode("utf-8")).hexdigest()
        key_id = f"key_{uuid.uuid4().hex[:12]}"
        key_prefix = f"{raw_secret[:12]}..."

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO api_keys (key_id, key_hash, key_prefix, user_id, name, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
                """,
                (key_id, key_hash, key_prefix, user_id, name),
            )
            row = conn.execute("SELECT created_at FROM api_keys WHERE key_id = ?", (key_id,)).fetchone()
            created_at = row["created_at"] if row else ""
            conn.commit()

        return CreateApiKeyResponse(
            key_id=key_id,
            key_prefix=key_prefix,
            name=name,
            api_key=raw_secret,
            created_at=str(created_at),
        )

    def list_api_keys(self, user_id: str) -> List[ApiKeyInfo]:
        """List all API keys belonging to a user (raw secret omitted)."""
        user_id = str(user_id or "anonymous").strip()
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT key_id, key_prefix, name, user_id, created_at, last_used_at, is_active
                FROM api_keys
                WHERE user_id = ? AND is_active = 1
                ORDER BY created_at DESC
                """,
                (user_id,),
            ).fetchall()

            return [
                ApiKeyInfo(
                    key_id=row["key_id"],
                    key_prefix=row["key_prefix"],
                    name=row["name"],
                    user_id=row["user_id"],
                    created_at=str(row["created_at"]),
                    last_used_at=str(row["last_used_at"]) if row["last_used_at"] else None,
                    is_active=bool(row["is_active"]),
                )
                for row in rows
            ]

    def delete_api_key(self, user_id: str, key_id: str) -> bool:
        """Permanently delete an API key."""
        user_id = str(user_id or "anonymous").strip()
        with self._get_connection() as conn:
            cur = conn.execute(
                "DELETE FROM api_keys WHERE user_id = ? AND key_id = ?",
                (user_id, key_id),
            )
            conn.commit()
            return cur.rowcount > 0

    def revoke_api_key(self, user_id: str, key_id: str) -> bool:
        """Alias to delete_api_key."""
        return self.delete_api_key(user_id, key_id)

    def verify_api_key(self, raw_secret: str) -> Optional[Dict[str, Any]]:
        """
        Verify raw API key token.
        If valid, updates last_used_at and returns user info + quota.
        """
        if not raw_secret or not raw_secret.strip():
            return None

        clean_token = raw_secret.strip()
        key_hash = hashlib.sha256(clean_token.encode("utf-8")).hexdigest()

        with self._get_connection() as conn:
            row = conn.execute(
                """
                SELECT key_id, user_id, name, is_active
                FROM api_keys
                WHERE key_hash = ?
                """,
                (key_hash,),
            ).fetchone()

            if not row or not bool(row["is_active"]):
                return None

            key_id = row["key_id"]
            user_id = row["user_id"]

            conn.execute(
                "UPDATE api_keys SET last_used_at = CURRENT_TIMESTAMP WHERE key_id = ?",
                (key_id,),
            )
            conn.commit()

        quota = self.get_user_quota(user_id)
        return {
            "user_id": user_id,
            "key_id": key_id,
            "tier": quota.tier,
            "quota": quota,
        }

    # -------------------------------------------------------------
    # Payments Management
    # -------------------------------------------------------------

    def record_payment_order(
        self,
        order_id: str,
        user_id: str,
        tier: PlanTier,
        amount: int,
        currency: str = "INR",
    ) -> None:
        """Record a newly created Razorpay order."""
        user_id = str(user_id or "anonymous").strip()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO payments (order_id, user_id, tier, amount, currency, status)
                VALUES (?, ?, ?, ?, ?, 'created')
                ON CONFLICT(order_id) DO NOTHING
                """,
                (order_id, user_id, tier.value, amount, currency),
            )
            conn.commit()

    def mark_payment_successful(
        self,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> Optional[UserQuota]:
        """Mark Razorpay payment verified and upgrade user quota idempotently."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT user_id, tier, status FROM payments WHERE order_id = ?",
                (order_id,),
            ).fetchone()

            if not row:
                return None

            user_id = row["user_id"]
            tier_str = row["tier"]
            status = row["status"] if "status" in row.keys() else ""

            # Idempotency check: if already paid, do not re-upgrade and wipe screenings_used
            if status == "paid":
                logger.info(f"Payment order {order_id} already marked as paid. Skipping duplicate tier reset.")
                return self.get_user_quota(user_id)

            conn.execute(
                """
                UPDATE payments
                SET status = 'paid', payment_id = ?, signature = ?, updated_at = CURRENT_TIMESTAMP
                WHERE order_id = ?
                """,
                (payment_id, signature, order_id),
            )
            conn.commit()

        try:
            tier = PlanTier(tier_str)
        except ValueError:
            tier = PlanTier.PRO_29

        return self.upgrade_user_tier(user_id, tier)

    # -------------------------------------------------------------------------
    # Previous Shortlistings & Screening History
    # -------------------------------------------------------------------------

    def save_screening_history(
        self,
        user_id: str,
        report: ScreeningReport,
        target_role: str = "Python Developer",
    ) -> str:
        """Save a completed candidate screening batch report to user's history."""
        user_id = str(user_id or "anonymous").strip()
        batch_id = f"batch_{uuid.uuid4().hex[:12]}"

        total_resumes = report.batch_summary.total_resumes
        eligible_count = report.batch_summary.eligible
        rejected_count = report.batch_summary.rejected
        avg_score = report.batch_summary.average_score_eligible
        top_score = (
            report.ranked_candidates[0].total_score
            if report.ranked_candidates
            else 0.0
        )
        report_json = report.model_dump_json()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO screening_history (
                    batch_id, user_id, target_role, total_resumes,
                    eligible_count, rejected_count, avg_score, top_score, report_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    batch_id,
                    user_id,
                    target_role or "Python Developer",
                    total_resumes,
                    eligible_count,
                    rejected_count,
                    avg_score,
                    top_score,
                    report_json,
                ),
            )
            conn.commit()

        logger.info(f"Saved screening history {batch_id} for user {user_id} with {total_resumes} resumes.")
        return batch_id

    def list_screening_history(self, user_id: str) -> List[ScreeningHistoryItem]:
        """List past shortlisting batches for the user (latest first)."""
        user_id = str(user_id or "anonymous").strip()
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT batch_id, user_id, target_role, total_resumes,
                       eligible_count, rejected_count, avg_score, top_score, created_at
                FROM screening_history
                WHERE user_id = ?
                ORDER BY created_at DESC
                """,
                (user_id,),
            ).fetchall()

            return [
                ScreeningHistoryItem(
                    batch_id=r["batch_id"],
                    user_id=r["user_id"],
                    target_role=r["target_role"],
                    total_resumes=r["total_resumes"],
                    eligible_count=r["eligible_count"],
                    rejected_count=r["rejected_count"],
                    avg_score=r["avg_score"],
                    top_score=r["top_score"],
                    created_at=str(r["created_at"]),
                )
                for r in rows
            ]

    def get_screening_history_item(self, user_id: str, batch_id: str) -> Optional[ScreeningReport]:
        """Fetch the full ScreeningReport of a specific previous shortlisting."""
        user_id = str(user_id or "anonymous").strip()
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT report_json FROM screening_history WHERE batch_id = ? AND user_id = ?",
                (batch_id, user_id),
            ).fetchone()

            if not row:
                return None

            try:
                data = json.loads(row["report_json"])
                return ScreeningReport(**data)
            except Exception as e:
                logger.error(f"Failed to deserialize screening history {batch_id}: {e}")
                return None

    def delete_screening_history_item(self, user_id: str, batch_id: str) -> bool:
        """Permanently delete a previous shortlisting record."""
        user_id = str(user_id or "anonymous").strip()
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM screening_history WHERE batch_id = ? AND user_id = ?",
                (batch_id, user_id),
            )
            conn.commit()
            return cursor.rowcount > 0


# Global singleton instance
quota_manager = QuotaManager()

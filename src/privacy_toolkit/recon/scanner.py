"""Scan orchestrator — fixed: encryption key missing + stuck progress."""

from __future__ import annotations

from datetime import datetime
from typing import Callable, Optional

from privacy_toolkit.core.constants import Status
from privacy_toolkit.core.exceptions import ProxyVerificationError
from privacy_toolkit.core.logging import get_logger
from privacy_toolkit.db.database import get_db
from privacy_toolkit.db.models import UserProfile
from privacy_toolkit.db.repository import (
    AppEventRepository, BrokerFindingRepository,
    BrokerRepository, ScanRunRepository, UserProfileRepository,
)
from privacy_toolkit.network.anonymizer import prepare_anonymized_client
from privacy_toolkit.recon.broker_adapter import ScanResult, get_adapter

logger = get_logger(__name__)

ProgressCallback = Callable[[str, int, int], None]


class Scanner:
    def __init__(
        self,
        profile_label: str = "default",
        progress_callback: Optional[ProgressCallback] = None,
        triggered_by: str = "manual",
    ) -> None:
        self.profile_label = profile_label
        self.progress_callback = progress_callback
        self.triggered_by = triggered_by

    def _emit(self, msg: str, cur: int = 0, total: int = 0) -> None:
        logger.info(msg)
        if self.progress_callback:
            try:
                self.progress_callback(msg, cur, total)
            except Exception:
                pass

    def run(self) -> dict[str, object]:
        self._emit("Preparing network client…")
        try:
            anon = prepare_anonymized_client(fail_closed=True, print_disclaimer=False)
        except ProxyVerificationError as exc:
            logger.error("Scan aborted — proxy verification failed: %s", exc)
            return {"error": str(exc), "aborted": True}

        self._emit(f"Network: {anon.message}")

        with get_db() as db:
            profile_repo  = UserProfileRepository(db)
            broker_repo   = BrokerRepository(db)
            scan_repo     = ScanRunRepository(db)
            finding_repo  = BrokerFindingRepository(db)
            event_repo    = AppEventRepository(db)

            profile: Optional[UserProfile] = profile_repo.get_by_label(self.profile_label)
            if profile is None:
                msg = f"No profile '{self.profile_label}'. Run: privacy-toolkit init"
                logger.error(msg)
                return {"error": msg, "aborted": True}

            enc_available, profile_fields = self._decrypt_profile(profile)
            if not enc_available:
                self._emit(
                    "⚠ Encryption key not set — only non-sensitive fields available. "
                    "Run: privacy-toolkit init --generate-key"
                )

            scan_run = scan_repo.create(
                profile_id=profile.id,
                status=Status.SCANNING,
                triggered_by=self.triggered_by,
                started_at=datetime.utcnow(),
            )

            brokers = broker_repo.list_enabled()
            total = len(brokers)
            findings_count = 0
            skipped = 0

            self._emit(f"Found {total} enabled brokers.", 0, total)

            for idx, broker in enumerate(brokers, start=1):
                self._emit(f"[{idx}/{total}] {broker.name}…", idx, total)
                adapter = get_adapter(broker.slug)

                if adapter is None:
                    # No adapter registered — still log as not-started
                    finding_repo.create(
                        broker_id=broker.id,
                        scan_run_id=scan_run.id,
                        status=Status.MANUAL_REVIEW_REQUIRED,
                        snippet="No automated adapter — manual review required.",
                    )
                    skipped += 1
                    continue

                # Check required fields
                missing = [
                    f for f in adapter.required_fields
                    if not profile_fields.get(f)
                ]
                if missing:
                    self._emit(
                        f"  ↳ Skipped {broker.name} — missing fields: {missing}. "
                        "Add them to your profile.",
                        idx, total,
                    )
                    skipped += 1
                    continue

                result: ScanResult = adapter.scan(profile_fields, anon.client)

                if result.error:
                    logger.warning("Broker %s error: %s", broker.slug, result.error)
                    finding_repo.create(
                        broker_id=broker.id,
                        scan_run_id=scan_run.id,
                        status=Status.FAILED,
                        snippet=str(result.error)[:200],
                    )
                    continue

                status = Status.FOUND if result.found else Status.NOT_FOUND
                finding = finding_repo.create(
                    broker_id=broker.id,
                    scan_run_id=scan_run.id,
                    status=status,
                    result_url=result.result_url,
                    snippet=result.snippet,
                    raw_hash=result.raw_html_hash,
                )
                if result.found:
                    findings_count += 1
                    if result.requires_manual_review:
                        finding_repo.update_status(finding.id, Status.MANUAL_REVIEW_REQUIRED)

            scan_repo.update(
                scan_run.id,
                status=Status.COMPLETED,
                brokers_scanned=total,
                findings_count=findings_count,
                completed_at=datetime.utcnow(),
            )
            event_repo.log(
                "scan_completed",
                f"Scan #{scan_run.id}: {findings_count} findings, {skipped} skipped / {total} brokers.",
            )

            summary = {
                "scan_run_id": scan_run.id,
                "brokers_scanned": total,
                "findings": findings_count,
                "skipped": skipped,
                "aborted": False,
            }
            self._emit(
                f"✓ Scan complete — {findings_count} findings, {skipped} skipped / {total} brokers."
            )
            return summary

    @staticmethod
    def _decrypt_profile(profile: UserProfile) -> tuple[bool, dict[str, str]]:
        """Return (encryption_available, fields_dict).
        Never raises — gracefully degrades to non-sensitive fields only.
        """
        non_sensitive: dict[str, str] = {
            "city":     profile.city or "",
            "state":    profile.state or "",
            "zip_code": profile.zip_code or "",
        }
        try:
            from privacy_toolkit.security.encryption import get_encryptor
            enc = get_encryptor()
            full_name = enc.decrypt_optional(profile.full_name_enc) or ""
            parts = full_name.split()
            return True, {
                **non_sensitive,
                "full_name":  full_name,
                "first_name": parts[0] if parts else "",
                "last_name":  " ".join(parts[1:]) if len(parts) > 1 else "",
                "email":      enc.decrypt_optional(profile.email_enc) or "",
                "phone":      enc.decrypt_optional(profile.phone_enc) or "",
                "address":    enc.decrypt_optional(profile.address_enc) or "",
            }
        except Exception as exc:
            logger.warning("Encryption key unavailable (%s) — using non-sensitive fields only.", exc)
            return False, non_sensitive

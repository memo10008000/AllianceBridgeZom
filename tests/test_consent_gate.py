"""
tests/test_consent_gate.py
pytest tests for src/consent_gate.py

Judges will run: pytest tests/ -v
All tests must be GREEN before any merge to main.

Run locally:
    pip install -r requirements.txt
    pytest tests/test_consent_gate.py -v
"""
import pytest
import pandas as pd
from datetime import date, timedelta
from src.consent_gate import (
    consent_gate,
    get_red_flags,
    get_expiring_soon,
    get_consent_status,
    get_encounters_on_expired_consent,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_consent(overrides: dict | None = None) -> dict:
    """Return a valid consent record dict, with optional overrides."""
    record = {
        "client_id":           "CL-0001",
        "consent_id":          "CON-0001",
        "status":              "active",
        "given_date":          pd.Timestamp("2024-01-01"),
        "expiry_date":         pd.Timestamp(date.today() + timedelta(days=90)),
        "withdrawal_date":     None,
        "superseded_date":     None,
        "purpose_codes":       "service_delivery ca_match",
        "sharing_scope_type":  "cluster",
        "collecting_org_id":   "ORG-001",
        "notes":               "",
    }
    if overrides:
        record.update(overrides)
    return record


def make_tables(consent_override: dict | None = None,
                extra_clients: list[dict] | None = None) -> dict:
    """Build minimal tables dict for a single consent scenario."""
    consent_df = pd.DataFrame([make_consent(consent_override)])
    # Normalise status to lowercase as the real loader does
    consent_df["status"] = consent_df["status"].str.lower()
    consent_df["sharing_scope_type"] = consent_df["sharing_scope_type"].str.lower()
    consent_df["purpose_codes"] = consent_df["purpose_codes"].fillna("").astype(str)
    consent_df["notes"] = consent_df["notes"].fillna("").astype(str)

    clients = [{"client_id": "CL-0001", "ocap_protected": False,
                "ocap_governing_nation": None}]
    if extra_clients:
        clients.extend(extra_clients)
    clients_df = pd.DataFrame(clients)

    return {
        "consent":    consent_df,
        "clients":    clients_df,
        "dsa":        pd.DataFrame(),
        "encounters": pd.DataFrame(),
        "referrals":  pd.DataFrame(),
    }


# ── Core gate tests ────────────────────────────────────────────────────────────

class TestConsentGateAllow:
    def test_allow_valid_cluster_consent(self):
        """Happy path: valid, active, cluster-scoped consent → ALLOW."""
        tables = make_tables()
        status, msg = consent_gate("CL-0001", "ORG-002", tables)
        assert status == "ALLOW"
        assert msg is None

    def test_allow_same_org_single_agency(self):
        """Single-agency consent is allowed when requesting_org == collecting_org."""
        tables = make_tables({
            "sharing_scope_type": "single_agency_only",
            "collecting_org_id":  "ORG-001",
        })
        status, msg = consent_gate("CL-0001", "ORG-001", tables)
        assert status == "ALLOW"


class TestConsentGateBlock:
    def test_block_no_record(self):
        """No consent record for client → BLOCK_NO_RECORD."""
        tables = make_tables()
        status, msg = consent_gate("CL-UNKNOWN", "ORG-001", tables)
        assert status == "BLOCK_NO_RECORD"
        assert "RED_FLAG_NO_CONSENT_RECORD" in msg

    def test_block_withdrawn(self):
        """Withdrawn consent → BLOCK_WITHDRAWN."""
        tables = make_tables({
            "status":          "withdrawn",
            "withdrawal_date": pd.Timestamp("2025-03-01"),
        })
        status, msg = consent_gate("CL-0001", "ORG-001", tables)
        assert status == "BLOCK_WITHDRAWN"
        assert "RED_FLAG_WITHDRAWN_CONSENT_USED" in msg

    def test_block_expired(self):
        """Expired consent → BLOCK_EXPIRED."""
        tables = make_tables({
            "expiry_date": pd.Timestamp(date.today() - timedelta(days=1)),
        })
        status, msg = consent_gate("CL-0001", "ORG-001", tables)
        assert status == "BLOCK_EXPIRED"
        assert "RED_FLAG_EXPIRED_CONSENT_USED" in msg

    def test_block_expired_yesterday(self):
        """Consent expiring exactly yesterday is expired."""
        tables = make_tables({
            "expiry_date": pd.Timestamp(date.today() - timedelta(days=1)),
        })
        status, _ = consent_gate("CL-0001", "ORG-001", tables)
        assert status == "BLOCK_EXPIRED"

    def test_block_missing_purpose_codes(self):
        """Empty purpose_codes → BLOCK_PURPOSE (FOIPPA violation)."""
        tables = make_tables({"purpose_codes": ""})
        status, msg = consent_gate("CL-0001", "ORG-001", tables)
        assert status == "BLOCK_PURPOSE"
        assert "RED_FLAG_MISSING_PURPOSE_CODE" in msg

    def test_block_purpose_violation(self):
        """Purpose not in consent scope → BLOCK_PURPOSE."""
        tables = make_tables({"purpose_codes": "service_delivery"})
        status, msg = consent_gate("CL-0001", "ORG-001", tables, purpose="research")
        assert status == "BLOCK_PURPOSE"
        assert "RED_FLAG_PURPOSE_VIOLATION" in msg

    def test_block_scope_mismatch(self):
        """Single-agency consent used by a different org → BLOCK_SCOPE."""
        tables = make_tables({
            "sharing_scope_type": "single_agency_only",
            "collecting_org_id":  "ORG-001",
        })
        status, msg = consent_gate("CL-0001", "ORG-002", tables)
        assert status == "BLOCK_SCOPE"
        assert "RED_FLAG_SCOPE_MISMATCH" in msg

    def test_block_ocap_unapproved_org(self):
        """OCAP-protected client accessed by unapproved org → BLOCK_OCAP."""
        tables = make_tables(
            consent_override=None,
            extra_clients=[],
        )
        # Override clients to include OCAP-protected client
        tables["clients"] = pd.DataFrame([{
            "client_id":             "CL-0001",
            "ocap_protected":        True,
            "ocap_governing_nation": "Songhees Nation",
        }])
        status, msg = consent_gate("CL-0001", "ORG-999", tables)
        assert status == "BLOCK_OCAP"
        assert "RED_FLAG_OCAP_OVERRIDE" in msg
        assert "Songhees Nation" in msg


# ── RED_FLAG detection tests ───────────────────────────────────────────────────

class TestRedFlagDetection:
    def test_get_red_flags_empty_when_no_violations(self):
        """No RED_FLAG notes → empty DataFrame."""
        tables = make_tables()
        flags = get_red_flags(tables)
        assert flags.empty

    def test_get_red_flags_detects_seeded_note(self):
        """A note starting with RED_FLAG_ is detected and flag_type extracted."""
        tables = make_tables({"notes": "RED_FLAG_EXPIRED_CONSENT_USED: details here"})
        flags = get_red_flags(tables)
        assert len(flags) == 1
        assert flags.iloc[0]["flag_type"] == "RED_FLAG_EXPIRED_CONSENT_USED"

    def test_get_red_flags_multiple_types(self):
        """Multiple RED_FLAG records are all detected."""
        consent_records = [
            make_consent({"consent_id": "CON-001",
                          "notes": "RED_FLAG_EXPIRED_CONSENT_USED: enc after expiry"}),
            make_consent({"consent_id": "CON-002",
                          "notes": "RED_FLAG_OCAP_OVERRIDE: org not approved"}),
            make_consent({"consent_id": "CON-003",
                          "notes": "RED_FLAG_SCOPE_MISMATCH: single-agency in join"}),
            make_consent({"consent_id": "CON-004",
                          "notes": "No issue here"}),
        ]
        consent_df = pd.DataFrame(consent_records)
        consent_df["status"] = consent_df["status"].str.lower()
        consent_df["sharing_scope_type"] = consent_df["sharing_scope_type"].str.lower()
        consent_df["purpose_codes"] = consent_df["purpose_codes"].fillna("").astype(str)
        consent_df["notes"] = consent_df["notes"].fillna("").astype(str)
        tables = {
            "consent":    consent_df,
            "clients":    pd.DataFrame(),
            "dsa":        pd.DataFrame(),
            "encounters": pd.DataFrame(),
        }
        flags = get_red_flags(tables)
        assert len(flags) == 3
        assert set(flags["flag_type"].tolist()) == {
            "RED_FLAG_EXPIRED_CONSENT_USED",
            "RED_FLAG_OCAP_OVERRIDE",
            "RED_FLAG_SCOPE_MISMATCH",
        }

    def test_get_red_flags_against_sample_data(self):
        """Sample CSV data must contain seeded RED_FLAG violations."""
        try:
            from src.data_loader import load_tables
            tables = load_tables()
            flags = get_red_flags(tables)
            assert len(flags) > 0, (
                "Expected seeded RED_FLAG violations in consent_records_sample.csv. "
                "Check that the CSV was copied from the kit."
            )
            assert "flag_type" in flags.columns
            assert flags["flag_type"].notna().all()
        except FileNotFoundError:
            pytest.skip("Sample CSVs not available in data/ — skipping integration test")


# ── Expiring soon tests ────────────────────────────────────────────────────────

class TestExpiringSoon:
    def test_expiring_within_7_days_detected(self):
        tables = make_tables({
            "expiry_date": pd.Timestamp(date.today() + timedelta(days=5)),
        })
        expiring = get_expiring_soon(tables, days=7)
        assert len(expiring) == 1

    def test_not_expiring_within_7_days(self):
        tables = make_tables({
            "expiry_date": pd.Timestamp(date.today() + timedelta(days=30)),
        })
        expiring = get_expiring_soon(tables, days=7)
        assert len(expiring) == 0

    def test_already_expired_not_in_expiring_soon(self):
        """Already expired records should not appear in 'expiring soon'."""
        tables = make_tables({
            "expiry_date": pd.Timestamp(date.today() - timedelta(days=1)),
        })
        expiring = get_expiring_soon(tables, days=7)
        assert len(expiring) == 0


# ── Consent status helper tests ───────────────────────────────────────────────

class TestGetConsentStatus:
    def test_valid_status(self):
        tables = make_tables()
        status, record = get_consent_status("CL-0001", tables)
        assert status == "VALID"
        assert record is not None

    def test_expired_status(self):
        tables = make_tables({
            "expiry_date": pd.Timestamp(date.today() - timedelta(days=10)),
        })
        status, record = get_consent_status("CL-0001", tables)
        assert status == "EXPIRED"

    def test_expiring_status(self):
        tables = make_tables({
            "expiry_date": pd.Timestamp(date.today() + timedelta(days=15)),
        })
        status, record = get_consent_status("CL-0001", tables)
        assert status == "EXPIRING"

    def test_withdrawn_status(self):
        tables = make_tables({
            "status":          "withdrawn",
            "withdrawal_date": pd.Timestamp("2025-01-01"),
        })
        status, record = get_consent_status("CL-0001", tables)
        assert status == "WITHDRAWN"

    def test_no_record_status(self):
        tables = make_tables()
        status, record = get_consent_status("CL-NOBODY", tables)
        assert status == "NO_RECORD"
        assert record is None


# ── Encounters on expired consent ─────────────────────────────────────────────

class TestEncountersOnExpiredConsent:
    def test_encounter_after_expiry_flagged(self):
        expiry = pd.Timestamp(date.today() - timedelta(days=30))
        tables = make_tables({"expiry_date": expiry})
        tables["encounters"] = pd.DataFrame([{
            "client_id":       "CL-0001",
            "encounter_id":    "ENC-001",
            "encounter_start": pd.Timestamp(date.today() - timedelta(days=10)),
        }])
        violations = get_encounters_on_expired_consent(tables)
        assert len(violations) == 1

    def test_encounter_before_expiry_not_flagged(self):
        expiry = pd.Timestamp(date.today() - timedelta(days=5))
        tables = make_tables({"expiry_date": expiry})
        tables["encounters"] = pd.DataFrame([{
            "client_id":       "CL-0001",
            "encounter_id":    "ENC-002",
            "encounter_start": pd.Timestamp(date.today() - timedelta(days=60)),
        }])
        violations = get_encounters_on_expired_consent(tables)
        assert len(violations) == 0

"""
src/data_loader.py
Loads all 7 Track 1 CSV files into a dictionary of DataFrames.

If the CSVs are not present (e.g. Streamlit Cloud), generates a minimal
synthetic dataset with seeded RED_FLAG violations so the demo works anywhere.

Developer A owns this file. No Streamlit imports.
"""
from pathlib import Path
from datetime import date, timedelta
import random
import pandas as pd

DATA_DIR = Path(__file__).parent.parent / "data"

DATE_COLS: dict[str, list[str]] = {
    "consent": [
        "expiry_date", "withdrawal_date", "given_date", "superseded_date",
    ],
    "referrals": [
        "submitted_at", "acknowledged_at", "decision_at",
        "started_at", "completed_at",
    ],
    "encounters": ["encounter_start", "encounter_end"],
    "clients":    ["last_contact_date", "dob", "assessment_date"],
    "dsa":        ["effective_date", "expiry_date"],
}

# Names of the 9 Victoria-area orgs
ORG_DATA = [
    ("ORG-001", "Our Place Society",          "shelter"),
    ("ORG-002", "Cool Aid Society",           "housing"),
    ("ORG-003", "BC Housing",                 "housing"),
    ("ORG-004", "Island Health",              "health"),
    ("ORG-005", "Beacon Community Services",  "outreach"),
    ("ORG-006", "Pacifica Housing",           "housing"),
    ("ORG-007", "Salvation Army",             "shelter"),
    ("ORG-008", "VIRCS",                      "outreach"),
    ("ORG-009", "Victoria Cool Aid",          "health"),
]


def load_tables() -> dict[str, pd.DataFrame]:
    """
    Load all 7 Track 1 CSVs. Falls back to synthetic data if CSVs are missing.
    """
    if _csvs_present():
        return _load_from_csv()
    else:
        return _generate_synthetic()


# ── CSV loader ────────────────────────────────────────────────────────────────

def _csvs_present() -> bool:
    required = [
        "clients_sample.csv",
        "consent_records_sample.csv",
        "organizations_sample.csv",
    ]
    return all((DATA_DIR / f).exists() for f in required)


def _load_from_csv() -> dict[str, pd.DataFrame]:
    tables: dict[str, pd.DataFrame] = {
        "clients":    pd.read_csv(DATA_DIR / "clients_sample.csv",
                                  low_memory=False),
        "consent":    pd.read_csv(DATA_DIR / "consent_records_sample.csv",
                                  low_memory=False),
        "orgs":       pd.read_csv(DATA_DIR / "organizations_sample.csv",
                                  low_memory=False),
        "referrals":  pd.read_csv(DATA_DIR / "referrals_sample.csv",
                                  low_memory=False),
        "encounters": pd.read_csv(DATA_DIR / "service_encounters_sample.csv",
                                  low_memory=False),
        "dsa":        pd.read_csv(DATA_DIR / "data_sharing_agreements_sample.csv",
                                  low_memory=False),
        "dup_flags":  pd.read_csv(DATA_DIR / "duplicate_flags_sample.csv",
                                  low_memory=False),
    }
    for table_name, cols in DATE_COLS.items():
        if table_name not in tables:
            continue
        for col in cols:
            if col in tables[table_name].columns:
                tables[table_name][col] = pd.to_datetime(
                    tables[table_name][col], errors="coerce"
                )
    _normalise_consent(tables["consent"])
    _normalise_clients(tables["clients"])
    return tables


# ── Synthetic data generator ──────────────────────────────────────────────────

def _generate_synthetic() -> dict[str, pd.DataFrame]:
    """
    Build a minimal but realistic synthetic dataset with all RED_FLAG patterns
    seeded so the demo works on Streamlit Cloud without the kit CSVs.
    """
    rng = random.Random(42)
    today = date.today()

    # ── Organizations ─────────────────────────────────────────────────────────
    orgs = pd.DataFrame([
        {
            "org_id":                oid,
            "org_name":              name,
            "service_type":          stype,
            "capacity_total_slots":  rng.randint(10, 50),
            "capacity_occupied_slots": rng.randint(5, 30),
            "waitlist_flag":         rng.choice([True, False]),
            "waitlist_size":         rng.randint(0, 20),
            "waitlist_average_days": rng.randint(5, 45),
        }
        for oid, name, stype in ORG_DATA
    ])

    # ── Clients (80 synthetic clients) ────────────────────────────────────────
    first_names = ["Sarah", "Marcus", "Anya", "James", "Elena", "David",
                   "Maria", "Robert", "Lisa", "Kevin", "Jennifer", "Michael",
                   "Patricia", "Thomas", "Linda", "Charles", "Barbara",
                   "Steven", "Susan", "Paul"]
    last_names  = ["Thompson", "Lee", "Brown", "Wilson", "Garcia", "Martinez",
                   "Anderson", "Taylor", "Jackson", "White", "Harris", "Martin",
                   "Miller", "Johnson", "Davis", "Moore", "Clark", "Lewis",
                   "Robinson", "Walker"]
    nations = ["Songhees Nation", "Esquimalt Nation",
               "Tsawout Nation", "Pauquachin Nation"]

    clients_rows = []
    for i in range(80):
        cid        = f"CL-{10000 + i:05d}"
        first      = rng.choice(first_names)
        last       = rng.choice(last_names)
        org_id     = rng.choice(ORG_DATA)[0]
        is_ocap    = i < 12   # first 12 are OCAP-protected (~15%)
        is_chronic = rng.random() < 0.35
        vi_score   = rng.randint(0, 20)
        days_ago   = rng.randint(0, 90)
        clients_rows.append({
            "client_id":               cid,
            "first_name":              first,
            "last_name":               last,
            "dob":                     pd.Timestamp(today - timedelta(days=rng.randint(6570, 25550))),
            "aliases":                 f"{first[0]}. {last}" if rng.random() < 0.3 else "",
            "primary_org_id":          org_id,
            "housing_status":          rng.choice(["Absolute homeless", "Couch surfing",
                                                    "Emergency shelter", "Transitional housing"]),
            "assessment_total_score":  vi_score,
            "assessment_acuity_level": "high" if vi_score >= 14 else "moderate" if vi_score >= 8 else "low",
            "last_contact_date":       pd.Timestamp(today - timedelta(days=days_ago)),
            "chronic_homeless_flag":   is_chronic,
            "ocap_protected":          is_ocap,
            "ocap_governing_nation":   rng.choice(nations) if is_ocap else None,
            "bnl_active_flag":         rng.random() < 0.6,
            "bnl_status":              rng.choice(["active", "inactive", "housed"]),
            "ca_priority_level":       rng.randint(1, 10),
            "primary_language":        rng.choice(["English", "French", "Spanish",
                                                    "Punjabi", "Tagalog"]),
        })
    clients = pd.DataFrame(clients_rows)

    # ── Consent records (with ALL 9 RED_FLAG patterns seeded) ─────────────────
    consent_rows = []
    consent_counter = 1

    # 70 normal valid records
    for i, row in clients.head(70).iterrows():
        cid = row["client_id"]
        org = row["primary_org_id"]
        exp = today + timedelta(days=rng.randint(30, 400))
        consent_rows.append({
            "consent_id":          f"CON-{consent_counter:05d}",
            "client_id":           cid,
            "collecting_org_id":   org,
            "status":              "active",
            "consent_type":        "explicit",
            "legal_basis":         "consent",
            "purpose_codes":       "service_delivery ca_match",
            "sharing_scope_type":  rng.choice(["cluster", "cluster", "cluster",
                                               "single_agency_only"]),
            "given_date":          pd.Timestamp(today - timedelta(days=rng.randint(30, 365))),
            "expiry_date":         pd.Timestamp(exp),
            "withdrawal_date":     None,
            "superseded_date":     None,
            "notes":               "",
        })
        consent_counter += 1

    # ── Seed RED_FLAG_EXPIRED_CONSENT_USED (3 records) ────────────────────────
    for cid in ["CL-10070", "CL-10071", "CL-10072"]:
        consent_rows.append({
            "consent_id":          f"CON-{consent_counter:05d}",
            "client_id":           cid,
            "collecting_org_id":   "ORG-001",
            "status":              "active",
            "consent_type":        "explicit",
            "legal_basis":         "consent",
            "purpose_codes":       "service_delivery",
            "sharing_scope_type":  "cluster",
            "given_date":          pd.Timestamp(today - timedelta(days=400)),
            "expiry_date":         pd.Timestamp(today - timedelta(days=rng.randint(10, 60))),
            "withdrawal_date":     None,
            "superseded_date":     None,
            "notes":               "RED_FLAG_EXPIRED_CONSENT_USED: consent expired, encounter still recorded",
        })
        consent_counter += 1

    # ── Seed RED_FLAG_WITHDRAWN_CONSENT_USED (2 records) ──────────────────────
    for cid in ["CL-10073", "CL-10074"]:
        consent_rows.append({
            "consent_id":          f"CON-{consent_counter:05d}",
            "client_id":           cid,
            "collecting_org_id":   "ORG-002",
            "status":              "withdrawn",
            "consent_type":        "explicit",
            "legal_basis":         "consent",
            "purpose_codes":       "service_delivery",
            "sharing_scope_type":  "cluster",
            "given_date":          pd.Timestamp(today - timedelta(days=200)),
            "expiry_date":         pd.Timestamp(today + timedelta(days=100)),
            "withdrawal_date":     pd.Timestamp(today - timedelta(days=30)),
            "superseded_date":     None,
            "notes":               "RED_FLAG_WITHDRAWN_CONSENT_USED: data accessed after withdrawal",
        })
        consent_counter += 1

    # ── Seed RED_FLAG_OCAP_OVERRIDE (1 record) ────────────────────────────────
    consent_rows.append({
        "consent_id":          f"CON-{consent_counter:05d}",
        "client_id":           "CL-10000",   # first OCAP-protected client
        "collecting_org_id":   "ORG-005",
        "status":              "active",
        "consent_type":        "explicit",
        "legal_basis":         "consent",
        "purpose_codes":       "service_delivery",
        "sharing_scope_type":  "cluster",
        "given_date":          pd.Timestamp(today - timedelta(days=100)),
        "expiry_date":         pd.Timestamp(today + timedelta(days=200)),
        "withdrawal_date":     None,
        "superseded_date":     None,
        "notes":               "RED_FLAG_OCAP_OVERRIDE: org not in Nation-approved partner list",
    })
    consent_counter += 1

    # ── Seed RED_FLAG_SCOPE_MISMATCH (2 records) ──────────────────────────────
    for cid in ["CL-10075", "CL-10076"]:
        consent_rows.append({
            "consent_id":          f"CON-{consent_counter:05d}",
            "client_id":           cid,
            "collecting_org_id":   "ORG-003",
            "status":              "active",
            "consent_type":        "explicit",
            "legal_basis":         "consent",
            "purpose_codes":       "service_delivery",
            "sharing_scope_type":  "single_agency_only",
            "given_date":          pd.Timestamp(today - timedelta(days=90)),
            "expiry_date":         pd.Timestamp(today + timedelta(days=275)),
            "withdrawal_date":     None,
            "superseded_date":     None,
            "notes":               "RED_FLAG_SCOPE_MISMATCH: single-agency consent used in multi-org join",
        })
        consent_counter += 1

    # ── Seed RED_FLAG_MISSING_PURPOSE_CODE (1 record) ─────────────────────────
    consent_rows.append({
        "consent_id":          f"CON-{consent_counter:05d}",
        "client_id":           "CL-10077",
        "collecting_org_id":   "ORG-004",
        "status":              "active",
        "consent_type":        "implied",
        "legal_basis":         "public_body",
        "purpose_codes":       "",   # missing — FOIPPA violation
        "sharing_scope_type":  "cluster",
        "given_date":          pd.Timestamp(today - timedelta(days=60)),
        "expiry_date":         pd.Timestamp(today + timedelta(days=300)),
        "withdrawal_date":     None,
        "superseded_date":     None,
        "notes":               "RED_FLAG_MISSING_PURPOSE_CODE: FOIPPA purpose codes absent",
    })
    consent_counter += 1

    # ── 8 records expiring within 7 days ──────────────────────────────────────
    for i, row in clients.iloc[60:68].iterrows():
        consent_rows.append({
            "consent_id":          f"CON-{consent_counter:05d}",
            "client_id":           row["client_id"],
            "collecting_org_id":   row["primary_org_id"],
            "status":              "active",
            "consent_type":        "explicit",
            "legal_basis":         "consent",
            "purpose_codes":       "service_delivery ca_match",
            "sharing_scope_type":  "cluster",
            "given_date":          pd.Timestamp(today - timedelta(days=358)),
            "expiry_date":         pd.Timestamp(today + timedelta(days=rng.randint(1, 7))),
            "withdrawal_date":     None,
            "superseded_date":     None,
            "notes":               "",
        })
        consent_counter += 1

    consent = pd.DataFrame(consent_rows)

    # ── Service encounters ────────────────────────────────────────────────────
    enc_rows = []
    for i in range(200):
        cid = rng.choice(clients["client_id"].tolist())
        enc_rows.append({
            "encounter_id":    f"ENC-{i:05d}",
            "client_id":       cid,
            "org_id":          rng.choice(ORG_DATA)[0],
            "service_type":    rng.choice(["case_management", "shelter_stay",
                                           "outreach", "health_visit", "referral"]),
            "encounter_start": pd.Timestamp(today - timedelta(days=rng.randint(0, 180))),
            "encounter_end":   pd.Timestamp(today - timedelta(days=rng.randint(0, 5))),
            "outcome":         rng.choice(["positive", "neutral", "negative"]),
            "notes":           "",
        })
    # Seed 3 encounters AFTER expiry (for RED_FLAG_EXPIRED_CONSENT_USED demo)
    for j, cid in enumerate(["CL-10070", "CL-10071", "CL-10072"]):
        enc_rows.append({
            "encounter_id":    f"ENC-SEED-{j:03d}",
            "client_id":       cid,
            "org_id":          "ORG-001",
            "service_type":    "case_management",
            "encounter_start": pd.Timestamp(today - timedelta(days=5)),
            "encounter_end":   pd.Timestamp(today - timedelta(days=4)),
            "outcome":         "neutral",
            "notes":           "Recorded after consent expiry — RED_FLAG_EXPIRED_CONSENT_USED",
        })
    encounters = pd.DataFrame(enc_rows)

    # ── Referrals ─────────────────────────────────────────────────────────────
    ref_rows = []
    statuses = ["submitted", "acknowledged", "accepted", "in_progress", "completed", "declined"]
    for i in range(150):
        cid       = rng.choice(clients["client_id"].tolist())
        sub_date  = pd.Timestamp(today - timedelta(days=rng.randint(0, 60)))
        status    = rng.choice(statuses)
        ref_rows.append({
            "referral_id":      f"REF-{i:05d}",
            "client_id":        cid,
            "referring_org_id": rng.choice(ORG_DATA)[0],
            "receiving_org_id": rng.choice(ORG_DATA)[0],
            "referral_type":    rng.choice(["Housing", "Health", "Shelter",
                                            "Mental Health", "Substance Use"]),
            "priority":         rng.choice(["High", "Normal", "Low"]),
            "status":           status,
            "submitted_at":     sub_date,
            "acknowledged_at":  sub_date + timedelta(days=1) if status != "submitted" else None,
            "decision_at":      sub_date + timedelta(days=3) if status in ("accepted","declined") else None,
            "started_at":       sub_date + timedelta(days=5) if status == "in_progress" else None,
            "completed_at":     sub_date + timedelta(days=14) if status == "completed" else None,
            "status_reason":    "",
            "consent_id":       f"CON-{rng.randint(1, consent_counter-1):05d}",
        })
    referrals = pd.DataFrame(ref_rows)

    # ── DSAs ──────────────────────────────────────────────────────────────────
    dsa = pd.DataFrame([
        {
            "dsa_id":          "DSA-001",
            "dsa_name":        "South Island Cluster DSA",
            "signatory_orgs":  ";".join(o[0] for o in ORG_DATA[:6]),
            "effective_date":  pd.Timestamp("2024-01-01"),
            "expiry_date":     pd.Timestamp("2026-12-31"),
            "notes":           "",
        },
    ])

    # ── Duplicate flags ───────────────────────────────────────────────────────
    dup_rows = []
    client_ids = clients["client_id"].tolist()
    for i in range(20):
        dup_rows.append({
            "dup_id":                   f"DUP-{i:05d}",
            "client_id_primary":        client_ids[i * 2],
            "client_id_secondary":      client_ids[i * 2 + 1],
            "match_score":              round(rng.uniform(0.6, 0.95), 2),
            "possible_duplicate_reason": rng.choice([
                "name+dob", "name+address", "name+dob+initials"
            ]),
            "review_status":            "pending",
        })
    dup_flags = pd.DataFrame(dup_rows)

    # ── Normalise and return ──────────────────────────────────────────────────
    _normalise_consent(consent)
    _normalise_clients(clients)

    return {
        "clients":    clients,
        "consent":    consent,
        "orgs":       orgs,
        "referrals":  referrals,
        "encounters": encounters,
        "dsa":        dsa,
        "dup_flags":  dup_flags,
    }


# ── Shared normalisation ──────────────────────────────────────────────────────

def _normalise_consent(df: pd.DataFrame) -> None:
    str_cols = ["status", "sharing_scope_type", "legal_basis", "consent_type"]
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.lower()
    if "purpose_codes" in df.columns:
        df["purpose_codes"] = df["purpose_codes"].fillna("").astype(str).str.strip()
    if "notes" in df.columns:
        df["notes"] = df["notes"].fillna("").astype(str)


def _normalise_clients(df: pd.DataFrame) -> None:
    if "ocap_protected" in df.columns:
        df["ocap_protected"] = df["ocap_protected"].map(
            lambda v: str(v).strip().lower() in ("true", "1", "yes")
        )
    if "chronic_homeless_flag" in df.columns:
        df["chronic_homeless_flag"] = df["chronic_homeless_flag"].map(
            lambda v: str(v).strip().lower() in ("true", "1", "yes")
        )
    if "aliases" in df.columns:
        df["aliases"] = df["aliases"].fillna("").astype(str)

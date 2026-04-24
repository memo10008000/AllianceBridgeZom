"""
src/data_loader.py
Loads all 7 Track 1 CSV files into a dictionary of DataFrames.
All date columns are parsed at load time — never call pd.to_datetime() in pages.

Developer A owns this file. No Streamlit imports.
"""
from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).parent.parent / "data"

# Every date column in every table, parsed once at load time
DATE_COLS: dict[str, list[str]] = {
    "consent": [
        "expiry_date",
        "withdrawal_date",
        "given_date",
        "superseded_date",
    ],
    "referrals": [
        "submitted_at",
        "acknowledged_at",
        "decision_at",
        "started_at",
        "completed_at",
    ],
    "encounters": [
        "encounter_start",
        "encounter_end",
    ],
    "clients": [
        "last_contact_date",
        "dob",
        "assessment_date",
    ],
    "dsa": [
        "effective_date",
        "expiry_date",
    ],
}


def load_tables() -> dict[str, pd.DataFrame]:
    """
    Load all 7 Track 1 sample CSVs into a dictionary of DataFrames.

    Returns:
        dict with keys:
            'clients'    — 800 rows, 57 fields
            'consent'    — 5,000 rows, 22 fields
            'orgs'       — 9 rows, 18 fields
            'referrals'  — 3,000 rows, 21 fields
            'encounters' — 10,000 rows, 15 fields
            'dsa'        — small, all DSAs
            'dup_flags'  — 500 rows (300 TP + 200 FP)

    Raises:
        FileNotFoundError if any CSV is missing from data/
    """
    _check_data_dir()

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

    # Parse date columns — coerce bad values to NaT (never crash on dirty data)
    for table_name, cols in DATE_COLS.items():
        if table_name not in tables:
            continue
        for col in cols:
            if col in tables[table_name].columns:
                tables[table_name][col] = pd.to_datetime(
                    tables[table_name][col], errors="coerce"
                )

    # Normalise string columns that drive consent logic
    _normalise_consent(tables["consent"])
    _normalise_clients(tables["clients"])

    return tables


# ── Private helpers ────────────────────────────────────────────────────────────

def _check_data_dir() -> None:
    """Raise a clear error if the data folder or any CSV is missing."""
    required = [
        "clients_sample.csv",
        "consent_records_sample.csv",
        "organizations_sample.csv",
        "referrals_sample.csv",
        "service_encounters_sample.csv",
        "data_sharing_agreements_sample.csv",
        "duplicate_flags_sample.csv",
    ]
    missing = [f for f in required if not (DATA_DIR / f).exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing CSV files in {DATA_DIR}:\n"
            + "\n".join(f"  - {f}" for f in missing)
            + "\n\nCopy them from: tracks/referral-care-coordination/data/sample/"
        )


def _normalise_consent(df: pd.DataFrame) -> None:
    """Normalise consent_records columns in-place."""
    str_cols = ["status", "sharing_scope_type", "legal_basis", "consent_type"]
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.lower()

    if "purpose_codes" in df.columns:
        df["purpose_codes"] = df["purpose_codes"].fillna("").astype(str).str.strip()

    if "notes" in df.columns:
        df["notes"] = df["notes"].fillna("").astype(str)


def _normalise_clients(df: pd.DataFrame) -> None:
    """Normalise clients columns in-place."""
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

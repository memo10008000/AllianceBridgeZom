"""
src/risk_scorer.py
At-risk scoring for the Coordinated Care Console.
Scores each client 0-15 across 5 signals and returns an explainable result.

Used by:
    - pages/1_Dashboard.py   — priority list
    - pages/3_Client_Profile.py — Risk Score tab

Developer A owns this file. No Streamlit imports.
"""
from datetime import date
import pandas as pd


# ── Score thresholds ──────────────────────────────────────────────────────────
HIGH_THRESHOLD     = 7
MODERATE_THRESHOLD = 4


def compute_risk(
    client: dict,
    consent: dict | None,
    referrals_df: pd.DataFrame,
) -> dict:
    """
    Compute an at-risk score for a single client.

    Args:
        client:       Row from clients DataFrame as a dict.
        consent:      Most recent consent record as a dict, or None.
        referrals_df: Full referrals DataFrame (all clients).

    Returns:
        {
            'score':   int,           # 0-15
            'level':   str,           # 'HIGH' | 'MODERATE' | 'LOW'
            'signals': list[str],     # plain-language explanation per signal
        }
    """
    score = 0
    signals: list[str] = []

    # ── Signal 1: VI-SPDAT acuity score (0-20 scale) ─────────────────────────
    vi = _safe_int(client.get("assessment_total_score"))
    if vi >= 16:
        score += 3
        signals.append(f"VI-SPDAT {vi}/20 — critical acuity")
    elif vi >= 10:
        score += 2
        signals.append(f"VI-SPDAT {vi}/20 — high acuity")
    elif vi >= 5:
        score += 1
        signals.append(f"VI-SPDAT {vi}/20 — moderate acuity")

    # ── Signal 2: Days since last contact ─────────────────────────────────────
    last_contact = client.get("last_contact_date")
    if last_contact is not None and pd.notna(last_contact):
        try:
            last_dt = last_contact if hasattr(last_contact, "date") else pd.to_datetime(last_contact)
            days_since = (date.today() - last_dt.date()).days
            if days_since > 30:
                score += 3
                signals.append(f"No contact for {days_since} days — lost contact risk")
            elif days_since > 14:
                score += 1
                signals.append(f"No contact for {days_since} days")
        except Exception:
            pass

    # ── Signal 3: Consent expiry proximity ────────────────────────────────────
    if consent:
        expiry = consent.get("expiry_date")
        if expiry is not None and pd.notna(expiry):
            try:
                expiry_date = expiry.date() if hasattr(expiry, "date") else pd.to_datetime(expiry).date()
                days_left = (expiry_date - date.today()).days
                if days_left < 0:
                    score += 3
                    signals.append("Consent EXPIRED — data access blocked")
                elif days_left <= 7:
                    score += 3
                    signals.append(f"Consent expires in {days_left} day(s) — urgent renewal")
                elif days_left <= 30:
                    score += 1
                    signals.append(f"Consent expires in {days_left} days")
            except Exception:
                pass

    # ── Signal 4: Active referral stall ──────────────────────────────────────
    client_id = client.get("client_id", "")
    if client_id and not referrals_df.empty:
        client_refs = referrals_df[referrals_df["client_id"] == client_id]
        active_refs = client_refs[
            client_refs["status"].isin(["submitted", "acknowledged"])
        ]
        if not active_refs.empty and "submitted_at" in active_refs.columns:
            try:
                oldest = active_refs["submitted_at"].min()
                if pd.notna(oldest):
                    stall_days = (pd.Timestamp.today() - oldest).days
                    if stall_days > 14:
                        score += 2
                        signals.append(f"Referral stalled {stall_days} days with no resolution")
            except Exception:
                pass

    # ── Signal 5: Chronic homeless flag ──────────────────────────────────────
    if client.get("chronic_homeless_flag", False):
        score += 1
        signals.append("Chronically homeless — sustained high vulnerability")

    level = (
        "HIGH"     if score >= HIGH_THRESHOLD else
        "MODERATE" if score >= MODERATE_THRESHOLD else
        "LOW"
    )

    return {"score": score, "level": level, "signals": signals}


def compute_risk_for_all(tables: dict) -> pd.DataFrame:
    """
    Compute risk scores for all clients in the dataset.
    Returns a DataFrame sorted by score descending, for Dashboard use.

    Columns: client_id, full_name, risk_level, risk_score, top_signal,
             consent_status, org_id
    """
    clients_df  = tables.get("clients", pd.DataFrame())
    consent_df  = tables.get("consent", pd.DataFrame())
    referrals_df = tables.get("referrals", pd.DataFrame())

    if clients_df.empty:
        return pd.DataFrame()

    rows = []
    for _, client in clients_df.iterrows():
        cid = client.get("client_id", "")

        # Get active consent for this client
        c_rows = consent_df[
            (consent_df["client_id"] == cid) &
            (consent_df["status"] != "superseded")
        ].sort_values("given_date", ascending=False)
        consent = c_rows.iloc[0].to_dict() if not c_rows.empty else None

        risk = compute_risk(client.to_dict(), consent, referrals_df)

        rows.append({
            "client_id":     cid,
            "full_name":     f"{client.get('first_name','')} {client.get('last_name','')}".strip(),
            "risk_level":    risk["level"],
            "risk_score":    risk["score"],
            "top_signal":    risk["signals"][0] if risk["signals"] else "No signals",
            "signal_count":  len(risk["signals"]),
            "all_signals":   risk["signals"],
        })

    result = pd.DataFrame(rows)
    if not result.empty:
        result = result.sort_values("risk_score", ascending=False).reset_index(drop=True)
    return result


# ── Private helpers ────────────────────────────────────────────────────────────

def _safe_int(value) -> int:
    """Convert a value to int safely, returning 0 on failure."""
    try:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return 0
        return int(float(value))
    except (ValueError, TypeError):
        return 0

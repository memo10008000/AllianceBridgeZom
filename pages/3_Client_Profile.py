"""
pages/3_Client_Profile.py  —  SCR-03  Client Profile (Golden Record)
The Consent Banner is the most prominent element — impossible to miss.
Tabs: Overview · Risk Score · Service History · Referrals

Developer A owns src/consent_gate.py and src/risk_scorer.py.
Developer B owns this page layout.
"""
import streamlit as st
import pandas as pd
from datetime import date

try:
    from src.data_loader import load_tables
    from src.consent_gate import consent_gate, get_consent_status
    from src.risk_scorer import compute_risk
    _STUB = False
except ImportError:
    _STUB = True

st.set_page_config(
    page_title="Client Profile — Coordinated Care Console",
    page_icon="👤",
    layout="wide",
)

@st.cache_data(show_spinner="Loading client record…")
def get_tables():
    if _STUB:
        return {}
    return load_tables()

tables = get_tables()

client_id      = st.session_state.get("selected_client_id")
requesting_org = st.session_state.get("caseworker_org", "ORG-001")

# ── Navigation ────────────────────────────────────────────────────────────────
col_back1, col_back2, col_ref = st.columns([2, 2, 5])
with col_back1:
    if st.button("← Dashboard"):
        st.switch_page("pages/1_Dashboard.py")
with col_back2:
    if st.button("← Search"):
        st.switch_page("pages/2_Client_Search.py")
with col_ref:
    pass

st.divider()

if _STUB:
    st.warning("⚠️ Running in stub mode — copy CSVs into data/ and restart.")
    st.stop()

if not client_id:
    st.warning("No client selected. Use Client Search to navigate here.")
    if st.button("🔍 Go to Client Search", type="primary"):
        st.switch_page("pages/2_Client_Search.py")
    st.stop()

# ── Consent Gate — runs BEFORE any data renders ───────────────────────────────
gate_status, gate_msg = consent_gate(client_id, requesting_org, tables)

if gate_status != "ALLOW":
    st.error(f"### 🚫 Access Blocked\n\n{gate_msg}")

    st.info(
        "The Consent Gate has blocked access to this client's data. "
        "This block has been logged for the Compliance Audit."
    )

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("📋 Record / Renew Consent"):
            st.switch_page("pages/4_Consent_Form.py")
    with col_b:
        if st.button("🚨 View Compliance Audit"):
            st.switch_page("pages/5_Compliance_Audit.py")
    st.stop()

# ── Load client data (only reached if ALLOW) ──────────────────────────────────
clients_df    = tables.get("clients",    pd.DataFrame())
consent_df    = tables.get("consent",    pd.DataFrame())
encounters_df = tables.get("encounters", pd.DataFrame())
referrals_df  = tables.get("referrals",  pd.DataFrame())
orgs_df       = tables.get("orgs",       pd.DataFrame())

client_row = clients_df[clients_df["client_id"] == client_id]
if client_row.empty:
    st.error(f"Client record not found for ID: {client_id}")
    st.stop()

client = client_row.iloc[0].to_dict()
full_name = f"{client.get('first_name','')} {client.get('last_name','')}".strip()
aliases   = client.get("aliases", "")

# Active consent
consent_status, consent_record = get_consent_status(client_id, tables)
active_consent = consent_record or {}

# ── Consent banner ────────────────────────────────────────────────────────────
exp       = active_consent.get("expiry_date")
exp_str   = str(exp)[:10] if exp else "No expiry set"
scope     = active_consent.get("sharing_scope_type", "unknown")
purpose   = active_consent.get("purpose_codes", "")
collected = active_consent.get("collecting_org_id", "")

if consent_status == "VALID":
    days_left = None
    if exp and pd.notna(exp):
        exp_date = exp.date() if hasattr(exp, "date") else pd.to_datetime(exp).date()
        days_left = (exp_date - date.today()).days

    if days_left is not None and days_left <= 7:
        st.warning(
            f"⚠️ **Consent expiring in {days_left} day(s)** — renewal required soon  \n"
            f"Scope: {scope} · Purpose: {purpose} · Collected by: {collected}"
        )
    else:
        st.success(
            f"✅ **VALID CONSENT** — Active until {exp_str}  \n"
            f"Scope: {scope} · Purpose: {purpose} · Collected by: {collected}"
        )
elif consent_status == "EXPIRING":
    st.warning(
        f"⚠️ **Consent expiring: {exp_str}** — please renew  \n"
        f"Scope: {scope} · Purpose: {purpose}"
    )
elif consent_status == "EXPIRED":
    st.error(f"🔴 **CONSENT EXPIRED** as of {exp_str} — data access is restricted")
elif consent_status == "WITHDRAWN":
    st.error("🚫 **CONSENT WITHDRAWN** — this client has revoked consent")
else:
    st.error("❓ **NO CONSENT RECORD** — consent must be recorded before proceeding")

# Consent action buttons
ca1, ca2, ca3 = st.columns([2, 2, 5])
with ca1:
    if st.button("📋 Renew / Update Consent"):
        st.session_state["selected_client_id"] = client_id
        st.switch_page("pages/4_Consent_Form.py")
with ca2:
    if st.button("➕ New Referral"):
        st.switch_page("pages/7_New_Referral.py")

st.divider()

# ── Client header ─────────────────────────────────────────────────────────────
h1, h2 = st.columns([4, 1])
with h1:
    st.markdown(f"# {full_name}")
    if aliases and aliases not in ("", "nan"):
        st.caption(f"Also known as: {aliases}")
    st.caption(
        f"`{client_id}` · Primary org: {client.get('primary_org_id', '—')} · "
        f"DOB: {str(client.get('dob','—'))[:10]}"
    )
with h2:
    # Risk badge
    risk_result = compute_risk(client, active_consent, referrals_df)
    level = risk_result["level"]
    score = risk_result["score"]
    if level == "HIGH":
        st.error(f"⚡ **{level}**\nRisk: {score}/15")
    elif level == "MODERATE":
        st.warning(f"⚡ **{level}**\nRisk: {score}/15")
    else:
        st.success(f"✅ **{level}**\nRisk: {score}/15")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_overview, tab_risk, tab_history, tab_referrals = st.tabs(
    ["📋 Overview", "⚡ Risk Score", "📅 Service History", "🔄 Referrals"]
)

# ── Tab 1: Overview ───────────────────────────────────────────────────────────
with tab_overview:
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Contact Information")
        fields = [
            ("Phone",            "phone"),
            ("Email",            "email"),
            ("Address",          "current_address"),
            ("Primary Language", "primary_language"),
        ]
        for label, key in fields:
            val = client.get(key, "")
            if val and str(val) not in ("nan", ""):
                st.write(f"**{label}:** {val}")

    with col2:
        st.subheader("Client Summary")
        fields2 = [
            ("Housing Status",   "housing_status"),
            ("VI-SPDAT Score",   "assessment_total_score"),
            ("Acuity Level",     "assessment_acuity_level"),
            ("BNL Status",       "bnl_status"),
            ("CA Priority",      "ca_priority_level"),
            ("Last Contact",     "last_contact_date"),
        ]
        for label, key in fields2:
            val = client.get(key, "")
            if val and str(val) not in ("nan", "None", ""):
                st.write(f"**{label}:** {val}")

        if client.get("chronic_homeless_flag"):
            st.write("**Chronic Homeless:** ✅ Yes")

    with col3:
        st.subheader("OCAP Status")
        if client.get("ocap_protected", False):
            nation = client.get("ocap_governing_nation", "Unknown Nation")
            st.warning(
                f"🪶 **OCAP Protected**  \n"
                f"Governing Nation: **{nation}**  \n"
                f"Data sovereignty applies — Nation approval required "
                f"for cross-org data sharing."
            )
        else:
            st.info("No OCAP restrictions on this client record.")

# ── Tab 2: Risk Score ─────────────────────────────────────────────────────────
with tab_risk:
    st.subheader(f"Risk Level: {risk_result['level']}  ·  Score: {risk_result['score']}/15")

    if risk_result["level"] == "HIGH":
        st.error("This client requires immediate caseworker action.")
    elif risk_result["level"] == "MODERATE":
        st.warning("This client should be contacted within 48 hours.")
    else:
        st.success("No urgent risk signals detected.")

    st.subheader("Contributing Signals")
    if risk_result["signals"]:
        for sig in risk_result["signals"]:
            st.write(f"• {sig}")
    else:
        st.write("No risk signals triggered.")

    st.divider()
    st.subheader("Signal Thresholds")
    thresholds = pd.DataFrame([
        ("VI-SPDAT ≥16",               "+3 pts", "Critical acuity"),
        ("VI-SPDAT 10-15",             "+2 pts", "High acuity"),
        ("No contact >30 days",        "+3 pts", "Lost contact"),
        ("Consent expired",            "+3 pts", "Data going dark"),
        ("Consent expiring ≤7 days",   "+3 pts", "Urgent renewal"),
        ("Referral stalled >14 days",  "+2 pts", "Unmet need"),
        ("Chronic homeless",           "+1 pt",  "Sustained vulnerability"),
        ("HIGH threshold",             "≥7 pts", "—"),
        ("MODERATE threshold",         "≥4 pts", "—"),
    ], columns=["Signal", "Score", "Meaning"])
    st.dataframe(thresholds, use_container_width=True, hide_index=True)

# ── Tab 3: Service History ────────────────────────────────────────────────────
with tab_history:
    if gate_status != "ALLOW":
        st.error("🚫 Service history blocked by Consent Gate.")
    else:
        client_enc = encounters_df[
            encounters_df["client_id"] == client_id
        ] if not encounters_df.empty else pd.DataFrame()

        if client_enc.empty:
            st.info("No service encounters recorded for this client.")
        else:
            sort_col = "encounter_start" if "encounter_start" in client_enc.columns else client_enc.columns[0]
            client_enc = client_enc.sort_values(sort_col, ascending=False)

            show_cols = [c for c in
                         ["encounter_id", "encounter_start", "encounter_end",
                          "service_type", "org_id", "outcome", "notes"]
                         if c in client_enc.columns]

            st.caption(f"{len(client_enc)} encounter(s) on record")
            st.dataframe(
                client_enc[show_cols].reset_index(drop=True),
                use_container_width=True,
                hide_index=True,
            )

# ── Tab 4: Referrals ──────────────────────────────────────────────────────────
with tab_referrals:
    if gate_status != "ALLOW":
        st.error("🚫 Referral history blocked by Consent Gate.")
    else:
        client_refs = referrals_df[
            referrals_df["client_id"] == client_id
        ] if not referrals_df.empty else pd.DataFrame()

        if client_refs.empty:
            st.info("No referrals on record for this client.")
        else:
            sort_col = "submitted_at" if "submitted_at" in client_refs.columns else client_refs.columns[0]
            client_refs = client_refs.sort_values(sort_col, ascending=False)

            show_cols = [c for c in
                         ["referral_id", "submitted_at", "status",
                          "referral_type", "receiving_org_id",
                          "priority", "status_reason"]
                         if c in client_refs.columns]

            st.caption(f"{len(client_refs)} referral(s) on record")
            st.dataframe(
                client_refs[show_cols].reset_index(drop=True),
                use_container_width=True,
                hide_index=True,
            )

        st.divider()
        if st.button("➕ Create New Referral for this Client", type="primary"):
            st.switch_page("pages/7_New_Referral.py")

"""
pages/1_Dashboard.py  —  SCR-01  Morning Briefing
Entry point. Surfaces RED_FLAG alerts, at-risk clients, and referral pipeline.

Developer B owns this file.
"""
import streamlit as st
import pandas as pd
from datetime import date

try:
    from src.data_loader import load_tables
    from src.consent_gate import get_red_flags, get_expiring_soon
    from src.risk_scorer import compute_risk_for_all
    _STUB = False
except ImportError:
    _STUB = True

st.set_page_config(
    page_title="Dashboard — Coordinated Care Console",
    page_icon="📊",
    layout="wide",
)

@st.cache_data(show_spinner="Loading dashboard…")
def get_tables():
    if _STUB:
        return {}
    return load_tables()

tables = get_tables()

# ── Header ────────────────────────────────────────────────────────────────────
caseworker = st.session_state.get("caseworker_name", "Caseworker")
org_id     = st.session_state.get("caseworker_org", "ORG-001")

st.markdown(f"## 📊 Good morning, {caseworker}")
st.caption(
    f"{date.today().strftime('%A, %B %d, %Y')} · "
    f"Org: {org_id}"
)
st.divider()

if _STUB:
    st.warning("⚠️ Running in stub mode — copy CSVs into data/ and restart.")
    st.stop()

consent_df    = tables.get("consent", pd.DataFrame())
referrals_df  = tables.get("referrals", pd.DataFrame())
clients_df    = tables.get("clients", pd.DataFrame())

# ── Section 1: KPI tiles ──────────────────────────────────────────────────────
red_flags = get_red_flags(tables)
expiring  = get_expiring_soon(tables, days=7)

stalled = pd.DataFrame()
if not referrals_df.empty and "status" in referrals_df.columns:
    stalled = referrals_df[
        referrals_df["status"].isin(["submitted", "acknowledged"])
    ]

active_clients = len(clients_df) if not clients_df.empty else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("👥 Active Clients",       active_clients)
k2.metric("🚩 RED_FLAG Violations",  len(red_flags),
          delta=f"{len(red_flags)} critical" if len(red_flags) > 0 else None,
          delta_color="inverse")
k3.metric("⏰ Consent Expiring ≤7d", len(expiring),
          delta_color="inverse")
k4.metric("⏳ Stalled Referrals",    len(stalled),
          delta_color="inverse")

# ── Section 2: Consent Alerts ─────────────────────────────────────────────────
st.subheader("🚨 Consent Alerts — Action Required")

if not red_flags.empty:
    by_type = red_flags["flag_type"].value_counts()
    cols = st.columns(min(len(by_type), 3))
    for i, (flag_type, count) in enumerate(by_type.items()):
        with cols[i % 3]:
            st.error(f"**{flag_type}**\n\n{count} record(s)")

    if st.button("🔍 View Full Compliance Audit →", type="primary"):
        st.switch_page("pages/5_Compliance_Audit.py")
else:
    st.success("✅ No active RED_FLAG violations.")

if not expiring.empty:
    st.warning(
        f"⏰ **{len(expiring)} client(s)** have consent expiring within 7 days — "
        "renewal required before data access is blocked."
    )

st.divider()

# ── Section 3: At-Risk Clients ────────────────────────────────────────────────
st.subheader("⚡ At-Risk Clients — Today's Priority List")

with st.spinner("Computing risk scores…"):
    risk_df = compute_risk_for_all(tables)

if risk_df.empty:
    st.info("No client risk data available.")
else:
    # Filter to HIGH and MODERATE only for the dashboard view
    at_risk = risk_df[risk_df["risk_level"].isin(["HIGH", "MODERATE"])].head(20)

    if at_risk.empty:
        st.success("✅ No high or moderate risk clients today.")
    else:
        # Colour-code the risk level column
        def style_risk(val):
            if val == "HIGH":
                return "background-color: #FDECEA; color: #C00000; font-weight: bold"
            if val == "MODERATE":
                return "background-color: #FFF8E1; color: #B8860B; font-weight: bold"
            return ""

        display_df = at_risk[["full_name", "risk_level", "risk_score", "top_signal"]].copy()
        display_df.columns = ["Client", "Risk Level", "Score", "Top Signal"]
        display_df.index = range(1, len(display_df) + 1)
print(display_df.columns)
        styled = display_df.style.applymap(style_risk, subset=["Risk Level"])
        st.dataframe(styled, use_container_width=True)

        st.caption(f"Showing top {len(at_risk)} of {len(risk_df[risk_df['risk_level'].isin(['HIGH','MODERATE'])])} at-risk clients")

        # Row selection → navigate to profile
        selected_name = st.selectbox(
            "Open client profile:",
            options=["— select a client —"] + at_risk["full_name"].tolist(),
            label_visibility="collapsed",
        )
        if selected_name != "— select a client —":
            match = at_risk[at_risk["full_name"] == selected_name]
            if not match.empty:
                st.session_state["selected_client_id"] = match.iloc[0]["client_id"]
                st.switch_page("pages/3_Client_Profile.py")

st.divider()

# ── Section 4: Referral Pipeline ──────────────────────────────────────────────
st.subheader("🔄 Referral Pipeline")

if referrals_df.empty:
    st.info("No referral data available.")
else:
    pipeline_cols = st.columns(4)

    statuses = ["submitted", "acknowledged", "accepted", "in_progress"]
    labels   = ["New / Submitted", "Acknowledged", "Accepted", "In Progress"]
    icons    = ["📤", "👁️", "✅", "🔄"]

    for col, status, label, icon in zip(pipeline_cols, statuses, labels, icons):
        count = len(referrals_df[referrals_df["status"] == status]) \
                if "status" in referrals_df.columns else 0
        with col:
            st.metric(f"{icon} {label}", count)

    # Stalled referrals detail
    if not stalled.empty:
        with st.expander(f"⏳ {len(stalled)} stalled referral(s) — view details"):
            show_cols = [c for c in
                         ["client_id", "referral_id", "status",
                          "submitted_at", "referral_type", "receiving_org_id"]
                         if c in stalled.columns]
            st.dataframe(
                stalled[show_cols].head(20).reset_index(drop=True),
                use_container_width=True,
                hide_index=True,
            )

st.divider()

# ── Quick actions ─────────────────────────────────────────────────────────────
st.subheader("Quick Actions")
qa1, qa2, qa3 = st.columns(3)

with qa1:
    if st.button("🔍 Search Clients", use_container_width=True):
        st.switch_page("pages/2_Client_Search.py")
with qa2:
    if st.button("📋 Record Consent", use_container_width=True):
        st.switch_page("pages/4_Consent_Form.py")
with qa3:
    if st.button("🚨 Compliance Audit", use_container_width=True):
        st.switch_page("pages/5_Compliance_Audit.py")

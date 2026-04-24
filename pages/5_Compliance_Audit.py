"""
pages/5_Compliance_Audit.py  —  SCR-05  HERO DEMO SCREEN
Compliance Audit — RED_FLAG Dashboard

This screen demonstrates the entire hackathon thesis in 90 seconds.
It surfaces all 9 seeded RED_FLAG violations from the sample data.

Developer A owns src/consent_gate.py (the logic).
Developer B owns this page (the UI).
"""
import streamlit as st
import pandas as pd
from datetime import date

# ── Stub for development before Dev A merges ─────────────────────────────────
try:
    from src.data_loader import load_tables
    from src.consent_gate import (
        get_red_flags,
        get_expiring_soon,
        get_encounters_on_expired_consent,
    )
    _STUB = False
except ImportError:
    _STUB = True

st.set_page_config(
    page_title="Compliance Audit — Coordinated Care Console",
    page_icon="🚨",
    layout="wide",
)

# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading compliance data…")
def get_tables():
    if _STUB:
        return {}
    return load_tables()

tables = get_tables()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## 🚨 Compliance Audit")
st.caption(
    f"Consent Gate enforcement report · All organizations · "
    f"As of {date.today().strftime('%B %d, %Y')}"
)

col_back, col_export = st.columns([6, 1])
with col_back:
    if st.button("← Back to Dashboard"):
        st.switch_page("pages/1_Dashboard.py")

st.divider()

if _STUB:
    st.warning("⚠️ Running in stub mode — copy CSVs into data/ and restart.")
    st.stop()

# ── Compute all violation sets ────────────────────────────────────────────────
consent_df    = tables.get("consent", pd.DataFrame())
encounters_df = tables.get("encounters", pd.DataFrame())

red_flags              = get_red_flags(tables)
expiring               = get_expiring_soon(tables, days=7)
expiring_30            = get_expiring_soon(tables, days=30)
encounters_on_expired  = get_encounters_on_expired_consent(tables)

total_consent_records  = len(consent_df)
compliance_score = max(
    0,
    round(100 * (1 - len(red_flags) / max(total_consent_records, 1)), 1)
)

# ── KPI tiles ─────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    if len(red_flags) > 0:
        st.error(f"### 🚩 {len(red_flags)}\n**RED_FLAG Violations**")
    else:
        st.success(f"### ✅ 0\n**RED_FLAG Violations**")

with k2:
    color = "error" if len(encounters_on_expired) > 0 else "success"
    getattr(st, color)(
        f"### 🔴 {len(encounters_on_expired)}\n**Encounters on Expired Consent**"
    )

with k3:
    color = "warning" if len(expiring) > 0 else "success"
    getattr(st, color)(
        f"### ⏰ {len(expiring)}\n**Expiring ≤7 Days**"
    )

with k4:
    st.info(f"### 📋 {len(expiring_30)}\n**Expiring ≤30 Days**")

with k5:
    color = "success" if compliance_score >= 95 else "warning" if compliance_score >= 80 else "error"
    getattr(st, color)(
        f"### {compliance_score}%\n**Compliance Score**"
    )

st.divider()

# ── Section 1: Critical RED_FLAG violations ───────────────────────────────────
st.subheader("🔍 Violations by Type")

if red_flags.empty:
    st.success("✅ No RED_FLAG violations detected in the current dataset.")
else:
    by_type = (
        red_flags["flag_type"]
        .value_counts()
        .reset_index()
        .rename(columns={"flag_type": "RED_FLAG Pattern", "count": "Count"})
    )

    for _, row in by_type.iterrows():
        flag   = row["RED_FLAG Pattern"]
        count  = row["Count"]

        # Colour-code by severity
        if flag in ("RED_FLAG_EXPIRED_CONSENT_USED",
                    "RED_FLAG_WITHDRAWN_CONSENT_USED",
                    "RED_FLAG_OCAP_OVERRIDE"):
            icon = "🔴"
        elif flag in ("RED_FLAG_SCOPE_MISMATCH", "RED_FLAG_PURPOSE_VIOLATION"):
            icon = "🟠"
        else:
            icon = "🟡"

        with st.expander(f"{icon} **{flag}** — {count} record(s)", expanded=False):
            subset = red_flags[red_flags["flag_type"] == flag]

            # Show relevant columns, gracefully handle missing ones
            show_cols = [c for c in
                         ["client_id", "consent_id", "status",
                          "expiry_date", "sharing_scope_type", "notes"]
                         if c in subset.columns]
            st.dataframe(
                subset[show_cols].reset_index(drop=True),
                use_container_width=True,
                hide_index=True,
            )

            # Action buttons per record
            for idx, rec in subset.iterrows():
                cid = rec.get("client_id", "")
                if cid and st.button(
                    f"👤 View Client {cid}",
                    key=f"view_{flag}_{idx}",
                ):
                    st.session_state["selected_client_id"] = cid
                    st.switch_page("pages/3_Client_Profile.py")

st.divider()

# ── Section 2: Encounters on expired consent ──────────────────────────────────
st.subheader("📅 Encounters Recorded After Consent Expired")

if encounters_on_expired.empty:
    st.success("✅ No encounters found on expired consent.")
else:
    st.error(
        f"⚠️ {len(encounters_on_expired)} encounter(s) recorded after client's "
        "consent had already expired. These may constitute PIPA violations."
    )
    show_cols = [c for c in
                 ["client_id", "encounter_id", "encounter_start",
                  "expiry_date", "consent_id"]
                 if c in encounters_on_expired.columns]
    st.dataframe(
        encounters_on_expired[show_cols].reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
    )

st.divider()

# ── Section 3: Expiring soon ──────────────────────────────────────────────────
st.subheader("⏰ Consent Expiring Soon")

tab_7, tab_30 = st.tabs(["Expiring within 7 days", "Expiring within 30 days"])

with tab_7:
    if expiring.empty:
        st.success("✅ No consent records expiring within 7 days.")
    else:
        st.warning(f"⚠️ {len(expiring)} client(s) need consent renewal urgently.")
        show_cols = [c for c in
                     ["client_id", "consent_id", "expiry_date",
                      "sharing_scope_type", "purpose_codes"]
                     if c in expiring.columns]
        st.dataframe(
            expiring[show_cols].reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
        )

with tab_30:
    if expiring_30.empty:
        st.success("✅ No consent records expiring within 30 days.")
    else:
        show_cols = [c for c in
                     ["client_id", "consent_id", "expiry_date",
                      "sharing_scope_type", "purpose_codes"]
                     if c in expiring_30.columns]
        st.dataframe(
            expiring_30[show_cols].reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
        )

st.divider()

# ── Section 4: Full audit log ─────────────────────────────────────────────────
st.subheader("📋 Full Audit Log")

with st.expander("Show full RED_FLAG audit log", expanded=False):
    if red_flags.empty:
        st.info("No violations to display.")
    else:
        st.dataframe(
            red_flags.reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
        )
        st.download_button(
            label="⬇ Download Audit CSV",
            data=red_flags.to_csv(index=False),
            file_name=f"compliance_audit_{date.today()}.csv",
            mime="text/csv",
        )

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "🔒 All gates enforced at query time — BC PIPA · FOIPPA · OCAP · "
    "System fails safe: blocked access shows reason, never silent error."
)

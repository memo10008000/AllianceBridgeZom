"""
pages/5_Compliance_Audit.py  —  SCR-05  HERO DEMO SCREEN
"""
import streamlit as st
import pandas as pd
from datetime import date

try:
    from src.data_loader import load_tables
    from src.consent_gate import get_red_flags, get_expiring_soon, get_encounters_on_expired_consent
    from src.styles import inject_css, page_header, section_header, kpi_bar, pill
    _STUB = False
except ImportError:
    _STUB = True

inject_css()

@st.cache_data(show_spinner=False)
def get_tables():
    return {} if _STUB else load_tables()

tables = get_tables()

page_header(
    "Compliance Audit",
    subtitle=f"Consent Gate · All organizations · {date.today().strftime('%d %b %Y')}",
)

col_back, col_export = st.columns([5, 1])
with col_back:
    if st.button("← Dashboard", key="audit_back"):
        st.switch_page("pages/1_Dashboard.py")

if _STUB:
    st.warning("Stub mode — add CSVs to data/ and restart.")
    st.stop()

consent_df    = tables.get("consent",    pd.DataFrame())
encounters_df = tables.get("encounters", pd.DataFrame())

red_flags             = get_red_flags(tables)
expiring_7            = get_expiring_soon(tables, days=7)
expiring_30           = get_expiring_soon(tables, days=30)
encounters_on_expired = get_encounters_on_expired_consent(tables)
total                 = len(consent_df)
score_val             = max(0, round(100 * (1 - len(red_flags) / max(total, 1)), 1))
score_cls             = "ok" if score_val >= 95 else "warn" if score_val >= 80 else "alert"

kpi_bar([
    {"label": "RED_FLAG Violations",          "value": len(red_flags),             "sub": "require review",            "cls": "alert" if red_flags.shape[0] > 0 else "ok"},
    {"label": "Encounters on Expired Consent","value": len(encounters_on_expired),  "sub": "potential PIPA violations",  "cls": "alert" if len(encounters_on_expired) > 0 else "ok"},
    {"label": "Expiring ≤7 Days",             "value": len(expiring_7),            "sub": f"{len(expiring_30)} ≤30 days","cls": "warn" if len(expiring_7) > 0 else "ok"},
    {"label": "Compliance Score",             "value": f"{score_val}%",            "sub": f"of {total} records clean",  "cls": score_cls},
])

st.divider()

col_l, col_r = st.columns([3, 2], gap="medium")

with col_l:
    section_header("🔍 Violations by Type")

    if red_flags.empty:
        pill("✅  No RED_FLAG violations detected in the current dataset", "green")
    else:
        by_type = red_flags["flag_type"].value_counts()
        SEVERITY = {
            "RED_FLAG_EXPIRED_CONSENT_USED":    ("alert", "🔴"),
            "RED_FLAG_WITHDRAWN_CONSENT_USED":  ("alert", "🔴"),
            "RED_FLAG_OCAP_OVERRIDE":           ("alert", "🔴"),
            "RED_FLAG_SCOPE_MISMATCH":          ("warn",  "🟠"),
            "RED_FLAG_PURPOSE_VIOLATION":       ("warn",  "🟠"),
            "RED_FLAG_MISSING_PURPOSE_CODE":    ("warn",  "🟡"),
            "RED_FLAG_NO_CONSENT_RECORD":       ("warn",  "🟡"),
        }
        for flag, count in by_type.items():
            sev, icon = SEVERITY.get(flag, ("warn", "🟡"))
            kind = "red" if sev == "alert" else "amber"
            with st.expander(f"{flag}  —  {count} record(s)", expanded=sev == "alert"):
                subset = red_flags[red_flags["flag_type"] == flag]
                show_cols = [c for c in ["client_id","consent_id","status","expiry_date","notes"] if c in subset.columns]
                st.dataframe(subset[show_cols].reset_index(drop=True), use_container_width=True, hide_index=True)
                for idx, rec in subset.head(3).iterrows():
                    cid = rec.get("client_id","")
                    if cid and st.button(f"👤 View {cid}", key=f"vw_{flag}_{idx}"):
                        st.session_state["selected_client_id"] = cid
                        st.switch_page("pages/3_Client_Profile.py")

    st.markdown("<br>", unsafe_allow_html=True)
    section_header("📅 Encounters on Expired Consent")

    if encounters_on_expired.empty:
        pill("✅  No encounters found on expired consent", "green")
    else:
        pill(f"🔴  {len(encounters_on_expired)} encounter(s) recorded after consent expired — potential PIPA violations", "red")
        show_cols = [c for c in ["client_id","encounter_id","encounter_start","expiry_date","consent_id"] if c in encounters_on_expired.columns]
        st.dataframe(encounters_on_expired[show_cols].reset_index(drop=True), use_container_width=True, hide_index=True)

with col_r:
    section_header("⏰ Expiring Consent")

    tab7, tab30 = st.tabs(["≤ 7 Days", "≤ 30 Days"])
    with tab7:
        if expiring_7.empty:
            pill("✅  None expiring this week", "green")
        else:
            pill(f"⏰  {len(expiring_7)} client(s) need urgent renewal", "amber")
            show_cols = [c for c in ["client_id","expiry_date","sharing_scope_type"] if c in expiring_7.columns]
            st.dataframe(expiring_7[show_cols].reset_index(drop=True), use_container_width=True, hide_index=True)
    with tab30:
        show_cols = [c for c in ["client_id","expiry_date","sharing_scope_type"] if c in expiring_30.columns]
        if not expiring_30.empty and show_cols:
            st.dataframe(expiring_30[show_cols].reset_index(drop=True), use_container_width=True, hide_index=True)
        else:
            pill("✅  None expiring within 30 days", "green")

    st.markdown("<br>", unsafe_allow_html=True)
    section_header("📋 Full Audit Log")

    with st.expander("Show all RED_FLAG records", expanded=False):
        if red_flags.empty:
            st.info("No violations.")
        else:
            st.dataframe(red_flags.reset_index(drop=True), use_container_width=True, hide_index=True)
            st.download_button(
                "⬇ Download CSV", red_flags.to_csv(index=False),
                file_name=f"audit_{date.today()}.csv", mime="text/csv",
            )

st.divider()
st.markdown('<div style="font-size:0.7rem;color:#64748B">🔒 BC PIPA · FOIPPA · OCAP — gates enforced at query time · fails safe, never silent</div>', unsafe_allow_html=True)

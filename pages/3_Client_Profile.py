"""
pages/3_Client_Profile.py  —  SCR-03  Client Profile (Golden Record)
"""
import streamlit as st
import pandas as pd
from datetime import date

try:
    from src.data_loader import load_tables
    from src.consent_gate import consent_gate, get_consent_status
    from src.risk_scorer import compute_risk
    from src.styles import inject_css, page_header, section_header, kpi_bar, field_row, consent_banner, pill
    _STUB = False
except ImportError:
    _STUB = True

inject_css()

@st.cache_data(show_spinner=False)
def get_tables():
    return {} if _STUB else load_tables()

tables         = get_tables()
client_id      = st.session_state.get("selected_client_id")
requesting_org = st.session_state.get("caseworker_org", "ORG-001")

# ── Helper: clear the selected client so we don’t loop back ─────────────────
def _go_search():
    """Clear selected client and return to Client Search."""
    st.session_state.pop("selected_client_id", None)
    st.session_state.pop("cs_last_query", None)      # reset searchbox query too
    st.switch_page("pages/2_Client_Search.py")

def _go_dashboard():
    """Clear selected client and return to Dashboard."""
    st.session_state.pop("selected_client_id", None)
    st.switch_page("pages/1_Dashboard.py")

# ── Nav ────────────────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns([2, 2, 5])
with c1:
    if st.button("← Dashboard", key="cp_dash"):   _go_dashboard()
with c2:
    if st.button("← Search",    key="cp_search"): _go_search()

if _STUB:
    st.warning("Stub mode"); st.stop()

if not client_id:
    st.warning("No client selected. Use Client Search to navigate here.")
    if st.button("🔍 Go to Client Search", type="primary"): st.switch_page("pages/2_Client_Search.py")
    st.stop()

# ── Consent Gate ──────────────────────────────────────────────────────────────
gate_status, gate_msg = consent_gate(client_id, requesting_org, tables)

if gate_status != "ALLOW":
    st.markdown(f"""
    <div class="block-screen">
      <div class="block-icon">🚫</div>
      <div class="block-title">Consent Gate — Access Blocked</div>
      <div class="block-msg">{gate_msg}</div>
    </div>
    """, unsafe_allow_html=True)
    pill("This block has been logged for the Compliance Audit.", "gray")
    b1, b2, b3 = st.columns(3)
    with b1:
        # ← Back to Search: MUST clear selected_client_id first or we loop forever
        if st.button("← Back to Search", key="cp_block_search", use_container_width=True):
            _go_search()
    with b2:
        if st.button("📋 Record Consent", key="cp_block_consent", type="primary", use_container_width=True):
            st.switch_page("pages/4_Consent_Form.py")
    with b3:
        if st.button("🚨 Compliance Audit", key="cp_block_audit", use_container_width=True):
            st.switch_page("pages/5_Compliance_Audit.py")
    st.stop()

# ── Load data ─────────────────────────────────────────────────────────────────
clients_df    = tables.get("clients",    pd.DataFrame())
consent_df    = tables.get("consent",    pd.DataFrame())
encounters_df = tables.get("encounters", pd.DataFrame())
referrals_df  = tables.get("referrals",  pd.DataFrame())

client_row = clients_df[clients_df["client_id"] == client_id]
if client_row.empty:
    st.error(f"Client record not found: {client_id}"); st.stop()

client    = client_row.iloc[0].to_dict()
full_name = f"{client.get('first_name','')} {client.get('last_name','')}".strip()
aliases   = client.get("aliases","")
cs_status, cs_record = get_consent_status(client_id, tables)
active_consent = cs_record or {}

# ── Page header ───────────────────────────────────────────────────────────────
risk_result = compute_risk(client, active_consent, referrals_df)
level = risk_result["level"]
rl_cls = "badge-high" if level=="HIGH" else "badge-mod" if level=="MODERATE" else "badge-low"

st.markdown(f"""
<div class="page-header">
  <div>
    <div class="page-header-title">{full_name}</div>
    <div class="page-header-sub">{client_id} &nbsp;·&nbsp; {client.get('primary_org_id','—')}</div>
    {"<div style='font-size:0.72rem;color:#64748B;margin-top:0.2rem'>Also known as: " + aliases + "</div>" if aliases and aliases not in ("","nan") else ""}
  </div>
  <div><span class="badge {rl_cls}" style="font-size:0.78rem;padding:0.3rem 0.7rem">{level} RISK &nbsp; {risk_result['score']}/15</span></div>
</div>
""", unsafe_allow_html=True)

# ── Consent banner ────────────────────────────────────────────────────────────
consent_banner(cs_status, cs_record)

b1, b2 = st.columns([2, 7])
with b1:
    if st.button("📋 Renew Consent", key="cp_renew"):
        st.switch_page("pages/4_Consent_Form.py")
with b2:
    if st.button("➕ New Referral",  key="cp_ref"):
        st.switch_page("pages/7_New_Referral.py")

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📋  Overview", "⚡  Risk Score", "📅  Service History", "🔄  Referrals"])

with tab1:
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        section_header("Contact")
        for label, key in [("Phone","phone"),("Email","email"),("Address","current_address"),("Language","primary_language")]:
            v = client.get(key,"")
            if v and str(v) not in ("nan",""):
                field_row(label, str(v))

    with col_b:
        section_header("Housing & Assessment")
        for label, key in [("Housing Status","housing_status"),("VI-SPDAT","assessment_total_score"),("Acuity","assessment_acuity_level"),("Last Contact","last_contact_date"),("BNL Status","bnl_status"),("CA Priority","ca_priority_level")]:
            v = client.get(key,"")
            if v and str(v) not in ("nan","None",""):
                field_row(label, str(v)[:20])
        if client.get("chronic_homeless_flag"):
            field_row("Chronic Homeless", "✅ Yes")

    with col_c:
        section_header("OCAP & Governance")
        if client.get("ocap_protected", False):
            nation = client.get("ocap_governing_nation","Unknown Nation")
            st.markdown(f"""
            <div class="card" style="border-left:3px solid #5B21B6">
              <div class="card-title" style="color:#5B21B6">🪶 OCAP Protected</div>
              <div style="font-size:0.8rem;font-weight:500;margin-bottom:0.3rem">{nation}</div>
              <div style="font-size:0.72rem;color:#64748B">Data sovereignty applies. Nation approval required for cross-org access.</div>
            </div>""", unsafe_allow_html=True)
        else:
            pill("No OCAP restrictions on this record", "gray")

with tab2:
    kpi_bar([
        {"label": "Risk Level", "value": level,              "sub": "overall assessment",       "cls": "alert" if level=="HIGH" else "warn" if level=="MODERATE" else "ok"},
        {"label": "Risk Score", "value": f"{risk_result['score']}/15", "sub": "composite score", "cls": "alert" if level=="HIGH" else "warn" if level=="MODERATE" else "ok"},
        {"label": "Signals",    "value": len(risk_result["signals"]), "sub": "active triggers",  "cls": ""},
    ])
    section_header("Contributing Signals")
    if risk_result["signals"]:
        for sig in risk_result["signals"]:
            pill(f"• {sig}", "amber" if level in ("HIGH","MODERATE") else "gray")
    else:
        pill("No risk signals triggered", "green")

with tab3:
    client_enc = encounters_df[encounters_df["client_id"]==client_id] if not encounters_df.empty else pd.DataFrame()
    if client_enc.empty:
        pill("No service encounters on record", "gray")
    else:
        sort_col = "encounter_start" if "encounter_start" in client_enc.columns else client_enc.columns[0]
        show_cols = [c for c in ["encounter_id","encounter_start","encounter_end","service_type","org_id","outcome"] if c in client_enc.columns]
        st.caption(f"{len(client_enc)} encounter(s)")
        st.dataframe(client_enc[show_cols].sort_values(sort_col, ascending=False).reset_index(drop=True), use_container_width=True, hide_index=True)

with tab4:
    client_refs = referrals_df[referrals_df["client_id"]==client_id] if not referrals_df.empty else pd.DataFrame()
    if client_refs.empty:
        pill("No referrals on record", "gray")
    else:
        sort_col = "submitted_at" if "submitted_at" in client_refs.columns else client_refs.columns[0]
        show_cols = [c for c in ["referral_id","submitted_at","status","referral_type","receiving_org_id","priority"] if c in client_refs.columns]
        st.caption(f"{len(client_refs)} referral(s)")
        st.dataframe(client_refs[show_cols].sort_values(sort_col, ascending=False).reset_index(drop=True), use_container_width=True, hide_index=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("➕ Create New Referral", type="primary", key="cp_new_ref"):
        st.switch_page("pages/7_New_Referral.py")

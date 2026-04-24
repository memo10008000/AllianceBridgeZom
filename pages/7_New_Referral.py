"""
pages/7_New_Referral.py  —  SCR-07  New Referral (Consent-Gated)
"""
import streamlit as st
import pandas as pd
from datetime import date
import uuid

try:
    from src.data_loader import load_tables
    from src.consent_gate import consent_gate, get_consent_status
    from src.styles import inject_css, page_header, section_header, consent_banner, pill, field_row
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

if "new_referral_records" not in st.session_state:
    st.session_state.new_referral_records = []

page_header("New Referral", subtitle="Consent-gated · org list filtered to client scope")

c1, c2 = st.columns([5, 2])
with c1:
    if st.button("← Dashboard", key="nr_back"): st.switch_page("pages/1_Dashboard.py")
with c2:
    if st.button("🔍 Search Client", key="nr_search"): st.switch_page("pages/2_Client_Search.py")

if _STUB:
    st.warning("Stub mode"); st.stop()

if not client_id:
    st.markdown('<div class="block-screen"><div class="block-icon">👤</div><div class="block-title">No Client Selected</div><div class="block-msg">Search for and select a client before creating a referral.</div></div>', unsafe_allow_html=True)
    if st.button("🔍 Go to Client Search", type="primary", key="nr_go_search"):
        st.switch_page("pages/2_Client_Search.py")
    st.stop()

# ── Load client ───────────────────────────────────────────────────────────────
clients_df = tables.get("clients", pd.DataFrame())
client_row = clients_df[clients_df["client_id"] == client_id]
if client_row.empty:
    st.error(f"Client {client_id} not found."); st.stop()

client    = client_row.iloc[0].to_dict()
full_name = f"{client.get('first_name','')} {client.get('last_name','')}".strip()

# ── Consent check ─────────────────────────────────────────────────────────────
cs_status, cs_record = get_consent_status(client_id, tables)
gate_status, gate_msg = consent_gate(client_id, requesting_org, tables)

st.markdown(f"""
<div class="page-header" style="margin-top:0.5rem">
  <div>
    <div class="page-header-title">{full_name}</div>
    <div class="page-header-sub">{client_id} &nbsp;·&nbsp; Requesting org: {requesting_org}</div>
  </div>
</div>
""", unsafe_allow_html=True)

consent_banner(cs_status, cs_record)

if gate_status != "ALLOW":
    st.markdown(f"""
    <div class="block-screen">
      <div class="block-icon">🚫</div>
      <div class="block-title">Consent Gate — Referral Blocked</div>
      <div class="block-msg">{gate_msg}</div>
    </div>
    """, unsafe_allow_html=True)
    pill("This is not an app error. The Consent Gate has intentionally blocked this referral to protect the client's privacy rights under BC PIPA.", "gray")
    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("📋 Record Consent", key="nr_rc", type="primary"):
            st.session_state["selected_client_id"] = client_id
            st.switch_page("pages/4_Consent_Form.py")
    with b2:
        if st.button("🔍 Different Client", key="nr_dc"):
            st.switch_page("pages/2_Client_Search.py")
    with b3:
        if st.button("🚨 Compliance Audit", key="nr_ca"):
            st.switch_page("pages/5_Compliance_Audit.py")
    st.stop()

st.divider()
col_l, col_r = st.columns([3, 2], gap="medium")

with col_l:
    section_header("Referral Details")

    ref_type = st.selectbox("Referral Type", ["Housing","Shelter","Health","Mental Health","Substance Use","Food Security","Income Assistance","Employment","Legal Aid","Other"], key="nr_type")
    priority = st.selectbox("Priority",      ["High","Normal","Low","Critical"], index=1, key="nr_priority")
    reason   = st.text_area("Reason for Referral", placeholder="Describe the client's situation and why this referral is needed…", height=90, key="nr_reason")

    st.markdown("<br>", unsafe_allow_html=True)
    section_header("Receiving Organization")
    st.caption("Filtered to client's consent scope — excluded orgs shown for transparency")

    orgs_df     = tables.get("orgs", pd.DataFrame())
    allowed     = []
    excluded    = []

    if not orgs_df.empty:
        org_id_col   = next((c for c in ["org_id","organization_id","id"]   if c in orgs_df.columns), None)
        org_name_col = next((c for c in ["org_name","organization_name","name"] if c in orgs_df.columns), None)

        if org_id_col and org_name_col:
            for _, org_row in orgs_df.iterrows():
                oid   = str(org_row[org_id_col])
                oname = str(org_row[org_name_col])
                if oid == requesting_org:
                    continue
                g, gmsg = consent_gate(client_id, oid, tables)
                if g == "ALLOW":
                    free = ""
                    if "capacity_total_slots" in org_row and "capacity_occupied_slots" in org_row:
                        t = int(org_row.get("capacity_total_slots",0) or 0)
                        o = int(org_row.get("capacity_occupied_slots",0) or 0)
                        free = f"  ·  {max(0,t-o)} slots free"
                    allowed.append((oid, f"{oname}{free}"))
                else:
                    excluded.append((oid, oname, gmsg))

    selected_org_id = None
    if allowed:
        sel_label = st.radio("Available:", [l for _,l in allowed], key="nr_org_radio")
        selected_org_id = next((oid for oid, lbl in allowed if lbl == sel_label), None)
    else:
        st.error("No organizations available within this client's consent scope.")

    if excluded:
        with st.expander(f"🚫 {len(excluded)} org(s) excluded by Consent Gate"):
            excl_html = ""
            for oid, oname, emsg in excluded:
                excl_html += f'<div class="field-row"><span class="field-label">{oname}</span><span class="field-value" style="font-size:0.75rem;color:#64748B">{emsg}</span></div>'
            st.markdown(excl_html, unsafe_allow_html=True)

with col_r:
    section_header("Client Summary")
    for label, key in [("VI-SPDAT","assessment_total_score"),("Housing","housing_status"),("Acuity","assessment_acuity_level"),("Last Contact","last_contact_date")]:
        v = client.get(key,"")
        if v and str(v) not in ("nan","None",""):
            field_row(label, str(v)[:22])

    st.markdown("<br>", unsafe_allow_html=True)
    section_header("Linked Consent")
    if cs_record:
        for label, key in [("Consent ID","consent_id"),("Scope","sharing_scope_type"),("Purpose","purpose_codes"),("Expires","expiry_date")]:
            v = cs_record.get(key,"")
            if v: field_row(label, str(v)[:22])

st.divider()

reason_clean = (reason or "").strip()
disabled = not reason_clean or not selected_org_id
if st.button("📤 Submit Referral", type="primary", disabled=disabled, key="nr_submit", use_container_width=False):
    consent_id = cs_record.get("consent_id","UNKNOWN") if cs_record else "UNKNOWN"
    new_ref = {
        "referral_id":      f"REF-DEMO-{str(uuid.uuid4())[:8].upper()}",
        "client_id":        client_id, "client_name": full_name,
        "referring_org_id": requesting_org, "receiving_org_id": selected_org_id,
        "referral_type":    ref_type, "priority": priority,
        "reason":           reason_clean, "consent_id": consent_id,
        "submitted_at":     str(date.today()), "status": "submitted",
    }
    st.session_state.new_referral_records.append(new_ref)
    pill(f"✅  Referral submitted · ID: {new_ref['referral_id']} · To: {selected_org_id} · Consent: {consent_id}", "green")
    st.balloons()

if st.session_state.new_referral_records:
    st.divider()
    with st.expander(f"📝 Session log ({len(st.session_state.new_referral_records)} referral(s) this session)"):
        st.dataframe(pd.DataFrame(st.session_state.new_referral_records), use_container_width=True, hide_index=True)

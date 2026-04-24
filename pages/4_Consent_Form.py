"""
pages/4_Consent_Form.py  —  SCR-04  Record New Consent
"""
import streamlit as st
import pandas as pd
from datetime import date, timedelta
import uuid

try:
    from src.data_loader import load_tables
    from src.styles import inject_css, page_header, section_header, step_bar, field_row, pill
    _STUB = False
except ImportError:
    _STUB = True

inject_css()

@st.cache_data(show_spinner=False)
def get_tables():
    return {} if _STUB else load_tables()

tables = get_tables()

if "consent_step"           not in st.session_state: st.session_state.consent_step = 1
if "new_consent_records"    not in st.session_state: st.session_state.new_consent_records = []
if "consent_form_data"      not in st.session_state: st.session_state.consent_form_data = {}
if "consent_just_confirmed" not in st.session_state: st.session_state.consent_just_confirmed = None

page_header("Record Consent", subtitle="Step-by-step wizard · BC PIPA · FOIPPA · OCAP")
if st.button("← Dashboard", key="cf_back"):
    st.switch_page("pages/1_Dashboard.py")
st.divider()

if _STUB:
    st.warning("Stub mode"); st.stop()

STEPS = ["Client", "Scope & Purpose", "Expiry & OCAP", "Review"]

# ── Success screen ────────────────────────────────────────────────────────────
if st.session_state.consent_just_confirmed:
    cid = st.session_state.consent_just_confirmed
    pill(f"✅  Consent recorded · ID: {cid} · Demo mode: stored in session state, not persisted to CSV", "green")
    st.balloons()
    b1, b2 = st.columns(2)
    with b1:
        if st.button("📋 Record Another", key="cf_another"):
            st.session_state.consent_just_confirmed = None
            st.session_state.consent_step = 1
            st.session_state.consent_form_data = {}
            st.rerun()
    with b2:
        if st.button("← Dashboard", key="cf_confirmed_back"):
            st.session_state.consent_just_confirmed = None
            st.switch_page("pages/1_Dashboard.py")
    if st.session_state.new_consent_records:
        st.divider()
        with st.expander(f"Session log ({len(st.session_state.new_consent_records)} recorded)"):
            st.dataframe(pd.DataFrame(st.session_state.new_consent_records), use_container_width=True, hide_index=True)
    st.stop()

step = st.session_state.consent_step
step_bar(STEPS, step)

# ── Step 1 ────────────────────────────────────────────────────────────────────
if step == 1:
    section_header("Identify Client")
    prefill = str(st.session_state.get("selected_client_id") or "")
    client_id = st.text_input("Client ID", value=prefill, placeholder="CL-XXXXXXXX", key="cf_cid")
    cid_clean = (client_id or "").strip()

    if cid_clean:
        clients_df = tables.get("clients", pd.DataFrame())
        if not clients_df.empty:
            match = clients_df[clients_df["client_id"] == cid_clean]
            if not match.empty:
                row = match.iloc[0]
                pill(f"✅  {row.get('first_name','')} {row.get('last_name','')} · Org: {row.get('primary_org_id','')} · DOB: {str(row.get('dob',''))[:10]}", "green")
                if row.get("ocap_protected",False):
                    pill(f"🪶 OCAP protected under {row.get('ocap_governing_nation','Unknown Nation')} — Nation approval required", "amber")
            else:
                pill(f"Client ID '{cid_clean}' not found", "red")

    cw = st.session_state.get("caseworker_name","Unknown")
    org = st.session_state.get("caseworker_org","Unknown")
    pill(f"📝  Caseworker: {cw} · Org: {org}", "blue")

    if st.button("Next →", type="primary", disabled=not cid_clean, key="cf_s1_next"):
        st.session_state.consent_form_data.update({"client_id": cid_clean, "caseworker": cw, "collecting_org": org})
        st.session_state.consent_step = 2
        st.rerun()

elif step == 2:
    section_header("Consent Scope & Purpose")
    col_l, col_r = st.columns(2)
    with col_l:
        ct = st.selectbox("Consent Type",    ["explicit","implied","substitute","emergency"], key="cf_ct")
        lb = st.selectbox("Legal Basis",     ["consent","public_body","legal_obligation","vital_interest"], key="cf_lb")
    with col_r:
        pc = st.multiselect("Purpose Codes *(min. 1 required)*", ["service_delivery","ca_match","reporting","research","outreach","income_assistance"], default=["service_delivery"], key="cf_pc")
        ss = st.selectbox("Sharing Scope",   ["cluster","single_agency_only","bilateral","ca_table"], key="cf_ss")

    b1, b2 = st.columns(2)
    with b1:
        if st.button("← Back",  key="cf_s2_back"):  st.session_state.consent_step=1; st.rerun()
    with b2:
        if st.button("Next →", type="primary", disabled=len(pc)==0, key="cf_s2_next"):
            st.session_state.consent_form_data.update({"consent_type":ct,"legal_basis":lb,"purpose_codes":" ".join(pc),"sharing_scope":ss})
            st.session_state.consent_step = 3; st.rerun()

elif step == 3:
    section_header("Expiry Date & OCAP")
    col_l, col_r = st.columns(2)
    with col_l:
        no_exp = st.checkbox("No expiry (ongoing consent)", key="cf_no_exp")
        exp_date = None
        if not no_exp:
            exp_date = st.date_input("Expires on", value=date.today()+timedelta(days=365), min_value=date.today()+timedelta(days=1), key="cf_exp")
        cm = st.selectbox("Capture Method", ["paper_form","digital_signature","verbal_witnessed","kiosk","third_party_authorized"], key="cf_cm")
    with col_r:
        ocap = st.checkbox("🪶 OCAP governance applies", value=bool(st.session_state.consent_form_data.get("ocap_protected",False)), key="cf_ocap")
        nation = None
        if ocap:
            nation = st.selectbox("Governing Nation", ["Songhees Nation","Esquimalt Nation","Tsawout Nation","Pauquachin Nation","Other"], key="cf_nation")
            pill("🪶 OCAP: data ownership, control, access and possession remain with the Nation. Confirm Nation approval before saving.", "amber")

    b1, b2 = st.columns(2)
    with b1:
        if st.button("← Back",  key="cf_s3_back"):  st.session_state.consent_step=2; st.rerun()
    with b2:
        if st.button("Next →", type="primary", key="cf_s3_next"):
            st.session_state.consent_form_data.update({"expiry_date":str(exp_date) if exp_date else None,"capture_method":cm,"ocap_protected":ocap,"ocap_nation":nation})
            st.session_state.consent_step = 4; st.rerun()

elif step == 4:
    section_header("Review & Confirm")
    fd = st.session_state.consent_form_data
    col_l, col_r = st.columns(2)
    fields_l = [("Client ID",fd.get("client_id","")),("Caseworker",fd.get("caseworker","")),("Collecting Org",fd.get("collecting_org","")),("Consent Type",fd.get("consent_type","")),("Legal Basis",fd.get("legal_basis",""))]
    fields_r = [("Purpose Codes",fd.get("purpose_codes","")),("Sharing Scope",fd.get("sharing_scope","")),("Expiry Date",fd.get("expiry_date") or "No expiry"),("Capture Method",fd.get("capture_method","")),("OCAP","Yes" if fd.get("ocap_protected") else "No")]
    if fd.get("ocap_protected"):
        fields_r.append(("OCAP Nation", fd.get("ocap_nation") or ""))
    with col_l:
        for label, val in fields_l: field_row(label, str(val))
    with col_r:
        for label, val in fields_r: field_row(label, str(val))

    st.markdown("<br>", unsafe_allow_html=True)
    pill("⚠️  By confirming, you attest that informed consent was obtained in accordance with BC PIPA and all applicable legislation.", "amber")

    b1, b2 = st.columns(2)
    with b1:
        if st.button("← Back", key="cf_s4_back"): st.session_state.consent_step=3; st.rerun()
    with b2:
        if st.button("✅ Confirm & Record Consent", type="primary", key="cf_s4_confirm"):
            new_id = f"CON-DEMO-{str(uuid.uuid4())[:8].upper()}"
            st.session_state.new_consent_records.append({
                "consent_id": new_id, "client_id": fd.get("client_id"),
                "collecting_org_id": fd.get("collecting_org"), "consent_type": fd.get("consent_type"),
                "legal_basis": fd.get("legal_basis"), "purpose_codes": fd.get("purpose_codes"),
                "sharing_scope_type": fd.get("sharing_scope"), "expiry_date": fd.get("expiry_date"),
                "given_date": str(date.today()), "status": "active",
                "capture_method": fd.get("capture_method"), "ocap_protected": fd.get("ocap_protected",False),
                "ocap_governing_nation": fd.get("ocap_nation"),
                "notes": "Recorded via Coordinated Care Console demo",
            })
            st.session_state.consent_just_confirmed = new_id
            st.session_state.consent_step = 1
            st.session_state.consent_form_data = {}
            st.rerun()

if st.session_state.new_consent_records and not st.session_state.consent_just_confirmed:
    st.divider()
    with st.expander(f"Session log ({len(st.session_state.new_consent_records)} recorded this session)", expanded=False):
        st.dataframe(pd.DataFrame(st.session_state.new_consent_records), use_container_width=True, hide_index=True)

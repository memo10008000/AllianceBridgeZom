"""
pages/7_New_Referral.py  —  SCR-07  New Referral (Consent-Gated)
The Consent Gate filters the receiving org list.
Orgs outside client's consent scope are shown as excluded, not hidden.

Developer B owns this file.
"""
import streamlit as st
import pandas as pd
from datetime import date
import uuid

try:
    from src.data_loader import load_tables
    from src.consent_gate import consent_gate, get_consent_status
    _STUB = False
except ImportError:
    _STUB = True

st.set_page_config(
    page_title="New Referral — Coordinated Care Console",
    page_icon="➕",
    layout="centered",
)

@st.cache_data(show_spinner=False)
def get_tables():
    if _STUB:
        return {}
    return load_tables()

tables = get_tables()

# ── Session state ─────────────────────────────────────────────────────────────
if "new_referral_records" not in st.session_state:
    st.session_state.new_referral_records = []

client_id     = st.session_state.get("selected_client_id")
requesting_org = st.session_state.get("caseworker_org", "ORG-001")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## ➕ New Referral")

col_back, col_search = st.columns([5, 2])
with col_back:
    if st.button("← Back to Dashboard"):
        st.switch_page("pages/1_Dashboard.py")
with col_search:
    if st.button("🔍 Search for a Client"):
        st.switch_page("pages/2_Client_Search.py")

st.divider()

if _STUB:
    st.warning("⚠️ Running in stub mode — copy CSVs into data/ and restart.")
    st.stop()

# ── No client selected ────────────────────────────────────────────────────────
if not client_id:
    st.warning("No client selected. Please search for and select a client first.")
    if st.button("🔍 Go to Client Search", type="primary"):
        st.switch_page("pages/2_Client_Search.py")
    st.stop()

# ── Load client details ───────────────────────────────────────────────────────
clients_df = tables.get("clients", pd.DataFrame())
client_row = clients_df[clients_df["client_id"] == client_id]

if client_row.empty:
    st.error(f"Client {client_id} not found in database.")
    st.stop()

client = client_row.iloc[0].to_dict()
full_name = f"{client.get('first_name','')} {client.get('last_name','')}".strip()

# ── Step 1: Consent gate check ────────────────────────────────────────────────
consent_status, consent_record = get_consent_status(client_id, tables)
gate_status, gate_msg = consent_gate(client_id, requesting_org, tables)

st.subheader(f"Client: {full_name}")
st.caption(f"ID: {client_id} · Requesting org: {requesting_org}")

if consent_status == "VALID":
    exp = consent_record.get("expiry_date") if consent_record else None
    exp_str = str(exp)[:10] if exp else "No expiry"
    scope   = consent_record.get("sharing_scope_type", "") if consent_record else ""
    st.success(f"✅ Consent valid · Expires: {exp_str} · Scope: {scope}")
elif consent_status == "EXPIRING":
    exp = consent_record.get("expiry_date") if consent_record else None
    st.warning(f"⚠️ Consent expiring soon: {str(exp)[:10]} — consider renewal")
else:
    block_reason = gate_msg or "Consent gate blocked this request."
    st.error(
        "### 🚫 Consent Gate — Referral Blocked"
    )
    st.error(block_reason)
    st.info(
        "This is not an app error. The Consent Gate has intentionally blocked this referral "
        "to protect the client privacy rights under BC PIPA. "
        "No data sharing or referrals are permitted until valid consent is recorded."
    )
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        if st.button("📋 Record New Consent", key="blocked_consent"):
            st.session_state["selected_client_id"] = client_id
            st.switch_page("pages/4_Consent_Form.py")
    with col_b:
        if st.button("🔍 Search Different Client", key="blocked_search"):
            st.switch_page("pages/2_Client_Search.py")
    with col_c:
        if st.button("🚨 View Compliance Audit", key="blocked_audit"):
            st.switch_page("pages/5_Compliance_Audit.py")
    st.stop()

st.divider()

# ── Step 2: Referral details ──────────────────────────────────────────────────
st.subheader("Referral Details")

referral_type = st.selectbox(
    "Referral type",
    ["Housing", "Shelter", "Health", "Mental Health",
     "Substance Use", "Food Security", "Income Assistance",
     "Employment", "Legal Aid", "Other"],
)

priority = st.selectbox(
    "Priority",
    ["High", "Normal", "Low", "Critical"],
    index=1,
)

reason = st.text_area(
    "Reason for referral",
    placeholder="Describe the client's situation and why this referral is needed…",
    height=100,
)

st.divider()

# ── Step 3: Consent-gated org selection ──────────────────────────────────────
st.subheader("Select Receiving Organization")
st.caption(
    "Only organizations within the client's consent scope are available. "
    "Excluded orgs are shown for transparency."
)

orgs_df = tables.get("orgs", pd.DataFrame())

if orgs_df.empty:
    st.warning("Organization data unavailable.")
    allowed_orgs = []
else:
    allowed_orgs   = []
    excluded_orgs  = []

    org_name_col = next(
        (c for c in ["org_name", "organization_name", "name"] if c in orgs_df.columns),
        None
    )
    org_id_col = next(
        (c for c in ["org_id", "organization_id", "id"] if c in orgs_df.columns),
        None
    )

    if org_name_col and org_id_col:
        for _, org_row in orgs_df.iterrows():
            oid  = str(org_row[org_id_col])
            oname = str(org_row[org_name_col])

            # Skip the requesting org (can't self-refer)
            if oid == requesting_org:
                continue

            org_gate, org_msg = consent_gate(client_id, oid, tables)
            if org_gate == "ALLOW":
                # Get capacity info if available
                capacity = ""
                if "capacity_total_slots" in org_row and "capacity_occupied_slots" in org_row:
                    total    = org_row.get("capacity_total_slots", 0)
                    occupied = org_row.get("capacity_occupied_slots", 0)
                    free     = max(0, int(total or 0) - int(occupied or 0))
                    capacity = f" · {free} open slot(s)"
                allowed_orgs.append((oid, f"{oname}{capacity}"))
            else:
                # Show why excluded — transparency, not silence
                excluded_orgs.append((oid, oname, org_msg))

    # Show allowed orgs
    if allowed_orgs:
        selected_org_label = st.radio(
            "Available organizations:",
            options=[label for _, label in allowed_orgs],
        )
        selected_org_id = next(
            (oid for oid, label in allowed_orgs if label == selected_org_label),
            None
        )
    else:
        st.error("No organizations available within this client's consent scope.")
        selected_org_id = None

    # Show excluded orgs in a collapsed expander
    if excluded_orgs:
        with st.expander(f"🚫 {len(excluded_orgs)} org(s) excluded by Consent Gate"):
            for oid, oname, reason_msg in excluded_orgs:
                st.write(f"**{oname}** (`{oid}`) — {reason_msg}")

st.divider()

# ── Step 4: Submit ────────────────────────────────────────────────────────────
if not reason.strip():
    st.info("Add a reason for referral before submitting.")

submit_disabled = (
    not reason.strip() or
    not selected_org_id or
    gate_status != "ALLOW"
)

if st.button("📤 Submit Referral", type="primary", disabled=submit_disabled):
    consent_id = (
        consent_record.get("consent_id", "UNKNOWN")
        if consent_record else "UNKNOWN"
    )

    new_referral = {
        "referral_id":       f"REF-DEMO-{str(uuid.uuid4())[:8].upper()}",
        "client_id":         client_id,
        "client_name":       full_name,
        "referring_org_id":  requesting_org,
        "receiving_org_id":  selected_org_id,
        "referral_type":     referral_type,
        "priority":          priority,
        "reason":            reason.strip(),
        "consent_id":        consent_id,
        "submitted_at":      str(date.today()),
        "status":            "submitted",
    }
    st.session_state.new_referral_records.append(new_referral)

    st.success(
        f"✅ Referral submitted!\n\n"
        f"**ID:** {new_referral['referral_id']}  \n"
        f"**To:** {selected_org_id}  \n"
        f"**Type:** {referral_type} · **Priority:** {priority}  \n"
        f"**Consent linked:** {consent_id}"
    )
    st.balloons()

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        if st.button("➕ New Referral"):
            st.session_state["selected_client_id"] = None
            st.rerun()
    with col_b:
        if st.button("👤 Back to Profile"):
            st.switch_page("pages/3_Client_Profile.py")
    with col_c:
        if st.button("← Dashboard"):
            st.switch_page("pages/1_Dashboard.py")

# ── Session referral log ──────────────────────────────────────────────────────
if st.session_state.new_referral_records:
    st.divider()
    with st.expander(
        f"📝 Session referral log ({len(st.session_state.new_referral_records)} submitted this session)"
    ):
        session_df = pd.DataFrame(st.session_state.new_referral_records)
        st.dataframe(session_df, use_container_width=True, hide_index=True)

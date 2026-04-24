"""
pages/4_Consent_Form.py  —  SCR-04  Record New Consent
4-step wizard. New records stored in st.session_state for demo session.

Developer B owns this file.
"""
import streamlit as st
import pandas as pd
from datetime import date, timedelta
import uuid

try:
    from src.data_loader import load_tables
    _STUB = False
except ImportError:
    _STUB = True

st.set_page_config(
    page_title="Record Consent — Coordinated Care Console",
    page_icon="📋",
    layout="centered",
)

@st.cache_data(show_spinner=False)
def get_tables():
    if _STUB:
        return {}
    return load_tables()

tables = get_tables()

# ── Session state init ────────────────────────────────────────────────────────
if "consent_step"          not in st.session_state:
    st.session_state.consent_step = 1
if "new_consent_records"   not in st.session_state:
    st.session_state.new_consent_records = []
if "consent_form_data"     not in st.session_state:
    st.session_state.consent_form_data = {}

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## 📋 Record New Consent")
if st.button("← Back to Dashboard"):
    st.switch_page("pages/1_Dashboard.py")
st.divider()

if _STUB:
    st.warning("⚠️ Running in stub mode — copy CSVs into data/ and restart.")

step  = st.session_state.consent_step
steps = ["Client", "Scope & Purpose", "Expiry & OCAP", "Review & Confirm"]

# Progress bar + step labels
st.progress(step / len(steps), text=f"Step {step} of {len(steps)}: {steps[step - 1]}")
st.markdown(" → ".join(
    f"**{s}**" if i + 1 == step else s
    for i, s in enumerate(steps)
))
st.divider()

# ── Step 1: Select client ─────────────────────────────────────────────────────
if step == 1:
    st.subheader("Step 1: Identify Client")

    # Pre-fill if navigated from profile/search
    prefill = st.session_state.get("selected_client_id", "")

    client_id = st.text_input(
        "Client ID",
        value=prefill,
        placeholder="CL-XXXXXXXX",
        help="Enter the client ID from the client record",
    )

    # Show client name if we have data
    if client_id and not _STUB:
        clients_df = tables.get("clients", pd.DataFrame())
        match = clients_df[clients_df["client_id"] == client_id]
        if not match.empty:
            row = match.iloc[0]
            st.success(
                f"✅ Found: **{row.get('first_name','')} {row.get('last_name','')}** · "
                f"Org: {row.get('primary_org_id', '')} · "
                f"DOB: {str(row.get('dob',''))[:10]}"
            )
            # Warn if OCAP protected
            if row.get("ocap_protected", False):
                nation = row.get("ocap_governing_nation", "Unknown Nation")
                st.warning(
                    f"🪶 This client is OCAP-protected under **{nation}**. "
                    "Ensure Nation governance approval before recording consent."
                )
        else:
            st.error(f"Client ID '{client_id}' not found in the database.")

    caseworker = st.session_state.get("caseworker_name", "Unknown")
    org        = st.session_state.get("caseworker_org",  "Unknown")
    st.info(f"📝 Caseworker: **{caseworker}** · Org: **{org}**")

    if st.button("Next →", type="primary", disabled=not client_id.strip()):
        st.session_state.consent_form_data["client_id"]    = client_id.strip()
        st.session_state.consent_form_data["caseworker"]   = caseworker
        st.session_state.consent_form_data["collecting_org"] = org
        st.session_state.consent_step = 2
        st.rerun()

# ── Step 2: Scope & purpose ───────────────────────────────────────────────────
elif step == 2:
    st.subheader("Step 2: Consent Scope & Purpose")

    consent_type = st.selectbox(
        "Consent type",
        ["explicit", "implied", "substitute", "emergency"],
        help="Explicit is the strongest form. Required for cross-org data sharing.",
    )

    legal_basis = st.selectbox(
        "Legal basis (PIPA / FOIPPA)",
        ["consent", "public_body", "legal_obligation", "vital_interest"],
    )

    purpose_codes = st.multiselect(
        "Purpose codes *(FOIPPA requires at least one)*",
        ["service_delivery", "ca_match", "reporting",
         "research", "outreach", "income_assistance"],
        default=["service_delivery"],
        help="Select all purposes for which this data may be used.",
    )

    sharing_scope = st.selectbox(
        "Sharing scope",
        ["cluster", "single_agency_only", "bilateral", "ca_table"],
        help=(
            "cluster = all South Island DSA signatories · "
            "single_agency_only = this org only · "
            "bilateral = named agencies · "
            "ca_table = Coordinated Access table"
        ),
    )

    if sharing_scope == "bilateral":
        st.text_input(
            "Named agencies (comma-separated org IDs)",
            key="bilateral_orgs",
            placeholder="ORG-002, ORG-004",
        )

    col_prev, col_next = st.columns(2)
    with col_prev:
        if st.button("← Back"):
            st.session_state.consent_step = 1
            st.rerun()
    with col_next:
        if st.button("Next →", type="primary", disabled=len(purpose_codes) == 0):
            st.session_state.consent_form_data.update({
                "consent_type":   consent_type,
                "legal_basis":    legal_basis,
                "purpose_codes":  " ".join(purpose_codes),
                "sharing_scope":  sharing_scope,
            })
            st.session_state.consent_step = 3
            st.rerun()

# ── Step 3: Expiry & OCAP ─────────────────────────────────────────────────────
elif step == 3:
    st.subheader("Step 3: Expiry Date & OCAP Check")

    no_expiry = st.checkbox("No expiry date (ongoing consent)")

    expiry_date = None
    if not no_expiry:
        expiry_date = st.date_input(
            "Consent expires on",
            value=date.today() + timedelta(days=365),
            min_value=date.today() + timedelta(days=1),
        )

    capture_method = st.selectbox(
        "How was consent captured?",
        ["paper_form", "digital_signature", "verbal_witnessed",
         "kiosk", "third_party_authorized"],
    )

    if capture_method == "paper_form":
        st.text_input("Paper form reference number", key="paper_ref",
                      placeholder="e.g. OPS-2026-0423-001")

    ocap_applies = st.checkbox(
        "🪶 Apply OCAP governance (client is First Nations)",
        value=st.session_state.consent_form_data.get("ocap_flag", False),
    )
    if ocap_applies:
        st.selectbox(
            "Governing Nation",
            ["Songhees Nation", "Esquimalt Nation",
             "Tsawout Nation", "Pauquachin Nation", "Other"],
            key="ocap_nation",
        )
        st.info(
            "🪶 OCAP requires that data ownership, control, access, and possession "
            "remain with the Nation. Confirm Nation approval before saving."
        )

    col_prev, col_next = st.columns(2)
    with col_prev:
        if st.button("← Back"):
            st.session_state.consent_step = 2
            st.rerun()
    with col_next:
        if st.button("Next →", type="primary"):
            st.session_state.consent_form_data.update({
                "expiry_date":      str(expiry_date) if expiry_date else None,
                "capture_method":   capture_method,
                "ocap_protected":   ocap_applies,
                "ocap_nation":      st.session_state.get("ocap_nation", None),
            })
            st.session_state.consent_step = 4
            st.rerun()

# ── Step 4: Review & Confirm ──────────────────────────────────────────────────
elif step == 4:
    st.subheader("Step 4: Review & Confirm")

    form_data = st.session_state.consent_form_data

    # Summary table
    summary_rows = [
        ("Client ID",       form_data.get("client_id", "")),
        ("Caseworker",      form_data.get("caseworker", "")),
        ("Collecting Org",  form_data.get("collecting_org", "")),
        ("Consent Type",    form_data.get("consent_type", "")),
        ("Legal Basis",     form_data.get("legal_basis", "")),
        ("Purpose Codes",   form_data.get("purpose_codes", "")),
        ("Sharing Scope",   form_data.get("sharing_scope", "")),
        ("Expiry Date",     form_data.get("expiry_date", "No expiry")),
        ("Capture Method",  form_data.get("capture_method", "")),
        ("OCAP Protected",  "Yes" if form_data.get("ocap_protected") else "No"),
    ]
    if form_data.get("ocap_protected"):
        summary_rows.append(("OCAP Nation", form_data.get("ocap_nation", "")))

    summary_df = pd.DataFrame(summary_rows, columns=["Field", "Value"])
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    st.warning(
        "⚠️ By confirming, you attest that informed consent was obtained "
        "in accordance with BC PIPA and all applicable legislation."
    )

    col_prev, col_confirm = st.columns(2)
    with col_prev:
        if st.button("← Back"):
            st.session_state.consent_step = 3
            st.rerun()
    with col_confirm:
        if st.button("✅ Confirm & Record Consent", type="primary"):
            new_record = {
                "consent_id":          f"CON-DEMO-{str(uuid.uuid4())[:8].upper()}",
                "client_id":           form_data.get("client_id"),
                "collecting_org_id":   form_data.get("collecting_org"),
                "consent_type":        form_data.get("consent_type"),
                "legal_basis":         form_data.get("legal_basis"),
                "purpose_codes":       form_data.get("purpose_codes"),
                "sharing_scope_type":  form_data.get("sharing_scope"),
                "expiry_date":         form_data.get("expiry_date"),
                "given_date":          str(date.today()),
                "status":              "active",
                "capture_method":      form_data.get("capture_method"),
                "ocap_protected":      form_data.get("ocap_protected", False),
                "ocap_governing_nation": form_data.get("ocap_nation"),
                "notes":               "Recorded via Coordinated Care Console demo",
            }
            st.session_state.new_consent_records.append(new_record)

            # Reset wizard
            st.session_state.consent_step     = 1
            st.session_state.consent_form_data = {}

            st.success(
                f"✅ Consent recorded for session · ID: {new_record['consent_id']}\n\n"
                "*(Demo mode: stored in session state, not persisted to CSV)*"
            )
            st.balloons()

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("📋 Record Another Consent"):
                    st.rerun()
            with col_b:
                if st.button("← Back to Dashboard"):
                    st.switch_page("pages/1_Dashboard.py")

# ── Session consent log ───────────────────────────────────────────────────────
if st.session_state.new_consent_records:
    st.divider()
    with st.expander(
        f"📝 Session consent log ({len(st.session_state.new_consent_records)} recorded this session)"
    ):
        session_df = pd.DataFrame(st.session_state.new_consent_records)
        st.dataframe(session_df, use_container_width=True, hide_index=True)

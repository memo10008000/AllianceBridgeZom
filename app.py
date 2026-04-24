"""
Coordinated Care Console — app.py
Entry point. Sets up sidebar navigation and caseworker session state.
Developer B owns this file.
"""
import streamlit as st

st.set_page_config(
    page_title="Coordinated Care Console",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Caseworker session (simulated login for demo) ─────────────────────────────
if "caseworker_org" not in st.session_state:
    st.session_state.caseworker_org = "ORG-001"          # Our Place Society
if "caseworker_name" not in st.session_state:
    st.session_state.caseworker_name = "J. Nguyen"
if "selected_client_id" not in st.session_state:
    st.session_state.selected_client_id = None

# ── Sidebar navigation ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏥 Coordinated Care Console")
    st.caption(f"👤 {st.session_state.caseworker_name}")
    st.caption(f"🏢 {st.session_state.caseworker_org}")
    st.divider()

    st.page_link("pages/1_Dashboard.py",         label="📊  Dashboard",          icon=None)
    st.page_link("pages/2_Client_Search.py",     label="🔍  Client Search",       icon=None)
    st.page_link("pages/5_Compliance_Audit.py",  label="🚨  Compliance Audit",    icon=None)
    st.divider()
    st.page_link("pages/4_Consent_Form.py",      label="📋  Record Consent",      icon=None)
    st.page_link("pages/7_New_Referral.py",      label="➕  New Referral",        icon=None)
    st.divider()
    st.page_link("pages/6_Duplicate_Review.py",  label="🔀  Duplicate Review",    icon=None)
    st.divider()

    # Org switcher — populated once data is loaded (shows placeholder until then)
    st.caption("**Switch org (demo)**")
    ORG_OPTIONS = {
        "ORG-001": "Our Place Society",
        "ORG-002": "Cool Aid Society",
        "ORG-003": "BC Housing",
        "ORG-004": "Island Health",
        "ORG-005": "Victoria Cool Aid",
        "ORG-006": "Beacon Community Services",
        "ORG-007": "Pacifica Housing",
        "ORG-008": "Salvation Army",
        "ORG-009": "VIRCS",
    }
    selected_name = st.selectbox(
        "org_switcher",
        options=list(ORG_OPTIONS.values()),
        index=list(ORG_OPTIONS.keys()).index(st.session_state.caseworker_org)
              if st.session_state.caseworker_org in ORG_OPTIONS else 0,
        label_visibility="collapsed",
    )
    # Reverse lookup org_id from name
    for org_id, org_name in ORG_OPTIONS.items():
        if org_name == selected_name:
            st.session_state.caseworker_org = org_id
            break

# ── Default landing — redirect to Dashboard ───────────────────────────────────
st.switch_page("pages/1_Dashboard.py")

"""
Coordinated Care Console — app.py
Entry point. Sets up sidebar navigation and caseworker session state.

Using st.navigation() to define the page list explicitly — this removes
the auto-generated "app" entry that would otherwise appear in the sidebar.
"""
import streamlit as st

st.set_page_config(
    page_title="Coordinated Care Console",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state (simulated caseworker login for demo) ───────────────────────
if "caseworker_org"  not in st.session_state:
    st.session_state.caseworker_org  = "ORG-001"
if "caseworker_name" not in st.session_state:
    st.session_state.caseworker_name = "J. Nguyen"
if "selected_client_id" not in st.session_state:
    st.session_state.selected_client_id = None

# ── Org options for the switcher ──────────────────────────────────────────────
ORG_OPTIONS = {
    "ORG-001": "Our Place Society",
    "ORG-002": "Cool Aid Society",
    "ORG-003": "BC Housing",
    "ORG-004": "Island Health",
    "ORG-005": "Beacon Community Services",
    "ORG-006": "Pacifica Housing",
    "ORG-007": "Salvation Army",
    "ORG-008": "VIRCS",
    "ORG-009": "Victoria Cool Aid",
}

# ── Define navigation explicitly — removes the "app" sidebar entry ────────────
pg = st.navigation(
    [
        st.Page("pages/1_Dashboard.py",        title="📊 Dashboard",          url_path="Dashboard"),
        st.Page("pages/2_Client_Search.py",    title="🔍 Client Search",       url_path="Client-Search"),
        st.Page("pages/3_Client_Profile.py",   title="👤 Client Profile",      url_path="Client-Profile"),
        st.Page("pages/5_Compliance_Audit.py", title="🚨 Compliance Audit",    url_path="Compliance-Audit"),
        st.Page("pages/4_Consent_Form.py",     title="📋 Record Consent",      url_path="Consent-Form"),
        st.Page("pages/7_New_Referral.py",     title="➕ New Referral",        url_path="New-Referral"),
        st.Page("pages/6_Duplicate_Review.py", title="🔀 Duplicate Review",    url_path="Duplicate-Review"),
    ],
    position="sidebar",
)

# ── Sidebar branding + org switcher ───────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏥 Coordinated Care Console")
    st.caption(f"👤 {st.session_state.caseworker_name}")
    st.divider()

    st.caption("**Switch org (demo)**")
    selected_name = st.selectbox(
        "org_switcher",
        options=list(ORG_OPTIONS.values()),
        index=list(ORG_OPTIONS.keys()).index(st.session_state.caseworker_org)
              if st.session_state.caseworker_org in ORG_OPTIONS else 0,
        label_visibility="collapsed",
    )
    for org_id, org_name in ORG_OPTIONS.items():
        if org_name == selected_name:
            st.session_state.caseworker_org = org_id
            break

    st.caption(f"🏢 `{st.session_state.caseworker_org}`")

# ── Run the selected page ─────────────────────────────────────────────────────
pg.run()

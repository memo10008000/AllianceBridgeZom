"""
Coordinated Care Console — app.py
Entry point. Sidebar navigation, caseworker session state.

NOTE: st.Page() icon= parameter is intentionally omitted.
In newer Streamlit versions (1.40+), emoji icons in st.Page() are parsed
as Material Symbols names and render as text (e.g. keyboard_double_arrow_right).
Icons are handled purely through sidebar markdown instead.
"""
import streamlit as st

st.set_page_config(
    page_title="Coordinated Care Console",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Caseworker session ────────────────────────────────────────────────────────
if "caseworker_org"     not in st.session_state: st.session_state.caseworker_org  = "ORG-0001"
if "caseworker_name"    not in st.session_state: st.session_state.caseworker_name = "J. Nguyen"
if "selected_client_id" not in st.session_state: st.session_state.selected_client_id = None

ORG_OPTIONS = {
    "ALL":      "All Organizations",
    "ORG-0001": "Inner Harbour Emergency Shelter",
    "ORG-0002": "Rock Bay Youth Shelter",
    "ORG-0003": "Downtown Outreach Collective",
    "ORG-0004": "Pandora Recovery Services",
    "ORG-0005": "Island Mental Health Partners",
    "ORG-0006": "Vancouver Island Legal Aid Clinic",
    "ORG-0007": "Mustard Seed Food Bank",
    "ORG-0008": "Pacifica Supportive Housing",
    "ORG-0009": "Our Place Community Hub",
}

# ── Navigation — NO icon= parameter, no emoji in title ───────────────────────
# Emoji in title or icon= causes Material Symbols names to render as text
# in Streamlit 1.40+. Labels are plain text; icons are in sidebar markdown only.
pg = st.navigation(
    [
        st.Page("pages/1_Dashboard.py",        title="Dashboard",        url_path="Dashboard"),
        st.Page("pages/2_Client_Search.py",    title="Client Search",    url_path="Client-Search"),
        st.Page("pages/3_Client_Profile.py",   title="Client Profile",   url_path="Client-Profile"),
        st.Page("pages/5_Compliance_Audit.py", title="Compliance Audit", url_path="Compliance-Audit"),
        st.Page("pages/4_Consent_Form.py",     title="Record Consent",   url_path="Consent-Form"),
        st.Page("pages/7_New_Referral.py",     title="New Referral",     url_path="New-Referral"),
        st.Page("pages/6_Duplicate_Review.py", title="Duplicate Review", url_path="Duplicate-Review"),
    ],
    position="sidebar",
)

# ── Sidebar branding + org switcher ───────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏥 Coordinated Care Console")
    st.caption(f"👤  {st.session_state.caseworker_name}")
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
    st.caption(f"🏢  `{st.session_state.caseworker_org}`")

# ── Run selected page ─────────────────────────────────────────────────────────
pg.run()

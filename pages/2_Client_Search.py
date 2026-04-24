"""
pages/2_Client_Search.py  —  SCR-02  Client Search
Search across name, aliases, DOB, and Client ID.
Results show consent status and duplicate badges.

Developer B owns this file.
"""
import streamlit as st
import pandas as pd

try:
    from src.data_loader import load_tables
    from src.consent_gate import get_consent_status
    _STUB = False
except ImportError:
    _STUB = True

st.set_page_config(
    page_title="Client Search — Coordinated Care Console",
    page_icon="🔍",
    layout="wide",
)

@st.cache_data(show_spinner="Loading client data…")
def get_tables():
    if _STUB:
        return {}
    return load_tables()

tables = get_tables()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## 🔍 Client Search")

c_back, c_new = st.columns([6, 1])
with c_back:
    if st.button("← Back to Dashboard"):
        st.switch_page("pages/1_Dashboard.py")
with c_new:
    if st.button("📋 Record Consent"):
        st.switch_page("pages/4_Consent_Form.py")

st.divider()

if _STUB:
    st.warning("⚠️ Running in stub mode — copy CSVs into data/ and restart.")
    st.stop()

clients_df = tables.get("clients", pd.DataFrame())
consent_df = tables.get("consent", pd.DataFrame())
dup_df     = tables.get("dup_flags", pd.DataFrame())

if clients_df.empty:
    st.error("Client data unavailable. Check that CSVs are in the data/ folder.")
    st.stop()

# ── Search bar ────────────────────────────────────────────────────────────────
query = st.text_input(
    "Search",
    placeholder="Name, date of birth (YYYY-MM-DD), alias, or Client ID…",
    label_visibility="collapsed",
)

org_id = st.session_state.get("caseworker_org", "ORG-001")

# ── Search logic ──────────────────────────────────────────────────────────────
if not query.strip():
    st.caption("Enter a name, DOB, alias, or ID to search.")
    st.stop()

q = query.strip()

mask = (
    clients_df.get("first_name", pd.Series(dtype=str)).str.contains(q, case=False, na=False) |
    clients_df.get("last_name",  pd.Series(dtype=str)).str.contains(q, case=False, na=False) |
    clients_df.get("client_id",  pd.Series(dtype=str)).str.contains(q, case=False, na=False) |
    clients_df.get("aliases",    pd.Series(dtype=str)).str.contains(q, case=False, na=False)
)

# DOB partial match
if "dob" in clients_df.columns:
    mask = mask | clients_df["dob"].astype(str).str.contains(q, na=False)

hits = clients_df[mask].copy()
st.caption(f"**{len(hits)}** result(s) for '{q}'")

if hits.empty:
    st.info("No clients found. Try a different name, DOB, or Client ID.")
    st.stop()

# ── Attach consent status and duplicate badges ────────────────────────────────
# Consent: get the status for each hit
consent_statuses = {}
for cid in hits["client_id"].tolist():
    status, _ = get_consent_status(cid, tables)
    consent_statuses[cid] = status

hits["consent_status"] = hits["client_id"].map(consent_statuses)

# Duplicate badge: check if client_id appears as primary in dup_flags
dup_ids = set()
if not dup_df.empty and "client_id_primary" in dup_df.columns:
    pending_dups = dup_df[dup_df.get("review_status", pd.Series()) == "pending"]
    dup_ids = set(pending_dups["client_id_primary"].dropna().tolist())

# OCAP flag
ocap_ids = set()
if "ocap_protected" in clients_df.columns:
    ocap_ids = set(clients_df[clients_df["ocap_protected"] == True]["client_id"].tolist())

# ── Render results ────────────────────────────────────────────────────────────
CONSENT_ICONS = {
    "VALID":     "✅",
    "EXPIRING":  "⚠️",
    "EXPIRED":   "🔴",
    "WITHDRAWN": "🚫",
    "NO_RECORD": "❓",
}

for _, row in hits.iterrows():
    cid            = row.get("client_id", "")
    first          = str(row.get("first_name", "")).strip()
    last           = str(row.get("last_name",  "")).strip()
    full_name      = f"{first} {last}".strip() or "(No name)"
    org            = str(row.get("primary_org_id", ""))
    housing        = str(row.get("housing_status", ""))
    consent_status = row.get("consent_status", "NO_RECORD")
    is_dup         = cid in dup_ids
    is_ocap        = cid in ocap_ids

    consent_icon = CONSENT_ICONS.get(consent_status, "❓")

    # Badges
    badges = ""
    if is_dup:
        badges += " ⚠️ POSSIBLE DUPLICATE"
    if is_ocap:
        badges += " 🪶 OCAP PROTECTED"

    with st.container():
        col_info, col_action = st.columns([5, 1])

        with col_info:
            st.markdown(f"**{full_name}** · `{cid}`{badges}")
            meta_parts = []
            if org:
                meta_parts.append(f"Org: {org}")
            if housing:
                meta_parts.append(f"Housing: {housing}")
            meta_parts.append(f"Consent: {consent_icon} {consent_status}")

            dob_val = row.get("dob", None)
            if dob_val is not None and str(dob_val) not in ("", "NaT", "nan"):
                meta_parts.append(f"DOB: {str(dob_val)[:10]}")

            st.caption("  ·  ".join(meta_parts))

        with col_action:
            if is_ocap:
                st.button(
                    "🪶 OCAP",
                    key=f"ocap_{cid}",
                    help="OCAP-protected — Nation governance required",
                    disabled=True,
                )
            else:
                if st.button("View →", key=f"view_{cid}", type="primary"):
                    st.session_state["selected_client_id"] = cid
                    st.switch_page("pages/3_Client_Profile.py")

            if is_dup:
                if st.button("🔀 Review Dup", key=f"dup_{cid}"):
                    st.session_state["review_dup_client"] = cid
                    st.switch_page("pages/6_Duplicate_Review.py")

        st.divider()

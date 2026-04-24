"""
pages/2_Client_Search.py  —  SCR-02  Client Search
"""
import streamlit as st
import pandas as pd

try:
    from src.data_loader import load_tables
    from src.consent_gate import get_consent_status
    from src.styles import inject_css, page_header, section_header, pill
    _STUB = False
except ImportError:
    _STUB = True

inject_css()

@st.cache_data(show_spinner=False)
def get_tables():
    return {} if _STUB else load_tables()

tables = get_tables()

page_header("Client Search", subtitle="Search by name · DOB · alias · Client ID")

col_back, col_consent = st.columns([5, 1])
with col_back:
    if st.button("← Dashboard", key="cs_back"):
        st.switch_page("pages/1_Dashboard.py")
with col_consent:
    if st.button("📋 Record Consent", key="cs_consent"):
        st.switch_page("pages/4_Consent_Form.py")

if _STUB:
    st.warning("Stub mode")
    st.stop()

clients_df = tables.get("clients", pd.DataFrame())
consent_df = tables.get("consent", pd.DataFrame())
dup_df     = tables.get("dup_flags", pd.DataFrame())

if clients_df.empty:
    st.error("Client data unavailable.")
    st.stop()

# ── Search bar ────────────────────────────────────────────────────────────────
query = st.text_input(
    "Search", placeholder="Name, date of birth (YYYY-MM-DD), alias, or Client ID…",
    label_visibility="collapsed", key="search_query",
)

if not (query or "").strip():
    st.markdown('<div style="font-size:0.82rem;color:#64748B;margin-top:0.5rem">Enter a name, DOB, alias, or ID to search across all clients.</div>', unsafe_allow_html=True)
    st.stop()

q = query.strip()
mask = (
    clients_df.get("first_name", pd.Series(dtype=str)).str.contains(q, case=False, na=False) |
    clients_df.get("last_name",  pd.Series(dtype=str)).str.contains(q, case=False, na=False) |
    clients_df.get("client_id",  pd.Series(dtype=str)).str.contains(q, case=False, na=False) |
    clients_df.get("aliases",    pd.Series(dtype=str)).str.contains(q, case=False, na=False)
)
if "dob" in clients_df.columns:
    mask = mask | clients_df["dob"].astype(str).str.contains(q, na=False)

hits = clients_df[mask].copy()

st.markdown(f'<div style="font-size:0.72rem;color:#64748B;margin-bottom:0.75rem"><span style="font-family:\'IBM Plex Mono\',monospace;font-weight:500">{len(hits)}</span> result(s) for &ldquo;{q}&rdquo;</div>', unsafe_allow_html=True)

if hits.empty:
    pill("No clients found. Try a different name, DOB, or Client ID.", "gray")
    st.stop()

# Attach consent status
consent_statuses = {}
for cid in hits["client_id"].tolist():
    status, _ = get_consent_status(cid, tables)
    consent_statuses[cid] = status

hits["_consent_status"] = hits["client_id"].map(consent_statuses)

dup_ids = set()
if not dup_df.empty and "client_id_primary" in dup_df.columns:
    if "review_status" in dup_df.columns:
        dup_ids = set(dup_df[dup_df["review_status"] == "pending"]["client_id_primary"].dropna())
    else:
        dup_ids = set(dup_df["client_id_primary"].dropna())

ocap_ids = set()
if "ocap_protected" in clients_df.columns:
    ocap_ids = set(clients_df[clients_df["ocap_protected"] == True]["client_id"])

CONSENT_BADGE = {
    "VALID":     ("badge-valid",    "VALID"),
    "EXPIRING":  ("badge-expiring", "EXPIRING"),
    "EXPIRED":   ("badge-expired",  "EXPIRED"),
    "WITHDRAWN": ("badge-withdrawn","WITHDRAWN"),
    "NO_RECORD": ("badge-norecord", "NO RECORD"),
}

# ── Results table ─────────────────────────────────────────────────────────────
section_header(f"Results — {len(hits)} client(s)")

rows_html = ""
client_list = []
for _, row in hits.iterrows():
    cid      = row.get("client_id", "")
    first    = str(row.get("first_name", "")).strip()
    last     = str(row.get("last_name",  "")).strip()
    name     = f"{first} {last}".strip() or "(No name)"
    org      = str(row.get("primary_org_id", ""))
    housing  = str(row.get("housing_status", ""))
    cs       = row.get("_consent_status", "NO_RECORD")
    dob      = str(row.get("dob", ""))[:10]
    bc, bt   = CONSENT_BADGE.get(cs, ("badge-norecord", cs))

    extras = ""
    if cid in dup_ids:  extras += ' <span class="badge badge-dup">DUP</span>'
    if cid in ocap_ids: extras += ' <span class="badge badge-ocap">OCAP</span>'

    rows_html += f"""
    <tr>
      <td class="mono-cell">{cid}</td>
      <td style="font-weight:500">{name}{extras}</td>
      <td class="mono-cell">{dob}</td>
      <td>{org}</td>
      <td>{housing[:28]}</td>
      <td><span class="badge {bc}">{bt}</span></td>
    </tr>"""
    client_list.append({"cid": cid, "name": name})

st.markdown(f"""
<table class="data-table">
  <thead><tr><th>ID</th><th>Name</th><th>DOB</th><th>Org</th><th>Housing</th><th>Consent</th></tr></thead>
  <tbody>{rows_html}</tbody>
</table>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
options = ["— select to open profile —"] + [f"{c['cid']} · {c['name']}" for c in client_list]
selected = st.selectbox("Open client profile:", options, label_visibility="collapsed", key="cs_select")
if selected and selected != options[0]:
    cid = selected.split(" · ")[0]
    st.session_state["selected_client_id"] = cid
    st.switch_page("pages/3_Client_Profile.py")

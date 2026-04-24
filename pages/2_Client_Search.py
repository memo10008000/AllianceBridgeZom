"""
pages/2_Client_Search.py  —  SCR-02  Client Search
Live suggestions as the user types — results update on every keystroke.
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

# ── Extra CSS for live search UX ──────────────────────────────────────────────
st.markdown("""
<style>
/* Search input — larger, more prominent */
.stTextInput input {
    font-size: 1rem !important;
    padding: 0.65rem 0.9rem !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 6px !important;
    transition: border-color 0.15s !important;
}
.stTextInput input:focus {
    border-color: var(--navy) !important;
    box-shadow: 0 0 0 3px rgba(15,41,66,0.08) !important;
}
/* Result count badge */
.result-count {
    font-size: 0.7rem;
    font-weight: 600;
    color: var(--text-sm);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 0.2rem 0.6rem;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 10px;
    display: inline-block;
    margin-bottom: 0.75rem;
}
/* Suggestion card */
.suggestion-card {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.7rem 0.9rem;
    margin-bottom: 0.45rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    cursor: pointer;
    transition: border-color 0.12s, box-shadow 0.12s;
}
.suggestion-card:hover {
    border-color: var(--navy);
    box-shadow: 0 2px 8px rgba(15,41,66,0.08);
}
.sug-avatar {
    width: 36px; height: 36px;
    border-radius: 50%;
    background: var(--navy);
    color: #FFFFFF;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.8rem; font-weight: 600;
    flex-shrink: 0;
    font-family: 'IBM Plex Sans', sans-serif !important;
}
.sug-avatar.expired  { background: var(--red); }
.sug-avatar.expiring { background: var(--amber); }
.sug-avatar.valid    { background: var(--teal); }
.sug-main { flex: 1; min-width: 0; }
.sug-name {
    font-weight: 600; font-size: 0.85rem; color: var(--text);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.sug-meta {
    font-size: 0.7rem; color: var(--text-sm);
    font-family: 'IBM Plex Mono', monospace !important;
    margin-top: 0.1rem;
}
.sug-badges { display: flex; gap: 0.3rem; flex-wrap: wrap; margin-top: 0.2rem; }
.sug-right { text-align: right; flex-shrink: 0; }
.sug-consent {
    font-size: 0.65rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.04em; padding: 0.15rem 0.45rem;
    border-radius: 3px; display: inline-block;
}
.sug-consent.valid    { background: var(--green-lt); color: var(--green); }
.sug-consent.expiring { background: var(--amber-lt); color: var(--amber); }
.sug-consent.expired  { background: var(--red-lt);   color: var(--red);   }
.sug-consent.withdrawn{ background: #EDF2F7; color: var(--slate); }
.sug-consent.norecord { background: #EDF2F7; color: var(--slate); }
.sug-org { font-size: 0.7rem; color: var(--text-sm); margin-top: 0.15rem; }

/* Match highlight */
mark {
    background: rgba(13,124,124,0.15);
    color: var(--teal);
    font-weight: 600;
    border-radius: 2px;
    padding: 0 1px;
}

/* Empty state */
.empty-state {
    text-align: center; padding: 2.5rem 1rem;
    color: var(--text-sm); font-size: 0.82rem;
}
.empty-icon { font-size: 2rem; margin-bottom: 0.5rem; }

/* Search hint */
.search-hint {
    font-size: 0.78rem; color: var(--text-sm);
    padding: 0.5rem 0; display: flex; align-items: center; gap: 0.4rem;
}
</style>
""", unsafe_allow_html=True)

# ── Data ──────────────────────────────────────────────────────────────────────
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
    if st.button("Record Consent", key="cs_consent"):
        st.switch_page("pages/4_Consent_Form.py")

if _STUB:
    st.warning("Stub mode"); st.stop()

clients_df = tables.get("clients", pd.DataFrame())
consent_df = tables.get("consent", pd.DataFrame())
dup_df     = tables.get("dup_flags", pd.DataFrame())

if clients_df.empty:
    st.error("Client data unavailable."); st.stop()

# ── Precompute dup and ocap sets once ─────────────────────────────────────────
dup_ids = set()
if not dup_df.empty and "client_id_primary" in dup_df.columns:
    if "review_status" in dup_df.columns:
        dup_ids = set(dup_df[dup_df["review_status"]=="pending"]["client_id_primary"].dropna())
    else:
        dup_ids = set(dup_df["client_id_primary"].dropna())

ocap_ids = set()
if "ocap_protected" in clients_df.columns:
    ocap_ids = set(clients_df[clients_df["ocap_protected"]==True]["client_id"])

# ── Search bar ────────────────────────────────────────────────────────────────
# NOTE: Do NOT pass value= together with key= — Streamlit treats the session-state
# key as the single source of truth and silently ignores value=, which breaks the
# live-search by always delivering an empty string to the filter logic.
st.text_input(
    "Search",
    placeholder="Start typing a name, Client ID, DOB, or alias…",
    label_visibility="collapsed",
    key="cs_input",
)

q = (st.session_state.get("cs_input") or "").strip()

# ── Hint line ─────────────────────────────────────────────────────────────────
if not q:
    st.markdown(
        '<div class="search-hint">🔍  Type at least 1 character to see suggestions</div>',
        unsafe_allow_html=True
    )
    st.stop()

# ── Live search — runs on every character ─────────────────────────────────────
mask = (
    clients_df.get("first_name", pd.Series(dtype=str)).str.contains(q, case=False, na=False) |
    clients_df.get("last_name",  pd.Series(dtype=str)).str.contains(q, case=False, na=False) |
    clients_df.get("client_id",  pd.Series(dtype=str)).str.contains(q, case=False, na=False) |
    clients_df.get("aliases",    pd.Series(dtype=str)).str.contains(q, case=False, na=False)
)
if "dob" in clients_df.columns:
    mask = mask | clients_df["dob"].astype(str).str.contains(q, na=False)

hits = clients_df[mask].copy().head(30)  # cap at 30 for live performance

total_matches = mask.sum()

# ── Result count ──────────────────────────────────────────────────────────────
if total_matches == 0:
    st.markdown(f"""
    <div class="empty-state">
      <div class="empty-icon">🔎</div>
      <div>No clients match <strong>{q}</strong></div>
      <div style="margin-top:0.3rem;font-size:0.72rem">Try a different name, ID, or DOB</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

more = f"  ·  showing first 30" if total_matches > 30 else ""
st.markdown(
    f'<div class="result-count">{total_matches} match{"es" if total_matches != 1 else ""}{more}</div>',
    unsafe_allow_html=True
)

# ── Highlight helper ──────────────────────────────────────────────────────────
def highlight(text: str, q: str) -> str:
    """Wrap query match in <mark> for visual highlight."""
    if not q or not text:
        return str(text)
    import re
    escaped = re.escape(q)
    return re.sub(f"({escaped})", r"<mark>\1</mark>", str(text), flags=re.IGNORECASE)

# ── Consent status cache ──────────────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=60)
def get_all_consent_statuses(_consent_df, client_ids: tuple):
    result = {}
    for cid in client_ids:
        active = _consent_df[
            (_consent_df["client_id"] == cid) &
            (_consent_df["status"] != "superseded")
        ].sort_values("given_date", ascending=False)
        if active.empty:
            result[cid] = "NO_RECORD"
            continue
        c = active.iloc[0]
        if c["status"] == "withdrawn":
            result[cid] = "WITHDRAWN"
        elif pd.notna(c.get("expiry_date")):
            from datetime import date
            import pandas as pd2
            exp = c["expiry_date"].date() if hasattr(c["expiry_date"], "date") else c["expiry_date"]
            today = date.today()
            if exp < today:
                result[cid] = "EXPIRED"
            elif (exp - today).days <= 30:
                result[cid] = "EXPIRING"
            else:
                result[cid] = "VALID"
        else:
            result[cid] = "VALID"
    return result

client_ids_tuple = tuple(hits["client_id"].tolist())
consent_map = get_all_consent_statuses(consent_df, client_ids_tuple)

CONSENT_LABEL = {
    "VALID":     ("valid",    "Valid"),
    "EXPIRING":  ("expiring", "Expiring"),
    "EXPIRED":   ("expired",  "Expired"),
    "WITHDRAWN": ("withdrawn","Withdrawn"),
    "NO_RECORD": ("norecord", "No Record"),
}

# ── Suggestion cards ──────────────────────────────────────────────────────────
for _, row in hits.iterrows():
    cid        = row.get("client_id", "")
    first      = str(row.get("first_name", "")).strip()
    last       = str(row.get("last_name",  "")).strip()
    full_name  = f"{first} {last}".strip() or "(No name)"
    org        = str(row.get("primary_org_id", "—"))
    housing    = str(row.get("housing_status", "—"))
    dob        = str(row.get("dob", ""))[:10]
    aliases    = str(row.get("aliases", ""))
    cs         = consent_map.get(cid, "NO_RECORD")
    cs_cls, cs_lbl = CONSENT_LABEL.get(cs, ("norecord", "No Record"))

    # Avatar initials
    initials = f"{first[:1]}{last[:1]}".upper() or "??"
    avatar_cls = cs_cls if cs_cls in ("valid","expired","expiring") else ""

    # Extra badges
    badges_html = ""
    if cid in dup_ids:
        badges_html += '<span class="badge badge-dup" style="font-size:0.6rem">DUP</span>'
    if cid in ocap_ids:
        badges_html += '<span class="badge badge-ocap" style="font-size:0.6rem">OCAP</span>'

    # Highlight matching text
    name_hl   = highlight(full_name, q)
    cid_hl    = highlight(cid, q)
    alias_str = f" · alias: {highlight(aliases, q)}" if aliases and aliases not in ("", "nan") else ""

    # Card HTML (display only — button handles navigation)
    st.markdown(f"""
    <div class="suggestion-card">
      <div class="sug-avatar {avatar_cls}">{initials}</div>
      <div class="sug-main">
        <div class="sug-name">{name_hl}</div>
        <div class="sug-meta">{cid_hl}{alias_str}</div>
        <div class="sug-meta">DOB: {dob} · Housing: {housing[:28]}</div>
        {f'<div class="sug-badges">{badges_html}</div>' if badges_html else ""}
      </div>
      <div class="sug-right">
        <div class="sug-consent {cs_cls}">{cs_lbl}</div>
        <div class="sug-org">{org}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Invisible button that sits on top and handles click
    if st.button(
        f"Open {full_name}",
        key=f"open_{cid}",
        help=f"View profile for {full_name}",
        use_container_width=True,
    ):
        st.session_state["selected_client_id"] = cid
        st.switch_page("pages/3_Client_Profile.py")

# ── Footer hint ───────────────────────────────────────────────────────────────
if total_matches > 30:
    st.markdown(
        f'<div class="search-hint" style="justify-content:center;margin-top:0.5rem">'
        f'Showing first 30 of {total_matches} — refine your search to narrow results'
        f'</div>',
        unsafe_allow_html=True
    )

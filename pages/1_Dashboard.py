"""
pages/1_Dashboard.py  —  SCR-01  Morning Briefing
Professional two-column layout with custom CSS for a clinical, data-dense dashboard.
"""
import streamlit as st
import pandas as pd
from datetime import date

try:
    from src.data_loader import load_tables
    from src.consent_gate import get_red_flags, get_expiring_soon
    from src.risk_scorer import compute_risk_for_all
    _STUB = False
except ImportError:
    _STUB = True

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

/* ── Root variables ── */
:root {
    --navy:    #0F2942;
    --teal:    #0D7C7C;
    --teal-lt: #E0F4F4;
    --red:     #C0392B;
    --red-lt:  #FDECEA;
    --amber:   #C07000;
    --amber-lt:#FFF3E0;
    --green:   #1A6B3A;
    --green-lt:#E6F5EC;
    --slate:   #4A5568;
    --border:  #DDE2E8;
    --bg:      #F7F9FC;
    --white:   #FFFFFF;
    --text:    #1A202C;
    --text-sm: #64748B;
}

/* ── Global font override ── */
html, body, [class*="css"], .stMarkdown, .stText,
.stDataFrame, p, div, span, td, th, label {
    font-family: 'IBM Plex Sans', sans-serif !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ── Slim the sidebar ── */
[data-testid="stSidebar"] {
    min-width: 200px !important;
    max-width: 200px !important;
    background: var(--navy) !important;
}
[data-testid="stSidebar"] * {
    color: #CBD5E0 !important;
    font-size: 0.82rem !important;
}
[data-testid="stSidebar"] .stMarkdown h3 {
    color: #FFFFFF !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
}
[data-testid="stSidebarNavLink"] {
    padding: 0.35rem 0.75rem !important;
    border-radius: 4px !important;
    margin: 1px 0 !important;
    font-size: 0.8rem !important;
}
[data-testid="stSidebarNavLink"][aria-current="page"] {
    background: rgba(255,255,255,0.12) !important;
    color: #FFFFFF !important;
}
[data-testid="stSidebarNavLink"]:hover {
    background: rgba(255,255,255,0.08) !important;
}

/* ── Main content padding ── */
.main .block-container {
    padding: 1.5rem 2rem 2rem 2rem !important;
    max-width: 1400px !important;
}

/* ── Page header ── */
.dash-header {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    margin-bottom: 1.25rem;
    padding-bottom: 0.75rem;
    border-bottom: 2px solid var(--navy);
}
.dash-header-title {
    font-size: 1.35rem;
    font-weight: 600;
    color: var(--navy);
    letter-spacing: -0.01em;
}
.dash-header-sub {
    font-size: 0.78rem;
    color: var(--text-sm);
    font-family: 'IBM Plex Mono', monospace !important;
}

/* ── KPI bar ── */
.kpi-bar {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.75rem;
    margin-bottom: 1.25rem;
}
.kpi-card {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.85rem 1rem;
    border-left: 3px solid var(--navy);
}
.kpi-card.alert  { border-left-color: var(--red); }
.kpi-card.warn   { border-left-color: var(--amber); }
.kpi-card.ok     { border-left-color: var(--green); }
.kpi-label {
    font-size: 0.68rem;
    font-weight: 500;
    color: var(--text-sm);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 0.2rem;
}
.kpi-value {
    font-size: 1.85rem;
    font-weight: 300;
    color: var(--navy);
    line-height: 1;
    font-family: 'IBM Plex Mono', monospace !important;
}
.kpi-value.alert { color: var(--red); }
.kpi-value.warn  { color: var(--amber); }
.kpi-value.ok    { color: var(--green); }
.kpi-sub {
    font-size: 0.68rem;
    color: var(--text-sm);
    margin-top: 0.2rem;
}

/* ── Section headers ── */
.section-header {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-sm);
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.4rem;
    margin-bottom: 0.75rem;
}

/* ── Alert pill ── */
.alert-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: var(--red-lt);
    border: 1px solid #F5C6CB;
    border-radius: 4px;
    padding: 0.4rem 0.75rem;
    font-size: 0.78rem;
    color: var(--red);
    font-weight: 500;
    margin: 0.25rem 0;
    width: 100%;
}
.warn-pill {
    background: var(--amber-lt);
    border-color: #FFCC80;
    color: var(--amber);
}
.ok-pill {
    background: var(--green-lt);
    border-color: #A8D5B5;
    color: var(--green);
}

/* ── Risk table ── */
.risk-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.8rem;
}
.risk-table th {
    font-size: 0.65rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-sm);
    background: var(--bg);
    padding: 0.5rem 0.6rem;
    text-align: left;
    border-bottom: 1px solid var(--border);
}
.risk-table td {
    padding: 0.5rem 0.6rem;
    border-bottom: 1px solid #EDF2F7;
    color: var(--text);
    vertical-align: middle;
}
.risk-table tr:hover td { background: #F8FAFC; }
.badge {
    display: inline-block;
    padding: 0.15rem 0.5rem;
    border-radius: 3px;
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.badge-high   { background: var(--red-lt);   color: var(--red);   }
.badge-mod    { background: var(--amber-lt); color: var(--amber); }
.badge-low    { background: var(--green-lt); color: var(--green); }

/* ── Pipeline ── */
.pipeline-row {
    display: flex;
    align-items: stretch;
    gap: 0;
    margin: 0.5rem 0;
}
.pipeline-stage {
    flex: 1;
    text-align: center;
    padding: 0.6rem 0.4rem;
    border: 1px solid var(--border);
    border-right: none;
    background: var(--white);
    font-size: 0.72rem;
}
.pipeline-stage:first-child { border-radius: 4px 0 0 4px; }
.pipeline-stage:last-child  { border-right: 1px solid var(--border); border-radius: 0 4px 4px 0; }
.pipeline-count {
    font-size: 1.4rem;
    font-weight: 300;
    color: var(--navy);
    font-family: 'IBM Plex Mono', monospace !important;
    display: block;
}
.pipeline-label {
    font-size: 0.62rem;
    color: var(--text-sm);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* ── Org capacity ── */
.org-row {
    display: flex;
    align-items: center;
    padding: 0.45rem 0;
    border-bottom: 1px solid #EDF2F7;
    gap: 0.6rem;
    font-size: 0.78rem;
}
.org-name  { flex: 1; color: var(--text); font-weight: 500; }
.org-bar-wrap { width: 80px; height: 6px; background: #E2E8F0; border-radius: 3px; overflow: hidden; }
.org-bar   { height: 100%; border-radius: 3px; background: var(--teal); }
.org-bar.full { background: var(--amber); }
.org-count { font-size: 0.68rem; color: var(--text-sm); width: 45px; text-align: right;
             font-family: 'IBM Plex Mono', monospace !important; }

/* ── Expiring table ── */
.exp-row {
    display: flex;
    align-items: center;
    padding: 0.4rem 0;
    border-bottom: 1px solid #EDF2F7;
    gap: 0.5rem;
    font-size: 0.78rem;
}
.exp-client { flex: 1; font-weight: 500; }
.exp-days   { font-family: 'IBM Plex Mono', monospace !important;
              font-size: 0.72rem; color: var(--amber); font-weight: 600; }

/* ── Column layout helper ── */
.two-col { display: grid; grid-template-columns: 3fr 2fr; gap: 1.25rem; align-items: start; }
.card {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 1rem 1.1rem;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ── Data ──────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def get_tables():
    if _STUB:
        return {}
    return load_tables()

tables      = get_tables()
caseworker  = st.session_state.get("caseworker_name", "Caseworker")
org_id      = st.session_state.get("caseworker_org", "ORG-001")
today_str   = date.today().strftime("%a %d %b %Y")

if _STUB:
    st.warning("⚠️ Stub mode — copy CSVs into data/ and restart.")
    st.stop()

consent_df   = tables.get("consent",   pd.DataFrame())
referrals_df = tables.get("referrals", pd.DataFrame())
clients_df   = tables.get("clients",   pd.DataFrame())
orgs_df      = tables.get("orgs",      pd.DataFrame())

red_flags    = get_red_flags(tables)
expiring_7   = get_expiring_soon(tables, days=7)
expiring_30  = get_expiring_soon(tables, days=30)

stalled = pd.DataFrame()
if not referrals_df.empty and "status" in referrals_df.columns:
    stalled = referrals_df[referrals_df["status"].isin(["submitted", "acknowledged"])]

active_clients = len(clients_df)

with st.spinner("Computing risk scores…"):
    risk_df = compute_risk_for_all(tables)

at_risk = risk_df[risk_df["risk_level"].isin(["HIGH", "MODERATE"])].head(15) \
          if not risk_df.empty else pd.DataFrame()

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="dash-header">
  <div>
    <div class="dash-header-title">Good morning, {caseworker}</div>
    <div class="dash-header-sub">{org_id} &nbsp;·&nbsp; {today_str}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── KPI bar ───────────────────────────────────────────────────────────────────
rf_cls  = "alert" if len(red_flags) > 0 else "ok"
exp_cls = "warn"  if len(expiring_7) > 0 else "ok"
st_cls  = "warn"  if len(stalled) > 10  else "ok"

st.markdown(f"""
<div class="kpi-bar">
  <div class="kpi-card">
    <div class="kpi-label">Active Clients</div>
    <div class="kpi-value">{active_clients}</div>
    <div class="kpi-sub">across all orgs</div>
  </div>
  <div class="kpi-card {rf_cls}">
    <div class="kpi-label">RED_FLAG Violations</div>
    <div class="kpi-value {rf_cls}">{len(red_flags)}</div>
    <div class="kpi-sub">require immediate action</div>
  </div>
  <div class="kpi-card {exp_cls}">
    <div class="kpi-label">Consent Expiring ≤7d</div>
    <div class="kpi-value {exp_cls}">{len(expiring_7)}</div>
    <div class="kpi-sub">{len(expiring_30)} expiring ≤30d</div>
  </div>
  <div class="kpi-card {st_cls}">
    <div class="kpi-label">Stalled Referrals</div>
    <div class="kpi-value {st_cls}">{len(stalled)}</div>
    <div class="kpi-sub">awaiting response</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Two-column body ───────────────────────────────────────────────────────────
col_left, col_right = st.columns([3, 2], gap="medium")

# ════ LEFT COLUMN ════════════════════════════════════════════════════════════

with col_left:

    # ── Consent Alerts ────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">🚨 Consent Alerts</div>', unsafe_allow_html=True)

    if red_flags.empty:
        st.markdown('<div class="alert-pill ok-pill">✅ No active RED_FLAG violations</div>',
                    unsafe_allow_html=True)
    else:
        by_type = red_flags["flag_type"].value_counts()
        for flag_type, count in by_type.items():
            st.markdown(
                f'<div class="alert-pill">🚩 {flag_type} &nbsp;—&nbsp; {count} record(s)</div>',
                unsafe_allow_html=True
            )
        if st.button("→ View Full Compliance Audit", type="primary", key="btn_audit"):
            st.switch_page("pages/5_Compliance_Audit.py")

    if not expiring_7.empty:
        st.markdown(
            f'<div class="alert-pill warn-pill">⏰ {len(expiring_7)} client(s) — '
            f'consent expiring within 7 days</div>',
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── At-Risk Priority List ─────────────────────────────────────────────────
    st.markdown('<div class="section-header">⚡ At-Risk Clients — Priority List</div>',
                unsafe_allow_html=True)

    if at_risk.empty:
        st.markdown('<div class="alert-pill ok-pill">✅ No high or moderate risk clients</div>',
                    unsafe_allow_html=True)
    else:
        rows_html = ""
        for i, (_, row) in enumerate(at_risk.iterrows(), 1):
            level = row["risk_level"]
            badge_cls = "badge-high" if level == "HIGH" else "badge-mod"
            score = row["risk_score"]
            signal = str(row["top_signal"])[:48]
            name = str(row["full_name"])
            rows_html += f"""
            <tr>
              <td style="color:#64748B;font-family:'IBM Plex Mono',monospace;font-size:0.65rem">{i}</td>
              <td style="font-weight:500">{name}</td>
              <td><span class="badge {badge_cls}">{level}</span></td>
              <td style="font-family:'IBM Plex Mono',monospace">{score}/15</td>
              <td style="color:#64748B;font-size:0.75rem">{signal}</td>
            </tr>"""

        st.markdown(f"""
        <table class="risk-table">
          <thead><tr>
            <th>#</th><th>Client</th><th>Risk</th><th>Score</th><th>Top Signal</th>
          </tr></thead>
          <tbody>{rows_html}</tbody>
        </table>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        selected = st.selectbox(
            "Open profile:",
            ["— select —"] + at_risk["full_name"].tolist(),
            label_visibility="collapsed",
            key="risk_select",
        )
        if selected != "— select —":
            match = at_risk[at_risk["full_name"] == selected]
            if not match.empty:
                st.session_state["selected_client_id"] = match.iloc[0]["client_id"]
                st.switch_page("pages/3_Client_Profile.py")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Referral Pipeline ─────────────────────────────────────────────────────
    st.markdown('<div class="section-header">🔄 Referral Pipeline</div>',
                unsafe_allow_html=True)

    stages = [
        ("submitted",   "Submitted"),
        ("acknowledged","Acknowledged"),
        ("accepted",    "Accepted"),
        ("in_progress", "In Progress"),
        ("completed",   "Completed"),
    ]
    counts = {}
    for status, label in stages:
        counts[status] = len(referrals_df[referrals_df["status"] == status]) \
                         if not referrals_df.empty and "status" in referrals_df.columns else 0

    stage_html = "".join(
        f'<div class="pipeline-stage">'
        f'<span class="pipeline-count">{counts[s]}</span>'
        f'<span class="pipeline-label">{l}</span>'
        f'</div>'
        for s, l in stages
    )
    st.markdown(f'<div class="pipeline-row">{stage_html}</div>', unsafe_allow_html=True)


# ════ RIGHT COLUMN ═══════════════════════════════════════════════════════════

with col_right:

    # ── Expiring Soon ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">⏰ Expiring Consent</div>',
                unsafe_allow_html=True)

    if expiring_7.empty:
        st.markdown('<div class="alert-pill ok-pill">✅ None expiring this week</div>',
                    unsafe_allow_html=True)
    else:
        exp_html = ""
        show_cols_exp = [c for c in ["client_id", "expiry_date"] if c in expiring_7.columns]
        for _, row in expiring_7.head(8).iterrows():
            cid  = row.get("client_id", "")
            exp  = row.get("expiry_date")
            exp_str = str(exp)[:10] if exp is not None else "—"
            try:
                days_left = (pd.to_datetime(exp).date() - date.today()).days
                days_str = f"{days_left}d"
            except Exception:
                days_str = "—"
            exp_html += f"""
            <div class="exp-row">
              <span class="exp-client">{cid}</span>
              <span style="font-size:0.7rem;color:#64748B">{exp_str}</span>
              <span class="exp-days">{days_str}</span>
            </div>"""
        st.markdown(exp_html, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Org Capacity ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">🏢 Org Capacity</div>',
                unsafe_allow_html=True)

    if orgs_df.empty:
        st.markdown('<div style="font-size:0.78rem;color:#64748B">No org data.</div>',
                    unsafe_allow_html=True)
    else:
        org_html = ""
        for _, org in orgs_df.head(9).iterrows():
            name  = str(org.get("org_name", org.get("name", "—")))[:22]
            total = int(org.get("capacity_total_slots", 0) or 0)
            occ   = int(org.get("capacity_occupied_slots", 0) or 0)
            if total > 0:
                pct = min(int(occ / total * 100), 100)
                bar_cls = "full" if pct >= 85 else ""
                free = total - occ
                org_html += f"""
                <div class="org-row">
                  <span class="org-name">{name}</span>
                  <div class="org-bar-wrap">
                    <div class="org-bar {bar_cls}" style="width:{pct}%"></div>
                  </div>
                  <span class="org-count">{free} free</span>
                </div>"""
        if org_html:
            st.markdown(org_html, unsafe_allow_html=True)
        else:
            st.markdown('<div style="font-size:0.78rem;color:#64748B">No capacity data.</div>',
                        unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Quick Actions ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Quick Actions</div>',
                unsafe_allow_html=True)
    if st.button("🔍 Search Clients",     use_container_width=True, key="qa_search"):
        st.switch_page("pages/2_Client_Search.py")
    if st.button("📋 Record Consent",     use_container_width=True, key="qa_consent"):
        st.switch_page("pages/4_Consent_Form.py")
    if st.button("➕ New Referral",       use_container_width=True, key="qa_referral"):
        st.switch_page("pages/7_New_Referral.py")
    if st.button("🚨 Compliance Audit",   use_container_width=True, key="qa_audit"):
        st.switch_page("pages/5_Compliance_Audit.py")

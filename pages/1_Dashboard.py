"""
pages/1_Dashboard.py  —  SCR-01  Morning Briefing
Clickable KPI cards — proper full-card design with responsive layout.
"""
import streamlit as st
import pandas as pd
from datetime import date

try:
    from src.data_loader import load_tables
    from src.consent_gate import get_red_flags, get_expiring_soon, get_encounters_on_expired_consent
    from src.risk_scorer import compute_risk_for_all
    from src.styles import inject_css, section_header, pill
    _STUB = False
except ImportError:
    _STUB = True

inject_css()

st.markdown("""
<style>
/* ── Responsive: stack to 2 cols on mobile ── */
@media (max-width: 640px) {
    .kpi-responsive {
        grid-template-columns: repeat(2, 1fr) !important;
    }
}

/* ── Page header ── */
.page-header {
    display: flex; align-items: baseline; justify-content: space-between;
    margin-bottom: 1.25rem; padding-bottom: 0.75rem;
    border-bottom: 2px solid var(--navy);
}
.page-header-title { font-size: 1.3rem; font-weight: 600; color: var(--navy); }
.page-header-sub   { font-size: 0.75rem; color: var(--text-sm); font-family: 'IBM Plex Mono', monospace !important; }

/* ── KPI card HTML blocks (not buttons — used for display) ── */
.kpi-card {
    background: var(--white);
    border: 1px solid var(--border);
    border-left: 3px solid var(--navy);
    border-radius: 6px;
    padding: 0.85rem 1rem;
    cursor: pointer;
    transition: box-shadow 0.15s;
    height: 100%;
}
.kpi-card:hover { box-shadow: 0 2px 10px rgba(15,41,66,0.10); }
.kpi-card.alert { border-left-color: var(--red); }
.kpi-card.warn  { border-left-color: var(--amber); }
.kpi-card.ok    { border-left-color: var(--green); }
.kpi-lbl {
    font-size: 0.63rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.07em; color: var(--text-sm); margin-bottom: 0.35rem;
}
.kpi-num {
    font-size: 2.1rem; font-weight: 300; line-height: 1;
    font-family: 'IBM Plex Mono', monospace !important;
    color: var(--navy);
    display: flex; align-items: baseline; gap: 0.4rem;
}
.kpi-num.alert { color: var(--red); }
.kpi-num.warn  { color: var(--amber); }
.kpi-num.ok    { color: var(--green); }

/* ── KPI number <a> link — visually identical to the original big number ── */
a.kpi-link {
    font-size: 2.1rem !important;
    font-weight: 300 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    line-height: 1 !important;
    color: var(--navy) !important;
    text-decoration: underline dotted !important;
    text-decoration-color: rgba(15,41,66,0.3) !important;
    text-underline-offset: 4px !important;
    letter-spacing: -0.01em !important;
    cursor: pointer !important;
    display: inline-block !important;
    margin-bottom: 0.25rem !important;
}
a.kpi-link:hover {
    color: var(--teal) !important;
    text-decoration-style: solid !important;
    text-decoration-color: var(--teal) !important;
}
a.kpi-link.alert { color: var(--red) !important; text-decoration-color: rgba(192,57,43,0.3) !important; }
a.kpi-link.alert:hover { color: #8B1E14 !important; }
a.kpi-link.warn  { color: var(--amber) !important; text-decoration-color: rgba(192,112,0,0.3) !important; }
a.kpi-link.warn:hover  { color: #8F5200 !important; }
a.kpi-link.ok    { color: var(--green) !important; text-decoration-color: rgba(26,107,58,0.3) !important; }
a.kpi-link.ok:hover    { color: #0E4023 !important; }

/* ── Invisible trigger button overlaid on the card ── */
.kpi-trigger-wrap {
    position: relative;
    margin-top: -5.5rem;  /* pull up to overlap the card */
    height: 5.5rem;
    overflow: hidden;
}
.kpi-trigger-wrap button {
    opacity: 0 !important;
    width: 100% !important;
    height: 100% !important;
    min-height: unset !important;
    cursor: pointer !important;
    position: absolute !important;
    top: 0 !important; left: 0 !important;
    border: none !important;
    background: transparent !important;
    z-index: 10 !important;
}
.kpi-click {
    font-size: 0.6rem; color: var(--teal);
    font-weight: 500; letter-spacing: 0.04em;
    margin-left: 0.25rem;
    display: none; /* number itself is now the link */
}
.kpi-sub { font-size: 0.65rem; color: var(--text-sm); margin-top: 0.3rem; }

/* ── Risk table ── */
.risk-table { width:100%; border-collapse:collapse; font-size:0.8rem; }
.risk-table th { font-size:0.63rem; font-weight:600; text-transform:uppercase; letter-spacing:0.06em; color:var(--text-sm); background:var(--bg); padding:0.5rem 0.65rem; text-align:left; border-bottom:1px solid var(--border); }
.risk-table td { padding:0.48rem 0.65rem; border-bottom:1px solid #EDF2F7; color:var(--text); vertical-align:middle; }
.risk-table tr:hover td { background:#F8FAFC; }

/* ── Pipeline strip ── */
.pipeline-row { display:flex; align-items:stretch; gap:0; margin:0.5rem 0; flex-wrap:wrap; }
.pipeline-stage { flex:1; min-width:80px; text-align:center; padding:0.6rem 0.4rem; border:1px solid var(--border); border-right:none; background:var(--white); font-size:0.72rem; }
.pipeline-stage:first-child { border-radius:4px 0 0 4px; }
.pipeline-stage:last-child  { border-right:1px solid var(--border); border-radius:0 4px 4px 0; }
.pipeline-count { font-size:1.4rem; font-weight:300; color:var(--navy); font-family:'IBM Plex Mono',monospace !important; display:block; }
.pipeline-label { font-size:0.62rem; color:var(--text-sm); text-transform:uppercase; letter-spacing:0.05em; }

/* ── Org / expiry rows ── */
.org-row { display:flex; align-items:center; padding:0.45rem 0; border-bottom:1px solid #EDF2F7; gap:0.6rem; font-size:0.78rem; }
.org-name { flex:1; color:var(--text); font-weight:500; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.org-bar-wrap { width:80px; min-width:80px; height:6px; background:#E2E8F0; border-radius:3px; overflow:hidden; }
.org-bar { height:100%; border-radius:3px; background:var(--teal); }
.org-bar.full { background:var(--amber); }
.org-count { font-size:0.68rem; color:var(--text-sm); width:45px; text-align:right; font-family:'IBM Plex Mono',monospace !important; }
.exp-row { display:flex; align-items:center; padding:0.4rem 0; border-bottom:1px solid #EDF2F7; gap:0.5rem; font-size:0.78rem; }
.exp-client { flex:1; font-weight:500; font-family:'IBM Plex Mono',monospace !important; font-size:0.73rem; }
.exp-date { font-size:0.7rem; color:var(--text-sm); }
.exp-days { font-family:'IBM Plex Mono',monospace !important; font-size:0.72rem; color:var(--amber); font-weight:600; min-width:24px; text-align:right; }
</style>
""", unsafe_allow_html=True)

# ══ DIALOGS ═══════════════════════════════════════════════════════════════════

@st.dialog("Active Clients", width="large")
def dialog_active_clients(clients_df):
    st.caption(f"{len(clients_df)} clients registered across all organizations")
    if clients_df.empty:
        st.info("No client data available."); return
    if "primary_org_id" in clients_df.columns:
        section_header("Clients by Organization")
        by_org = clients_df["primary_org_id"].value_counts().reset_index()
        by_org.columns = ["Organization", "Clients"]
        st.dataframe(by_org, use_container_width=True, hide_index=True)
        st.divider()
    section_header("All Clients")
    show = [c for c in ["client_id","first_name","last_name","primary_org_id",
                         "housing_status","assessment_acuity_level","bnl_status"]
            if c in clients_df.columns]
    st.dataframe(clients_df[show].reset_index(drop=True), use_container_width=True, hide_index=True)


@st.dialog("RED_FLAG Violations", width="large")
def dialog_red_flags(red_flags, encounters_on_expired):
    if red_flags.empty:
        pill("No RED_FLAG violations in the current dataset", "green")
    else:
        st.error(f"{len(red_flags)} consent violation(s) require immediate review")
        by_type = red_flags["flag_type"].value_counts()
        for flag, count in by_type.items():
            with st.expander(f"{flag} — {count} record(s)"):
                show = [c for c in ["client_id","consent_id","status","expiry_date","notes"]
                        if c in red_flags.columns]
                st.dataframe(red_flags[red_flags["flag_type"]==flag][show].reset_index(drop=True),
                             use_container_width=True, hide_index=True)
    if not encounters_on_expired.empty:
        st.divider()
        st.warning(f"{len(encounters_on_expired)} encounter(s) recorded after consent expiry")
        show = [c for c in ["client_id","encounter_id","encounter_start","expiry_date"]
                if c in encounters_on_expired.columns]
        st.dataframe(encounters_on_expired[show].reset_index(drop=True),
                     use_container_width=True, hide_index=True)
    st.divider()
    if st.button("Open Full Compliance Audit", type="primary", key="dlg_audit"):
        st.switch_page("pages/5_Compliance_Audit.py")


@st.dialog("Consent Expiring Soon", width="large")
def dialog_expiring(expiring_7, expiring_30, consent_df):
    active_count = len(consent_df[consent_df["status"]=="active"]) if not consent_df.empty else 0
    tab7, tab30, tab_all = st.tabs([
        f"≤ 7 days  ({len(expiring_7)})",
        f"≤ 30 days  ({len(expiring_30)})",
        f"All active  ({active_count})",
    ])
    show = [c for c in ["client_id","consent_id","expiry_date",
                         "sharing_scope_type","purpose_codes","collecting_org_id"]
            if c in expiring_7.columns]
    with tab7:
        if expiring_7.empty:
            pill("No consent expiring this week", "green")
        else:
            st.warning(f"{len(expiring_7)} client(s) need urgent renewal")
            st.dataframe(expiring_7[show].reset_index(drop=True), use_container_width=True, hide_index=True)
    with tab30:
        show30 = [c for c in show if c in expiring_30.columns]
        if expiring_30.empty:
            pill("No consent expiring within 30 days", "green")
        else:
            st.dataframe(expiring_30[show30].reset_index(drop=True), use_container_width=True, hide_index=True)
    with tab_all:
        if not consent_df.empty and "status" in consent_df.columns:
            active = consent_df[consent_df["status"]=="active"]
            st.caption(f"{len(active)} active consent records")
            show_a = [c for c in show if c in active.columns]
            st.dataframe(active[show_a].reset_index(drop=True), use_container_width=True, hide_index=True)
    st.divider()
    if st.button("Record New Consent", type="primary", key="dlg_consent"):
        st.switch_page("pages/4_Consent_Form.py")


@st.dialog("Stalled Referrals", width="large")
def dialog_stalled(stalled, referrals_df):
    if stalled.empty:
        pill("No stalled referrals", "green"); return
    stalled = stalled.copy()
    if "submitted_at" in stalled.columns:
        stalled["days_waiting"] = (pd.Timestamp.today() - stalled["submitted_at"]).dt.days.fillna(0).astype(int)
        stalled = stalled.sort_values("days_waiting", ascending=False)
    st.warning(f"{len(stalled)} referral(s) awaiting response — sorted by wait time")
    show = [c for c in ["client_id","referral_id","status","days_waiting",
                         "referral_type","receiving_org_id","priority","submitted_at"]
            if c in stalled.columns]
    st.dataframe(stalled[show].reset_index(drop=True), use_container_width=True, hide_index=True)
    st.divider()
    section_header("Full Pipeline Summary")
    if not referrals_df.empty and "status" in referrals_df.columns:
        pipeline = referrals_df["status"].value_counts().reset_index()
        pipeline.columns = ["Status", "Count"]
        st.dataframe(pipeline, use_container_width=True, hide_index=True)
    if st.button("New Referral", type="primary", key="dlg_referral"):
        st.switch_page("pages/7_New_Referral.py")


# ══ DATA ══════════════════════════════════════════════════════════════════════

@st.cache_data(show_spinner=False)
def get_tables():
    return {} if _STUB else load_tables()

tables     = get_tables()
caseworker = st.session_state.get("caseworker_name", "Caseworker")
org_id     = st.session_state.get("caseworker_org",  "ORG-001")
today_str  = date.today().strftime("%a %d %b %Y")

st.markdown(f"""
<div class="page-header">
  <div>
    <div class="page-header-title">Good morning, {caseworker}</div>
    <div class="page-header-sub">{org_id} &nbsp;·&nbsp; {today_str}</div>
  </div>
</div>
""", unsafe_allow_html=True)

if _STUB:
    st.warning("Stub mode — add CSVs to data/ and restart."); st.stop()

consent_df   = tables.get("consent",   pd.DataFrame())
referrals_df = tables.get("referrals", pd.DataFrame())
clients_df   = tables.get("clients",   pd.DataFrame())
orgs_df      = tables.get("orgs",      pd.DataFrame())

red_flags             = get_red_flags(tables)
expiring_7            = get_expiring_soon(tables, days=7)
expiring_30           = get_expiring_soon(tables, days=30)
encounters_on_expired = get_encounters_on_expired_consent(tables)

stalled = pd.DataFrame()
if not referrals_df.empty and "status" in referrals_df.columns:
    stalled = referrals_df[referrals_df["status"].isin(["submitted","acknowledged"])]

active_clients = len(clients_df)

with st.spinner("Computing risk scores…"):
    risk_df = compute_risk_for_all(tables)
at_risk = risk_df[risk_df["risk_level"].isin(["HIGH","MODERATE"])].head(15) \
          if not risk_df.empty else pd.DataFrame()

# ══ KPI BAR — 4 columns, styled card with HTML, button below the number ══════
# Pattern: HTML card label + big number + "tap to open" hint, then
# a transparent Streamlit button overlapping it for the click event.

# KPI render helper below
k1, k2, k3, k4 = st.columns(4)

RF_CLS  = "alert" if len(red_flags) > 0 else "ok"
EXP_CLS = "warn"  if len(expiring_7) > 0 else "ok"
STL_CLS = "warn"  if len(stalled) > 10  else "ok"

def render_kpi(col, label, value, sub, val_cls, btn_key, dialog_fn, *args):
    """
    KPI card: fully in HTML with a real <a> tag for the number.
    An invisible overlaid Streamlit button intercepts the click to open
    the st.dialog. This gives a perfect visual with native link behaviour.
    """
    with col:
        # Full card in HTML — number is a real <a> hyperlink
        st.markdown(f"""
        <div class="kpi-card {val_cls}">
          <div class="kpi-lbl">{label}</div>
          <a class="kpi-link {val_cls}" href="#" onclick="return false;"
             title="View {label} detail">{value}</a>
          <div class="kpi-sub">{sub}</div>
        </div>
        """, unsafe_allow_html=True)

        # Invisible button overlaid on the card — intercepts click → opens dialog
        st.markdown('<div class="kpi-trigger-wrap">', unsafe_allow_html=True)
        if st.button(" ", key=btn_key, help=f"View {label} detail",
                     use_container_width=True):
            dialog_fn(*args)
        st.markdown('</div>', unsafe_allow_html=True)

render_kpi(k1, "Active Clients",       active_clients,  "across all orgs",          "",      "kpi_clients",  dialog_active_clients, clients_df)
render_kpi(k2, "RED_FLAG Violations",  len(red_flags),  "require immediate action",  RF_CLS, "kpi_flags",    dialog_red_flags,       red_flags, encounters_on_expired)
render_kpi(k3, "Consent Expiring ≤7d", len(expiring_7), f"{len(expiring_30)} ≤30d",  EXP_CLS,"kpi_expiring", dialog_expiring,        expiring_7, expiring_30, consent_df)
render_kpi(k4, "Stalled Referrals",    len(stalled),    "awaiting response",          STL_CLS,"kpi_stalled",  dialog_stalled,         stalled, referrals_df)

st.divider()

# ══ TWO-COLUMN BODY ═══════════════════════════════════════════════════════════
col_left, col_right = st.columns([3, 2], gap="medium")

with col_left:

    # Consent Alerts
    section_header("Consent Alerts")
    if red_flags.empty:
        st.markdown('<div class="pill pill-green">No active RED_FLAG violations</div>', unsafe_allow_html=True)
    else:
        by_type = red_flags["flag_type"].value_counts()
        for flag_type, count in by_type.items():
            st.markdown(f'<div class="pill pill-red">{flag_type} &nbsp;— {count} record(s)</div>', unsafe_allow_html=True)
        if st.button("View Full Compliance Audit →", type="primary", key="btn_audit"):
            st.switch_page("pages/5_Compliance_Audit.py")
    if not expiring_7.empty:
        st.markdown(f'<div class="pill pill-amber">{len(expiring_7)} client(s) — consent expiring within 7 days</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # At-Risk Priority List
    section_header("At-Risk Clients — Priority List")
    if at_risk.empty:
        st.markdown('<div class="pill pill-green">No high or moderate risk clients</div>', unsafe_allow_html=True)
    else:
        rows_html = ""
        for i, (_, row) in enumerate(at_risk.iterrows(), 1):
            level  = row["risk_level"]
            bcls   = "badge-high" if level=="HIGH" else "badge-mod"
            signal = str(row["top_signal"])[:48]
            rows_html += f"""
            <tr>
              <td style="color:#64748B;font-family:'IBM Plex Mono',monospace;font-size:0.65rem">{i}</td>
              <td style="font-weight:500">{row['full_name']}</td>
              <td><span class="badge {bcls}">{level}</span></td>
              <td style="font-family:'IBM Plex Mono',monospace">{row['risk_score']}/15</td>
              <td style="color:#64748B;font-size:0.75rem">{signal}</td>
            </tr>"""
        st.markdown(f"""
        <table class="risk-table">
          <thead><tr><th>#</th><th>Client</th><th>Risk</th><th>Score</th><th>Top Signal</th></tr></thead>
          <tbody>{rows_html}</tbody>
        </table>""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        sel = st.selectbox("Open profile:", ["— select —"] + at_risk["full_name"].tolist(),
                           label_visibility="collapsed", key="risk_select")
        if sel != "— select —":
            match = at_risk[at_risk["full_name"]==sel]
            if not match.empty:
                st.session_state["selected_client_id"] = match.iloc[0]["client_id"]
                st.switch_page("pages/3_Client_Profile.py")

    st.markdown("<br>", unsafe_allow_html=True)

    # Referral Pipeline
    section_header("Referral Pipeline")
    stages = [("submitted","Submitted"),("acknowledged","Acknowledged"),
              ("accepted","Accepted"),("in_progress","In Progress"),("completed","Completed")]
    counts = {s: (len(referrals_df[referrals_df["status"]==s])
                  if not referrals_df.empty and "status" in referrals_df.columns else 0)
              for s,_ in stages}
    stage_html = "".join(
        f'<div class="pipeline-stage"><span class="pipeline-count">{counts[s]}</span>'
        f'<span class="pipeline-label">{l}</span></div>' for s,l in stages)
    st.markdown(f'<div class="pipeline-row">{stage_html}</div>', unsafe_allow_html=True)


with col_right:

    # Expiring Consent
    section_header("Expiring Consent")
    if expiring_7.empty:
        st.markdown('<div class="pill pill-green">None expiring this week</div>', unsafe_allow_html=True)
    else:
        exp_html = ""
        for _, row in expiring_7.head(8).iterrows():
            cid = row.get("client_id","")
            exp = row.get("expiry_date")
            exp_str = str(exp)[:10] if exp is not None else "—"
            try:
                days_left = (pd.to_datetime(exp).date() - date.today()).days
                days_str  = f"{days_left}d"
            except Exception:
                days_str = "—"
            exp_html += (f'<div class="exp-row">'
                         f'<span class="exp-client">{cid}</span>'
                         f'<span class="exp-date">{exp_str}</span>'
                         f'<span class="exp-days">{days_str}</span>'
                         f'</div>')
        st.markdown(exp_html, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Org Capacity
    section_header("Org Capacity")
    if not orgs_df.empty:
        org_html = ""
        for _, org in orgs_df.head(9).iterrows():
            name  = str(org.get("org_name", org.get("name","—")))[:22]
            total = int(org.get("capacity_total_slots",0) or 0)
            occ   = int(org.get("capacity_occupied_slots",0) or 0)
            if total > 0:
                pct     = min(int(occ/total*100), 100)
                free    = total - occ
                bar_cls = "full" if pct >= 85 else ""
                org_html += (f'<div class="org-row">'
                             f'<span class="org-name">{name}</span>'
                             f'<div class="org-bar-wrap"><div class="org-bar {bar_cls}" style="width:{pct}%"></div></div>'
                             f'<span class="org-count">{free} free</span>'
                             f'</div>')
        if org_html:
            st.markdown(org_html, unsafe_allow_html=True)
        else:
            st.markdown('<div style="font-size:0.78rem;color:#64748B">No capacity data.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="font-size:0.78rem;color:#64748B">No org data.</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Quick Actions
    section_header("Quick Actions")
    if st.button("Search Clients",   use_container_width=True, key="qa_search"):
        st.switch_page("pages/2_Client_Search.py")
    if st.button("Record Consent",   use_container_width=True, key="qa_consent"):
        st.switch_page("pages/4_Consent_Form.py")
    if st.button("New Referral",     use_container_width=True, key="qa_referral"):
        st.switch_page("pages/7_New_Referral.py")
    if st.button("Compliance Audit", use_container_width=True, key="qa_audit"):
        st.switch_page("pages/5_Compliance_Audit.py")

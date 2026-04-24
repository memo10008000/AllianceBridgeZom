"""
pages/1_Dashboard.py  —  SCR-01  Morning Briefing
KPI numbers are clickable — open st.dialog popups with full detail.
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

# ── Extra CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── KPI clickable cards ── */
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
    position: relative;
}
.kpi-card.alert  { border-left-color: var(--red); }
.kpi-card.warn   { border-left-color: var(--amber); }
.kpi-card.ok     { border-left-color: var(--green); }
.kpi-label {
    font-size: 0.65rem; font-weight: 500; color: var(--text-sm);
    text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.2rem;
}
.kpi-value {
    font-size: 1.85rem; font-weight: 300; color: var(--navy);
    line-height: 1; font-family: 'IBM Plex Mono', monospace !important;
}
.kpi-value.alert { color: var(--red); }
.kpi-value.warn  { color: var(--amber); }
.kpi-value.ok    { color: var(--green); }
.kpi-sub { font-size: 0.65rem; color: var(--text-sm); margin-top: 0.2rem; }

/* Make KPI buttons look like the value number */
div[data-testid="stButton"] > button.kpi-btn {
    all: unset;
    cursor: pointer;
    display: block;
}

/* ── KPI button override — make value look clickable ── */
.kpi-number-btn button {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    font-size: 1.85rem !important;
    font-weight: 300 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    line-height: 1 !important;
    color: var(--navy) !important;
    cursor: pointer !important;
    text-decoration: underline dotted !important;
    text-underline-offset: 3px !important;
    min-height: unset !important;
    height: auto !important;
    width: auto !important;
    box-shadow: none !important;
    border-radius: 0 !important;
}
.kpi-number-btn button:hover {
    color: var(--teal) !important;
    text-decoration: underline solid !important;
}
.kpi-number-btn.alert button { color: var(--red) !important; }
.kpi-number-btn.alert button:hover { color: #9B1E14 !important; }
.kpi-number-btn.warn  button { color: var(--amber) !important; }
.kpi-number-btn.warn  button:hover { color: #8F5200 !important; }
.kpi-number-btn.ok    button { color: var(--green) !important; }

/* ── Dialog styling ── */
div[data-testid="stModal"] {
    backdrop-filter: blur(2px) !important;
}
div[data-testid="stModal"] > div {
    max-width: 720px !important;
    border-radius: 8px !important;
}

/* ── Page header ── */
.page-header {
    display: flex; align-items: baseline; justify-content: space-between;
    margin-bottom: 1.25rem; padding-bottom: 0.75rem;
    border-bottom: 2px solid var(--navy);
}
.page-header-title { font-size: 1.3rem; font-weight: 600; color: var(--navy); }
.page-header-sub   { font-size: 0.75rem; color: var(--text-sm); font-family: 'IBM Plex Mono', monospace !important; }

/* Risk table */
.risk-table { width:100%; border-collapse:collapse; font-size:0.8rem; }
.risk-table th { font-size:0.63rem; font-weight:600; text-transform:uppercase; letter-spacing:0.06em; color:var(--text-sm); background:var(--bg); padding:0.5rem 0.65rem; text-align:left; border-bottom:1px solid var(--border); }
.risk-table td { padding:0.48rem 0.65rem; border-bottom:1px solid #EDF2F7; color:var(--text); vertical-align:middle; }
.risk-table tr:hover td { background:#F8FAFC; }

/* Pipeline */
.pipeline-row { display:flex; align-items:stretch; gap:0; margin:0.5rem 0; }
.pipeline-stage { flex:1; text-align:center; padding:0.6rem 0.4rem; border:1px solid var(--border); border-right:none; background:var(--white); font-size:0.72rem; }
.pipeline-stage:first-child { border-radius:4px 0 0 4px; }
.pipeline-stage:last-child  { border-right:1px solid var(--border); border-radius:0 4px 4px 0; }
.pipeline-count { font-size:1.4rem; font-weight:300; color:var(--navy); font-family:'IBM Plex Mono',monospace !important; display:block; }
.pipeline-label { font-size:0.62rem; color:var(--text-sm); text-transform:uppercase; letter-spacing:0.05em; }

/* Org capacity */
.org-row { display:flex; align-items:center; padding:0.45rem 0; border-bottom:1px solid #EDF2F7; gap:0.6rem; font-size:0.78rem; }
.org-name { flex:1; color:var(--text); font-weight:500; }
.org-bar-wrap { width:80px; height:6px; background:#E2E8F0; border-radius:3px; overflow:hidden; }
.org-bar { height:100%; border-radius:3px; background:var(--teal); }
.org-bar.full { background:var(--amber); }
.org-count { font-size:0.68rem; color:var(--text-sm); width:45px; text-align:right; font-family:'IBM Plex Mono',monospace !important; }

/* Exp row */
.exp-row { display:flex; align-items:center; padding:0.4rem 0; border-bottom:1px solid #EDF2F7; gap:0.5rem; font-size:0.78rem; }
.exp-client { flex:1; font-weight:500; }
.exp-days { font-family:'IBM Plex Mono',monospace !important; font-size:0.72rem; color:var(--amber); font-weight:600; }
</style>
""", unsafe_allow_html=True)

# ── Dialogs ───────────────────────────────────────────────────────────────────
@st.dialog("Active Clients", width="large")
def dialog_active_clients(clients_df):
    st.caption(f"{len(clients_df)} clients registered across all organizations")
    if clients_df.empty:
        st.info("No client data available."); return

    show_cols = [c for c in ["client_id","first_name","last_name",
                              "primary_org_id","housing_status",
                              "assessment_acuity_level","bnl_status"]
                 if c in clients_df.columns]
    # Summary by org
    if "primary_org_id" in clients_df.columns:
        section_header("Clients by Organization")
        by_org = clients_df["primary_org_id"].value_counts().reset_index()
        by_org.columns = ["Organization", "Clients"]
        st.dataframe(by_org, use_container_width=True, hide_index=True)
        st.divider()

    section_header("All Clients")
    st.dataframe(
        clients_df[show_cols].reset_index(drop=True),
        use_container_width=True, hide_index=True,
    )


@st.dialog("RED_FLAG Violations", width="large")
def dialog_red_flags(red_flags, encounters_on_expired):
    if red_flags.empty:
        pill("No RED_FLAG violations in the current dataset", "green")
    else:
        st.error(f"{len(red_flags)} consent violation(s) require immediate review")
        by_type = red_flags["flag_type"].value_counts()
        for flag, count in by_type.items():
            with st.expander(f"{flag} — {count} record(s)"):
                show_cols = [c for c in ["client_id","consent_id","status",
                                          "expiry_date","notes"]
                             if c in red_flags.columns]
                st.dataframe(
                    red_flags[red_flags["flag_type"]==flag][show_cols]
                    .reset_index(drop=True),
                    use_container_width=True, hide_index=True,
                )

    if not encounters_on_expired.empty:
        st.divider()
        st.warning(f"{len(encounters_on_expired)} encounter(s) recorded after consent expiry")
        show_cols = [c for c in ["client_id","encounter_id","encounter_start","expiry_date"]
                     if c in encounters_on_expired.columns]
        st.dataframe(encounters_on_expired[show_cols].reset_index(drop=True),
                     use_container_width=True, hide_index=True)

    st.divider()
    if st.button("Open Full Compliance Audit →", type="primary"):
        st.switch_page("pages/5_Compliance_Audit.py")


@st.dialog("Consent Expiring Soon", width="large")
def dialog_expiring(expiring_7, expiring_30, consent_df):
    tab7, tab30, tab_all = st.tabs([
        f"Expiring in 7 days  ({len(expiring_7)})",
        f"Expiring in 30 days  ({len(expiring_30)})",
        f"All active consent  ({len(consent_df[consent_df['status']=='active']) if not consent_df.empty else 0})",
    ])

    show_cols = [c for c in ["client_id","consent_id","expiry_date",
                              "sharing_scope_type","purpose_codes","collecting_org_id"]
                 if c in expiring_7.columns]

    with tab7:
        if expiring_7.empty:
            pill("No consent expiring this week", "green")
        else:
            st.warning(f"{len(expiring_7)} client(s) need urgent renewal before data access is blocked")
            st.dataframe(expiring_7[show_cols].reset_index(drop=True),
                         use_container_width=True, hide_index=True)

    with tab30:
        show_cols30 = [c for c in show_cols if c in expiring_30.columns]
        if expiring_30.empty:
            pill("No consent expiring within 30 days", "green")
        else:
            st.dataframe(expiring_30[show_cols30].reset_index(drop=True),
                         use_container_width=True, hide_index=True)

    with tab_all:
        if consent_df.empty:
            st.info("No consent data."); return
        active = consent_df[consent_df["status"]=="active"] if "status" in consent_df.columns else consent_df
        st.caption(f"{len(active)} active consent records")
        st.dataframe(active[show_cols30].reset_index(drop=True),
                     use_container_width=True, hide_index=True)

    st.divider()
    if st.button("Record New Consent →", type="primary"):
        st.switch_page("pages/4_Consent_Form.py")


@st.dialog("Stalled Referrals", width="large")
def dialog_stalled(stalled, referrals_df):
    st.warning(f"{len(stalled)} referral(s) awaiting acknowledgment or acceptance")

    if stalled.empty:
        pill("No stalled referrals", "green"); return

    # Days stalled per referral
    if "submitted_at" in stalled.columns:
        stalled = stalled.copy()
        stalled["days_waiting"] = (
            pd.Timestamp.today() - stalled["submitted_at"]
        ).dt.days.fillna(0).astype(int)
        stalled = stalled.sort_values("days_waiting", ascending=False)

    show_cols = [c for c in ["client_id","referral_id","status","days_waiting",
                              "referral_type","receiving_org_id","priority","submitted_at"]
                 if c in stalled.columns]
    st.dataframe(stalled[show_cols].reset_index(drop=True),
                 use_container_width=True, hide_index=True)

    st.divider()
    section_header("Full Pipeline Summary")
    if not referrals_df.empty and "status" in referrals_df.columns:
        pipeline = referrals_df["status"].value_counts().reset_index()
        pipeline.columns = ["Status", "Count"]
        st.dataframe(pipeline, use_container_width=True, hide_index=True)

    if st.button("New Referral →", type="primary"):
        st.switch_page("pages/7_New_Referral.py")


# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def get_tables():
    return {} if _STUB else load_tables()

tables      = get_tables()
caseworker  = st.session_state.get("caseworker_name", "Caseworker")
org_id      = st.session_state.get("caseworker_org",  "ORG-001")
today_str   = date.today().strftime("%a %d %b %Y")

# ── Page header ───────────────────────────────────────────────────────────────
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

consent_df    = tables.get("consent",    pd.DataFrame())
referrals_df  = tables.get("referrals",  pd.DataFrame())
clients_df    = tables.get("clients",    pd.DataFrame())
orgs_df       = tables.get("orgs",       pd.DataFrame())

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

# ── KPI bar — 4 columns, each with label + clickable number + sub ─────────────
k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown('<div class="kpi-card"><div class="kpi-label">Active Clients</div>', unsafe_allow_html=True)
    st.markdown('<div class="kpi-number-btn">', unsafe_allow_html=True)
    if st.button(str(active_clients), key="kpi_clients", help="Click to view all clients"):
        dialog_active_clients(clients_df)
    st.markdown('</div><div class="kpi-sub">across all orgs</div></div>', unsafe_allow_html=True)

with k2:
    cls = "alert" if len(red_flags) > 0 else "ok"
    st.markdown(f'<div class="kpi-card {cls}"><div class="kpi-label">RED_FLAG Violations</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="kpi-number-btn {cls}">', unsafe_allow_html=True)
    if st.button(str(len(red_flags)), key="kpi_flags", help="Click to view violations"):
        dialog_red_flags(red_flags, encounters_on_expired)
    st.markdown('</div><div class="kpi-sub">require immediate action</div></div>', unsafe_allow_html=True)

with k3:
    cls = "warn" if len(expiring_7) > 0 else "ok"
    st.markdown(f'<div class="kpi-card {cls}"><div class="kpi-label">Consent Expiring ≤7d</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="kpi-number-btn {cls}">', unsafe_allow_html=True)
    if st.button(str(len(expiring_7)), key="kpi_expiring", help="Click to view expiring consent"):
        dialog_expiring(expiring_7, expiring_30, consent_df)
    st.markdown(f'</div><div class="kpi-sub">{len(expiring_30)} expiring ≤30d</div></div>', unsafe_allow_html=True)

with k4:
    cls = "warn" if len(stalled) > 10 else "ok"
    st.markdown(f'<div class="kpi-card {cls}"><div class="kpi-label">Stalled Referrals</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="kpi-number-btn {cls}">', unsafe_allow_html=True)
    if st.button(str(len(stalled)), key="kpi_stalled", help="Click to view stalled referrals"):
        dialog_stalled(stalled, referrals_df)
    st.markdown('</div><div class="kpi-sub">awaiting response</div></div>', unsafe_allow_html=True)

st.divider()

# ── Two-column body ───────────────────────────────────────────────────────────
col_left, col_right = st.columns([3, 2], gap="medium")

with col_left:
    # Consent Alerts
    section_header("Consent Alerts")
    if red_flags.empty:
        st.markdown('<div class="pill pill-green">No active RED_FLAG violations</div>', unsafe_allow_html=True)
    else:
        by_type = red_flags["flag_type"].value_counts()
        for flag_type, count in by_type.items():
            st.markdown(f'<div class="pill pill-red">{flag_type} &nbsp;— {count} record(s)</div>',
                        unsafe_allow_html=True)
        if st.button("View Full Compliance Audit →", type="primary", key="btn_audit"):
            st.switch_page("pages/5_Compliance_Audit.py")

    if not expiring_7.empty:
        st.markdown(
            f'<div class="pill pill-amber">{len(expiring_7)} client(s) — consent expiring within 7 days</div>',
            unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # At-Risk list
    section_header("At-Risk Clients — Priority List")
    if at_risk.empty:
        st.markdown('<div class="pill pill-green">No high or moderate risk clients</div>', unsafe_allow_html=True)
    else:
        rows_html = ""
        for i, (_, row) in enumerate(at_risk.iterrows(), 1):
            level   = row["risk_level"]
            bcls    = "badge-high" if level=="HIGH" else "badge-mod"
            signal  = str(row["top_signal"])[:48]
            name    = str(row["full_name"])
            rows_html += f"""
            <tr>
              <td style="color:#64748B;font-family:'IBM Plex Mono',monospace;font-size:0.65rem">{i}</td>
              <td style="font-weight:500">{name}</td>
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
        sel = st.selectbox(
            "Open profile:", ["— select —"] + at_risk["full_name"].tolist(),
            label_visibility="collapsed", key="risk_select",
        )
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
    counts = {s: len(referrals_df[referrals_df["status"]==s])
              if not referrals_df.empty and "status" in referrals_df.columns else 0
              for s, _ in stages}
    stage_html = "".join(
        f'<div class="pipeline-stage"><span class="pipeline-count">{counts[s]}</span>'
        f'<span class="pipeline-label">{l}</span></div>'
        for s, l in stages
    )
    st.markdown(f'<div class="pipeline-row">{stage_html}</div>', unsafe_allow_html=True)

with col_right:
    # Expiring consent list
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
                days_str = f"{days_left}d"
            except Exception:
                days_str = "—"
            exp_html += f'<div class="exp-row"><span class="exp-client">{cid}</span><span style="font-size:0.7rem;color:#64748B">{exp_str}</span><span class="exp-days">{days_str}</span></div>'
        st.markdown(exp_html, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Org capacity
    section_header("Org Capacity")
    if orgs_df.empty:
        st.markdown('<div style="font-size:0.78rem;color:#64748B">No org data.</div>', unsafe_allow_html=True)
    else:
        org_html = ""
        for _, org in orgs_df.head(9).iterrows():
            name  = str(org.get("org_name", org.get("name","—")))[:22]
            total = int(org.get("capacity_total_slots",0) or 0)
            occ   = int(org.get("capacity_occupied_slots",0) or 0)
            if total > 0:
                pct = min(int(occ/total*100), 100)
                free = total - occ
                bar_cls = "full" if pct >= 85 else ""
                org_html += f'<div class="org-row"><span class="org-name">{name}</span><div class="org-bar-wrap"><div class="org-bar {bar_cls}" style="width:{pct}%"></div></div><span class="org-count">{free} free</span></div>'
        if org_html:
            st.markdown(org_html, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Quick actions
    section_header("Quick Actions")
    if st.button("Search Clients",    use_container_width=True, key="qa_search"):
        st.switch_page("pages/2_Client_Search.py")
    if st.button("Record Consent",    use_container_width=True, key="qa_consent"):
        st.switch_page("pages/4_Consent_Form.py")
    if st.button("New Referral",      use_container_width=True, key="qa_referral"):
        st.switch_page("pages/7_New_Referral.py")
    if st.button("Compliance Audit",  use_container_width=True, key="qa_audit"):
        st.switch_page("pages/5_Compliance_Audit.py")

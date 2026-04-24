"""
pages/1_Dashboard.py  —  SCR-01  Morning Briefing
KPI cards: each card is one st.button styled with CSS to look exactly
like a professional metric card — label, big number, sub text.
No HTML wrappers, no overlay tricks, no query params.
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
/* ═══ KPI CARD BUTTONS ═══════════════════════════════════════════════════════
   Each KPI card is ONE st.button. CSS makes it look like a metric card.
   The button label contains three lines separated by \\n rendered as HTML.
═══════════════════════════════════════════════════════════════════════════ */

/* Wrapper div that Streamlit puts around each button */
div[data-testid="stButton"].kpi-default > button,
div[data-testid="stButton"].kpi-alert   > button,
div[data-testid="stButton"].kpi-warn    > button,
div[data-testid="stButton"].kpi-ok      > button {
    /* Card shape */
    width: 100% !important;
    height: auto !important;
    min-height: unset !important;
    text-align: left !important;
    padding: 0.9rem 1rem 0.8rem 1rem !important;
    border-radius: 6px !important;
    border: 1px solid var(--border) !important;
    border-left-width: 3px !important;
    box-shadow: none !important;
    cursor: pointer !important;
    transition: box-shadow 0.15s, transform 0.1s !important;
    /* Reset Streamlit defaults */
    background: var(--white) !important;
    display: flex !important;
    flex-direction: column !important;
    gap: 0 !important;
    white-space: pre-wrap !important;
    line-height: 1.2 !important;
}
div[data-testid="stButton"].kpi-default > button { border-left-color: var(--navy) !important; }
div[data-testid="stButton"].kpi-alert   > button { border-left-color: var(--red)   !important; }
div[data-testid="stButton"].kpi-warn    > button { border-left-color: var(--amber) !important; }
div[data-testid="stButton"].kpi-ok      > button { border-left-color: var(--green) !important; }

/* Hover */
div[data-testid="stButton"].kpi-default > button:hover,
div[data-testid="stButton"].kpi-alert   > button:hover,
div[data-testid="stButton"].kpi-warn    > button:hover,
div[data-testid="stButton"].kpi-ok      > button:hover {
    box-shadow: 0 3px 12px rgba(15,41,66,0.12) !important;
    transform: translateY(-1px) !important;
}
div[data-testid="stButton"].kpi-default > button:active,
div[data-testid="stButton"].kpi-alert   > button:active,
div[data-testid="stButton"].kpi-warn    > button:active,
div[data-testid="stButton"].kpi-ok      > button:active {
    transform: translateY(0) !important;
}

/* ── The label text inside the button ── */
/* Streamlit wraps button text in <p> tags */
div[data-testid="stButton"].kpi-default > button p,
div[data-testid="stButton"].kpi-alert   > button p,
div[data-testid="stButton"].kpi-warn    > button p,
div[data-testid="stButton"].kpi-ok      > button p {
    margin: 0 !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    text-align: left !important;
}

/* ── KPI label line (first line in button text) ── */
div[data-testid="stButton"].kpi-default > button p:first-child,
div[data-testid="stButton"].kpi-alert   > button p:first-child,
div[data-testid="stButton"].kpi-warn    > button p:first-child,
div[data-testid="stButton"].kpi-ok      > button p:first-child {
    font-size: 0.62rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
    color: var(--text-sm) !important;
    margin-bottom: 0.3rem !important;
}

/* Use :has for the card label */
.kpi-label-txt {
    font-size: 0.62rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
    color: var(--text-sm) !important;
    display: block !important;
    margin-bottom: 0.3rem !important;
}
.kpi-value-txt {
    font-size: 2.1rem !important;
    font-weight: 300 !important;
    line-height: 1 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    display: block !important;
    margin-bottom: 0.3rem !important;
    text-decoration: underline dotted !important;
    text-underline-offset: 4px !important;
}
.kpi-sub-txt {
    font-size: 0.63rem !important;
    color: var(--text-sm) !important;
    display: block !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
}

/* Colour variants for value */
.kpi-default .kpi-value-txt { color: var(--navy) !important;
    text-decoration-color: rgba(15,41,66,0.3) !important; }
.kpi-alert   .kpi-value-txt { color: var(--red)   !important;
    text-decoration-color: rgba(192,57,43,0.3) !important; }
.kpi-warn    .kpi-value-txt { color: var(--amber) !important;
    text-decoration-color: rgba(192,112,0,0.3) !important; }
.kpi-ok      .kpi-value-txt { color: var(--green) !important;
    text-decoration-color: rgba(26,107,58,0.3) !important; }

/* Hover changes value colour to teal */
div[data-testid="stButton"].kpi-default > button:hover .kpi-value-txt,
div[data-testid="stButton"].kpi-alert   > button:hover .kpi-value-txt,
div[data-testid="stButton"].kpi-warn    > button:hover .kpi-value-txt,
div[data-testid="stButton"].kpi-ok      > button:hover .kpi-value-txt {
    color: var(--teal) !important;
    text-decoration-style: solid !important;
    text-decoration-color: var(--teal) !important;
}

/* ── Page header ── */
.page-header {
    display: flex; align-items: baseline; justify-content: space-between;
    margin-bottom: 1.25rem; padding-bottom: 0.75rem;
    border-bottom: 2px solid var(--navy);
}
.page-header-title { font-size: 1.3rem; font-weight: 600; color: var(--navy); }
.page-header-sub   { font-size: 0.75rem; color: var(--text-sm);
                     font-family: 'IBM Plex Mono', monospace !important; }

/* ── Risk table ── */
.risk-table { width:100%; border-collapse:collapse; font-size:0.8rem; }
.risk-table th { font-size:0.63rem; font-weight:600; text-transform:uppercase;
    letter-spacing:0.06em; color:var(--text-sm); background:var(--bg);
    padding:0.5rem 0.65rem; text-align:left; border-bottom:1px solid var(--border); }
.risk-table td { padding:0.48rem 0.65rem; border-bottom:1px solid #EDF2F7;
    color:var(--text); vertical-align:middle; }
.risk-table tr:hover td { background:#F8FAFC; }

/* ── Pipeline strip ── */
.pipeline-row { display:flex; align-items:stretch; gap:0; margin:0.5rem 0; flex-wrap:wrap; }
.pipeline-stage { flex:1; min-width:80px; text-align:center; padding:0.6rem 0.4rem;
    border:1px solid var(--border); border-right:none; background:var(--white); font-size:0.72rem; }
.pipeline-stage:first-child { border-radius:4px 0 0 4px; }
.pipeline-stage:last-child  { border-right:1px solid var(--border); border-radius:0 4px 4px 0; }
.pipeline-count { font-size:1.4rem; font-weight:300; color:var(--navy);
    font-family:'IBM Plex Mono',monospace !important; display:block; }
.pipeline-label { font-size:0.62rem; color:var(--text-sm); text-transform:uppercase; letter-spacing:0.05em; }

/* ── Org / expiry rows ── */
.org-row { display:flex; align-items:center; padding:0.45rem 0;
    border-bottom:1px solid #EDF2F7; gap:0.6rem; font-size:0.78rem; }
.org-name { flex:1; color:var(--text); font-weight:500; overflow:hidden;
    text-overflow:ellipsis; white-space:nowrap; }
.org-bar-wrap { width:80px; min-width:80px; height:6px; background:#E2E8F0;
    border-radius:3px; overflow:hidden; }
.org-bar { height:100%; border-radius:3px; background:var(--teal); }
.org-bar.full { background:var(--amber); }
.org-count { font-size:0.68rem; color:var(--text-sm); width:45px; text-align:right;
    font-family:'IBM Plex Mono',monospace !important; }
.exp-row { display:flex; align-items:center; padding:0.4rem 0;
    border-bottom:1px solid #EDF2F7; gap:0.5rem; font-size:0.78rem; }
.exp-client { flex:1; font-weight:500; font-family:'IBM Plex Mono',monospace !important; font-size:0.73rem; }
.exp-date { font-size:0.7rem; color:var(--text-sm); }
.exp-days { font-family:'IBM Plex Mono',monospace !important; font-size:0.72rem;
    color:var(--amber); font-weight:600; min-width:24px; text-align:right; }
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
                st.dataframe(red_flags[red_flags["flag_type"]==flag][show]
                             .reset_index(drop=True), use_container_width=True, hide_index=True)
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
    active_count = len(consent_df[consent_df["status"]=="active"]) \
                   if not consent_df.empty and "status" in consent_df.columns else 0
    tab7, tab30, tab_all = st.tabs([
        f"7 days  ({len(expiring_7)})",
        f"30 days  ({len(expiring_30)})",
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
            st.dataframe(expiring_7[show].reset_index(drop=True),
                         use_container_width=True, hide_index=True)
    with tab30:
        show30 = [c for c in show if c in expiring_30.columns]
        if expiring_30.empty:
            pill("No consent expiring within 30 days", "green")
        else:
            st.dataframe(expiring_30[show30].reset_index(drop=True),
                         use_container_width=True, hide_index=True)
    with tab_all:
        if not consent_df.empty and "status" in consent_df.columns:
            active = consent_df[consent_df["status"]=="active"]
            show_a = [c for c in show if c in active.columns]
            st.dataframe(active[show_a].reset_index(drop=True),
                         use_container_width=True, hide_index=True)
    st.divider()
    if st.button("Record New Consent", type="primary", key="dlg_consent"):
        st.switch_page("pages/4_Consent_Form.py")


@st.dialog("Stalled Referrals", width="large")
def dialog_stalled(stalled, referrals_df):
    if stalled.empty:
        pill("No stalled referrals", "green"); return
    stalled = stalled.copy()
    if "submitted_at" in stalled.columns:
        stalled["days_waiting"] = (
            pd.Timestamp.today() - stalled["submitted_at"]
        ).dt.days.fillna(0).astype(int)
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

# REQUIRED for Client Search bugfix: explicitly set current page
st.session_state["current_page"] = "dashboard"

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

# Active Clients KPI: filtered to caseworker's org
org_clients = clients_df[
    clients_df["primary_org_id"] == org_id
] if not clients_df.empty and "primary_org_id" in clients_df.columns else clients_df
active_clients = len(org_clients)

with st.spinner("Computing risk scores…"):
    risk_df = compute_risk_for_all(tables)
at_risk = risk_df[risk_df["risk_level"].isin(["HIGH","MODERATE"])].head(15) \
          if not risk_df.empty else pd.DataFrame()

# ══ KPI CARDS ═════════════════════════════════════════════════════════════════
# Each card is ONE st.button with an HTML label.
# The CSS class on the wrapper div controls the card's colour accent.
# Clicking anywhere on the card opens the dialog.

def kpi_card(col, css_cls, label, value, sub, btn_key, dialog_fn, *dialog_args):
    """
    KPI card: pure HTML for the visual card, transparent Streamlit button
    placed immediately below to handle click → opens st.dialog.
    This is the only approach that preserves the original big-number design.
    """
    accent = (
        "var(--red)"   if css_cls == "kpi-alert" else
        "var(--amber)" if css_cls == "kpi-warn"  else
        "var(--green)" if css_cls == "kpi-ok"    else
        "var(--navy)"
    )
    dec_color = (
        "rgba(192,57,43,0.3)"  if css_cls == "kpi-alert" else
        "rgba(192,112,0,0.3)"  if css_cls == "kpi-warn"  else
        "rgba(26,107,58,0.3)"  if css_cls == "kpi-ok"    else
        "rgba(15,41,66,0.3)"
    )
    with col:
        # Pure HTML card — big number renders correctly
        st.markdown(f"""
        <div style="
            background:var(--white);
            border:1px solid var(--border);
            border-left:3px solid {accent};
            border-radius:6px;
            padding:0.85rem 1rem 0.75rem 1rem;
        ">
          <div style="font-size:0.62rem;font-weight:600;text-transform:uppercase;
                      letter-spacing:0.07em;color:var(--text-sm);
                      font-family:'IBM Plex Sans',sans-serif;
                      margin-bottom:0.3rem">{label}</div>
          <div style="font-size:2.1rem;font-weight:300;line-height:1;
                      font-family:'IBM Plex Mono',monospace;color:{accent};
                      text-decoration:underline dotted;
                      text-decoration-color:{dec_color};
                      text-underline-offset:4px;
                      margin-bottom:0.25rem">{value}</div>
          <div style="font-size:0.63rem;color:var(--text-sm);
                      font-family:'IBM Plex Sans',sans-serif">{sub}</div>
        </div>
        """, unsafe_allow_html=True)

        # Transparent button — zero-height, z-index covers the card above
        st.markdown(f"""<style>
        button[data-testid="{btn_key}"] {{
            height:0 !important; min-height:0 !important;
            padding:0 !important; margin:0 !important;
            border:none !important; background:transparent !important;
            box-shadow:none !important; opacity:0 !important;
            width:100% !important; cursor:pointer !important;
            position:relative !important; top:-105px !important;
            z-index:20 !important; display:block !important;
        }}
        div[data-testid="stButton"]:has(button[data-testid="{btn_key}"]) {{
            margin-top:-105px !important; height:105px !important;
            overflow:hidden !important; position:relative !important;
            z-index:20 !important;
        }}
        </style>""", unsafe_allow_html=True)

        if st.button("·", key=btn_key, use_container_width=True):
            dialog_fn(*dialog_args)

k1, k2, k3, k4 = st.columns(4)

RF_CLS  = "kpi-alert" if len(red_flags) > 0 else "kpi-ok"
EXP_CLS = "kpi-warn"  if len(expiring_7) > 0 else "kpi-ok"
STL_CLS = "kpi-warn"  if len(stalled)    > 10 else "kpi-ok"

kpi_card(k1, "kpi-default", "Active Clients",       active_clients,  "across all orgs",           "kpi_clients",  dialog_active_clients, clients_df)
kpi_card(k2, RF_CLS,        "RED_FLAG Violations",  len(red_flags),  "require immediate action",   "kpi_flags",    dialog_red_flags,       red_flags, encounters_on_expired)
kpi_card(k3, EXP_CLS,       "Consent Expiring ≤7d", len(expiring_7), f"{len(expiring_30)} ≤ 30d",  "kpi_expiring", dialog_expiring,        expiring_7, expiring_30, consent_df)
kpi_card(k4, STL_CLS,       "Stalled Referrals",    len(stalled),    "awaiting response",           "kpi_stalled",  dialog_stalled,         stalled, referrals_df)

st.divider()

# ══ TWO-COLUMN BODY ═══════════════════════════════════════════════════════════
col_left, col_right = st.columns([3, 2], gap="medium")

with col_left:
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
        st.markdown(f'<div class="pill pill-amber">{len(expiring_7)} client(s) — consent expiring within 7 days</div>',
                    unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

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
    section_header("Expiring Consent")
    if expiring_7.empty:
        st.markdown('<div class="pill pill-green">None expiring this week</div>', unsafe_allow_html=True)
    else:
        exp_html = ""
        for _, row in expiring_7.head(8).iterrows():
            cid     = row.get("client_id","")
            exp     = row.get("expiry_date")
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

    st.markdown("<br>", unsafe_allow_html=True)

    section_header("Quick Actions")
    if st.button("Search Clients",   use_container_width=True, key="qa_search"):
        st.switch_page("pages/2_Client_Search.py")
    if st.button("Record Consent",   use_container_width=True, key="qa_consent"):
        st.switch_page("pages/4_Consent_Form.py")
    if st.button("New Referral",     use_container_width=True, key="qa_referral"):
        st.switch_page("pages/7_New_Referral.py")
    if st.button("Compliance Audit", use_container_width=True, key="qa_audit"):
        st.switch_page("pages/5_Compliance_Audit.py")

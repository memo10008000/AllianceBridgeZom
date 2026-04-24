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
/* ── KPI cards — full card is the clickable button ── */
.stButton.kpi-btn > button {
    background: var(--white) !important;
    border: 1px solid var(--border) !important;
    border-left: 3px solid var(--navy) !important;
    border-radius: 6px !important;
    padding: 0.85rem 1rem !important;
    width: 100% !important;
    height: auto !important;
    min-height: unset !important;
    text-align: left !important;
    cursor: pointer !important;
    box-shadow: none !important;
    transition: box-shadow 0.15s, border-color 0.15s !important;
    display: flex !important;
    flex-direction: column !important;
    gap: 0.1rem !important;
    line-height: 1.3 !important;
    white-space: normal !important;
}
.stButton.kpi-btn > button:hover {
    box-shadow: 0 2px 10px rgba(15,41,66,0.10) !important;
    border-color: var(--navy) !important;
}
.stButton.kpi-btn.alert > button { border-left-color: var(--red) !important; }
.stButton.kpi-btn.warn  > button { border-left-color: var(--amber) !important; }
.stButton.kpi-btn.ok    > button { border-left-color: var(--green) !important; }

/* ── KPI inner text styling via pseudo-structure ── */
/* We embed label + value + sub inside the button text using line breaks */
.stButton.kpi-btn > button p {
    margin: 0 !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
}

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
.kpi-click {
    font-size: 0.6rem; color: var(--teal);
    font-weight: 500; letter-spacing: 0.04em;
    margin-left: 0.25rem; text-decoration: underline dotted;
    text-underline-offset: 2px;
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

def kpi_card(col, label, value, sub, cls, key, dialog_fn, *dialog_args):
    """Render one KPI card in `col` with a full-card clickable button."""
    with col:
        # Visual card (pure HTML — renders correctly on all screen sizes)
        tick = "▲" if cls == "alert" else "●" if cls == "warn" else "✓" if cls == "ok" else ""
        tick_color = "var(--red)" if cls=="alert" else "var(--amber)" if cls=="warn" else "var(--green)" if cls=="ok" else "var(--navy)"
        num_cls = cls if cls else ""
        st.markdown(f"""
        <div class="kpi-card {cls}" style="margin-bottom:0.1rem">
          <div class="kpi-lbl">{label}</div>
          <div class="kpi-num {num_cls}">
            {value}
            <span style="font-size:0.7rem;color:{tick_color};font-family:'IBM Plex Sans',sans-serif">{tick}</span>
            <span class="kpi-click">tap for detail</span>
          </div>
          <div class="kpi-sub">{sub}</div>
        </div>
        """, unsafe_allow_html=True)

        # Invisible full-width button placed right after the card
        # CSS makes it transparent and overlapping — gives click area
        st.markdown(f"""
        <style>
        div[data-testid="element-container"]:has(button[kind="secondary"]#btn_{key}) {{
            margin-top: -4.2rem !important;
            height: 4.2rem !important;
            overflow: hidden;
        }}
        button[kind="secondary"]#btn_{key},
        div[data-testid="element-container"]:has(> div > button[key="kpi_{key}"]) button {{
            background: transparent !important;
            border: none !important;
            width: 100% !important;
            height: 4.8rem !important;
            opacity: 0 !important;
            cursor: pointer !important;
        }}
        </style>
        """, unsafe_allow_html=True)

        if st.button(" ", key=f"kpi_{key}", use_container_width=True,
                     help=f"View {label} detail"):
            dialog_fn(*dialog_args)


# Better approach: use st.columns layout with the card HTML + a real visible
# button styled to match the original big-number look
k1, k2, k3, k4 = st.columns(4)

RF_CLS  = "alert" if len(red_flags) > 0 else "ok"
EXP_CLS = "warn"  if len(expiring_7) > 0 else "ok"
STL_CLS = "warn"  if len(stalled) > 10  else "ok"

def render_kpi(col, label, value, sub, val_cls, btn_key, dialog_fn, *args):
    """
    Render a professional KPI card.
    The number + label are HTML. Below them sits a styled Streamlit button
    that looks like a subtle 'View detail' link — clean, no overlap tricks.
    """
    val_color = {
        "alert": "var(--red)",
        "warn":  "var(--amber)",
        "ok":    "var(--green)",
        "":      "var(--navy)",
    }.get(val_cls, "var(--navy)")

    border_color = {
        "alert": "var(--red)",
        "warn":  "var(--amber)",
        "ok":    "var(--green)",
        "":      "var(--navy)",
    }.get(val_cls, "var(--navy)")

    with col:
        st.markdown(f"""
        <div style="
            background:var(--white);
            border:1px solid var(--border);
            border-left:3px solid {border_color};
            border-radius:6px 6px 0 0;
            padding:0.85rem 1rem 0.5rem 1rem;
        ">
          <div style="font-size:0.62rem;font-weight:600;text-transform:uppercase;
                      letter-spacing:0.07em;color:var(--text-sm);margin-bottom:0.35rem">
            {label}
          </div>
          <div style="font-size:2.1rem;font-weight:300;line-height:1;
                      font-family:'IBM Plex Mono',monospace;color:{val_color}">
            {value}
          </div>
          <div style="font-size:0.63rem;color:var(--text-sm);margin-top:0.3rem">
            {sub}
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Button sits flush below the card, styled as a teal "View detail" tab
        st.markdown(f"""
        <style>
        div[data-testid="stButton"]:has(button[data-testid="{btn_key}"]) button {{
            background: #F0FAF9 !important;
            border: 1px solid {border_color} !important;
            border-top: none !important;
            border-radius: 0 0 6px 6px !important;
            color: {val_color} !important;
            font-size: 0.68rem !important;
            font-weight: 600 !important;
            letter-spacing: 0.04em !important;
            text-transform: uppercase !important;
            padding: 0.35rem 1rem !important;
            width: 100% !important;
            min-height: unset !important;
            height: auto !important;
            cursor: pointer !important;
            box-shadow: none !important;
            margin-top: 0 !important;
            transition: background 0.12s !important;
        }}
        div[data-testid="stButton"]:has(button[data-testid="{btn_key}"]) button:hover {{
            background: #D9F2F0 !important;
        }}
        </style>
        """, unsafe_allow_html=True)

        # data-testid is set via key in newer Streamlit
        clicked = st.button("View detail  →", key=btn_key, use_container_width=True)
        if clicked:
            dialog_fn(*args)

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

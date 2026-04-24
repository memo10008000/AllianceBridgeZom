"""
src/styles.py
Shared CSS design system for all pages.
Import and call inject_css() at the top of every page.

Design system: IBM Plex Sans + IBM Plex Mono
Palette: Navy #0F2942 · Teal #0D7C7C · Semantic red/amber/green
"""

import streamlit as st

SHARED_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
    --navy:     #0F2942;
    --navy-lt:  #1A3E5C;
    --teal:     #0D7C7C;
    --teal-lt:  #E0F4F4;
    --red:      #C0392B;
    --red-lt:   #FDECEA;
    --amber:    #C07000;
    --amber-lt: #FFF3E0;
    --green:    #1A6B3A;
    --green-lt: #E6F5EC;
    --slate:    #4A5568;
    --border:   #DDE2E8;
    --bg:       #F7F9FC;
    --white:    #FFFFFF;
    --text:     #1A202C;
    --text-sm:  #64748B;
    --mono:     'IBM Plex Mono', monospace;
    --sans:     'IBM Plex Sans', sans-serif;
}

html, body, [class*="css"] {
    font-family: var(--sans) !important;
}
/* Target content text but NOT spans (Material Symbols icons use span with icon font) */
p, h1, h2, h3, h4, h5, h6, label, caption,
.stMarkdown p, .stMarkdown li, .stMarkdown td,
.stText, td, th, .element-container {
    font-family: var(--sans) !important;
}
/* Override buttons but not their icon children */
button > *:not([data-testid*="Icon"]):not(.material-symbols-rounded) {
    font-family: var(--sans) !important;
}

/* ── Hide chrome ── */
#MainMenu, footer { visibility: hidden; }
/* Do NOT hide header — it contains the sidebar collapse/expand button */
header { background: transparent !important; }
[data-testid="stToolbar"] { display: none !important; }
.stDeployButton { display: none; }

/* ── Sidebar toggle buttons — always visible and styled ── */
/* Collapse button (inside sidebar, top right) */
[data-testid="stSidebar"] [data-testid="stBaseButton-headerNoPadding"] {
    color: rgba(255,255,255,0.6) !important;
}
[data-testid="stSidebar"] [data-testid="stBaseButton-headerNoPadding"]:hover {
    color: #FFFFFF !important;
    background: rgba(255,255,255,0.1) !important;
    border-radius: 4px !important;
}
/* Expand button (left edge, when sidebar is collapsed) */
[data-testid="stSidebarCollapsedControl"] {
    background: var(--navy) !important;
    border-radius: 0 6px 6px 0 !important;
}
[data-testid="stSidebarCollapsedControl"]:hover {
    background: #1A3E5C !important;
}
[data-testid="stSidebarCollapsedControl"] span {
    color: #FFFFFF !important;
}

/* ── Slim dark sidebar ── */
[data-testid="stSidebar"] {
    min-width: 200px !important;
    max-width: 200px !important;
    background: var(--navy) !important;
}
[data-testid="stSidebar"] * { color: #CBD5E0 !important; font-size: 0.82rem !important; }
[data-testid="stSidebar"] .stMarkdown h3 {
    color: #FFFFFF !important; font-size: 0.88rem !important;
    font-weight: 600 !important; letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
}
[data-testid="stSidebar"] .stMarkdown p { font-size: 0.75rem !important; }
[data-testid="stSidebarNavLink"] {
    padding: 0.3rem 0.75rem !important; border-radius: 4px !important;
    margin: 1px 0 !important; font-size: 0.8rem !important;
}
[data-testid="stSidebarNavLink"][aria-current="page"] {
    background: rgba(255,255,255,0.13) !important; color: #FFFFFF !important;
}
[data-testid="stSidebarNavLink"]:hover { background: rgba(255,255,255,0.07) !important; }

/* ── Main content ── */
.main .block-container {
    padding: 1.5rem 2rem 2rem 2rem !important;
    max-width: 1400px !important;
}

/* ── Page header ── */
.page-header {
    display: flex; align-items: baseline;
    justify-content: space-between;
    margin-bottom: 1.25rem;
    padding-bottom: 0.75rem;
    border-bottom: 2px solid var(--navy);
}
.page-header-title { font-size: 1.3rem; font-weight: 600; color: var(--navy); letter-spacing: -0.01em; }
.page-header-sub   { font-size: 0.75rem; color: var(--text-sm); font-family: var(--mono) !important; }

/* ── Section header ── */
.section-header {
    font-size: 0.68rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.08em; color: var(--text-sm);
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.35rem; margin-bottom: 0.75rem;
}

/* ── KPI bar ── */
.kpi-bar { display: grid; grid-template-columns: repeat(4,1fr); gap: 0.75rem; margin-bottom: 1.25rem; }
.kpi-card {
    background: var(--white); border: 1px solid var(--border);
    border-radius: 6px; padding: 0.85rem 1rem;
    border-left: 3px solid var(--navy);
}
.kpi-card.alert { border-left-color: var(--red); }
.kpi-card.warn  { border-left-color: var(--amber); }
.kpi-card.ok    { border-left-color: var(--green); }
.kpi-label { font-size: 0.65rem; font-weight: 500; color: var(--text-sm); text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.2rem; }
.kpi-value { font-size: 1.85rem; font-weight: 300; color: var(--navy); line-height: 1; font-family: var(--mono) !important; }
.kpi-value.alert { color: var(--red); }
.kpi-value.warn  { color: var(--amber); }
.kpi-value.ok    { color: var(--green); }
.kpi-sub   { font-size: 0.65rem; color: var(--text-sm); margin-top: 0.2rem; }

/* ── Badge ── */
.badge { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 3px; font-size: 0.63rem; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase; }
.badge-high    { background: var(--red-lt);   color: var(--red);   }
.badge-mod     { background: var(--amber-lt); color: var(--amber); }
.badge-low     { background: var(--green-lt); color: var(--green); }
.badge-valid   { background: var(--green-lt); color: var(--green); }
.badge-expired { background: var(--red-lt);   color: var(--red);   }
.badge-expiring{ background: var(--amber-lt); color: var(--amber); }
.badge-withdrawn{ background: #EDF2F7; color: var(--slate); }
.badge-norecord{ background: #EDF2F7; color: var(--slate); }
.badge-ocap    { background: #EDE9FE; color: #5B21B6; }
.badge-dup     { background: var(--amber-lt); color: var(--amber); }
.badge-navy    { background: var(--navy); color: #FFFFFF; }
.badge-teal    { background: var(--teal); color: #FFFFFF; }

/* ── Pill alerts ── */
.pill { display:flex; align-items:center; gap:0.5rem; border-radius:4px; padding:0.45rem 0.8rem; font-size:0.78rem; font-weight:500; margin:0.2rem 0; width:100%; }
.pill-red    { background:var(--red-lt);   border:1px solid #F5C6CB; color:var(--red);   }
.pill-amber  { background:var(--amber-lt); border:1px solid #FFCC80; color:var(--amber); }
.pill-green  { background:var(--green-lt); border:1px solid #A8D5B5; color:var(--green); }
.pill-blue   { background:#EBF8FF;         border:1px solid #BEE3F8; color:#1A6B8A;      }
.pill-gray   { background:#F7FAFC;         border:1px solid var(--border); color:var(--slate); }

/* ── Data table ── */
.data-table { width:100%; border-collapse:collapse; font-size:0.8rem; }
.data-table th { font-size:0.63rem; font-weight:600; text-transform:uppercase; letter-spacing:0.06em; color:var(--text-sm); background:var(--bg); padding:0.5rem 0.65rem; text-align:left; border-bottom:1px solid var(--border); }
.data-table td { padding:0.48rem 0.65rem; border-bottom:1px solid #EDF2F7; color:var(--text); vertical-align:middle; }
.data-table tr:hover td { background:#F8FAFC; }
.mono-cell { font-family:var(--mono) !important; font-size:0.72rem !important; }

/* ── Card ── */
.card { background:var(--white); border:1px solid var(--border); border-radius:6px; padding:1rem 1.1rem; margin-bottom:0.85rem; }
.card-title { font-size:0.72rem; font-weight:600; text-transform:uppercase; letter-spacing:0.06em; color:var(--text-sm); margin-bottom:0.5rem; }

/* ── Consent banner ── */
.consent-banner { border-radius:6px; padding:0.85rem 1rem; margin-bottom:1rem; display:flex; align-items:flex-start; gap:0.75rem; }
.consent-banner.valid    { background:var(--green-lt); border:1px solid #A8D5B5; }
.consent-banner.expiring { background:var(--amber-lt); border:1px solid #FFCC80; }
.consent-banner.expired  { background:var(--red-lt);   border:1px solid #F5C6CB; }
.consent-banner.blocked  { background:var(--red-lt);   border:1px solid #F5C6CB; }
.consent-icon { font-size:1.4rem; line-height:1; }
.consent-title { font-size:0.85rem; font-weight:600; margin-bottom:0.2rem; }
.consent-meta  { font-size:0.72rem; color:var(--slate); font-family:var(--mono) !important; }

/* ── Profile fields ── */
.field-row { display:flex; padding:0.38rem 0; border-bottom:1px solid #EDF2F7; gap:0.5rem; font-size:0.8rem; }
.field-label { width:140px; min-width:140px; font-size:0.68rem; font-weight:500; color:var(--text-sm); text-transform:uppercase; letter-spacing:0.04em; padding-top:0.05rem; }
.field-value { color:var(--text); flex:1; }

/* ── Step indicator ── */
.step-bar { display:flex; gap:0; margin-bottom:1.25rem; }
.step-item { flex:1; text-align:center; padding:0.5rem; border:1px solid var(--border); border-right:none; font-size:0.7rem; }
.step-item:first-child { border-radius:4px 0 0 4px; }
.step-item:last-child  { border-right:1px solid var(--border); border-radius:0 4px 4px 0; }
.step-item.active   { background:var(--navy); color:#FFFFFF !important; border-color:var(--navy); }
.step-item.done     { background:var(--green-lt); color:var(--green) !important; border-color:#A8D5B5; }
.step-item.inactive { background:var(--bg); color:var(--text-sm) !important; }
.step-num   { font-family:var(--mono) !important; font-weight:600; font-size:0.8rem; display:block; }
.step-label { font-size:0.65rem; letter-spacing:0.04em; text-transform:uppercase; }

/* ── Inline key-value ── */
.kv-inline { display:flex; gap:1.5rem; flex-wrap:wrap; font-size:0.78rem; margin:0.4rem 0; }
.kv-item label { font-size:0.65rem; font-weight:500; color:var(--text-sm); text-transform:uppercase; letter-spacing:0.05em; display:block; }
.kv-item span  { color:var(--text); font-family:var(--mono) !important; }

/* ── Block screen ── */
.block-screen { background:var(--red-lt); border:1px solid #F5C6CB; border-radius:8px; padding:1.5rem; margin:1rem 0; text-align:center; }
.block-icon   { font-size:2.5rem; margin-bottom:0.5rem; }
.block-title  { font-size:1.1rem; font-weight:600; color:var(--red); margin-bottom:0.4rem; }
.block-msg    { font-size:0.82rem; color:var(--slate); max-width:480px; margin:0 auto; }

/* ── Streamlit button overrides ── */
.stButton button {
    font-family: var(--sans) !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    border-radius: 4px !important;
}
.stButton button[kind="primary"] {
    background: var(--navy) !important;
    border-color: var(--navy) !important;
    color: #FFFFFF !important;
}
.stButton button[kind="primary"]:hover { background: var(--navy-lt) !important; }

/* ── Selectbox / input ── */
.stSelectbox label, .stTextInput label, .stTextArea label,
.stMultiSelect label, .stDateInput label, .stCheckbox label {
    font-size: 0.72rem !important;
    font-weight: 500 !important;
    color: var(--text-sm) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}

/* ── Tab styling ── */
.stTabs [data-baseweb="tab-list"] { gap: 0; border-bottom: 2px solid var(--border); }
.stTabs [data-baseweb="tab"] {
    font-size: 0.78rem !important; font-weight: 500 !important;
    padding: 0.5rem 1rem !important; border-radius: 0 !important;
    color: var(--text-sm) !important; background: transparent !important;
    border-bottom: 2px solid transparent !important; margin-bottom: -2px;
}
.stTabs [aria-selected="true"] { color: var(--navy) !important; border-bottom-color: var(--navy) !important; }
</style>
"""

def inject_css():
    """Call this at the top of every page to apply the shared design system."""
    st.markdown(SHARED_CSS, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "", right: str = ""):
    st.markdown(f"""
    <div class="page-header">
      <div>
        <div class="page-header-title">{title}</div>
        {"<div class='page-header-sub'>" + subtitle + "</div>" if subtitle else ""}
      </div>
      <div class="page-header-sub">{right}</div>
    </div>
    """, unsafe_allow_html=True)


def section_header(label: str):
    st.markdown(f'<div class="section-header">{label}</div>', unsafe_allow_html=True)


def kpi_bar(cards: list[dict]):
    """
    cards = [{"label": str, "value": str|int, "sub": str, "cls": ""|"alert"|"warn"|"ok"}]
    """
    inner = ""
    for c in cards:
        cls    = c.get("cls", "")
        val_cls = cls
        inner += f"""
        <div class="kpi-card {cls}">
          <div class="kpi-label">{c['label']}</div>
          <div class="kpi-value {val_cls}">{c['value']}</div>
          <div class="kpi-sub">{c.get('sub','')}</div>
        </div>"""
    st.markdown(f'<div class="kpi-bar">{inner}</div>', unsafe_allow_html=True)


def pill(text: str, kind: str = "gray"):
    """kind: red | amber | green | blue | gray"""
    st.markdown(f'<div class="pill pill-{kind}">{text}</div>', unsafe_allow_html=True)


def consent_banner(status: str, record: dict | None):
    """Render the consent status banner."""
    icons   = {"VALID": "✅", "EXPIRING": "⚠️", "EXPIRED": "🔴",
                "WITHDRAWN": "🚫", "NO_RECORD": "❓"}
    classes = {"VALID": "valid", "EXPIRING": "expiring", "EXPIRED": "expired",
               "WITHDRAWN": "blocked", "NO_RECORD": "blocked"}
    titles  = {"VALID": "Valid Consent",    "EXPIRING": "Consent Expiring Soon",
               "EXPIRED": "Consent Expired", "WITHDRAWN": "Consent Withdrawn",
               "NO_RECORD": "No Consent Record"}
    icon  = icons.get(status, "❓")
    cls   = classes.get(status, "blocked")
    title = titles.get(status, status)

    meta = ""
    if record:
        import pandas as pd
        exp   = record.get("expiry_date")
        scope = record.get("sharing_scope_type", "")
        purp  = record.get("purpose_codes", "")
        org   = record.get("collecting_org_id", "")
        exp_s = str(exp)[:10] if exp is not None else "No expiry"

        from datetime import date
        days_left = ""
        if exp is not None:
            try:
                dl = (pd.to_datetime(exp).date() - date.today()).days
                days_left = f" &nbsp;·&nbsp; {dl}d remaining" if dl > 0 else " &nbsp;·&nbsp; EXPIRED"
            except Exception:
                pass

        meta = (f"Expires: {exp_s}{days_left} &nbsp;·&nbsp; "
                f"Scope: {scope} &nbsp;·&nbsp; Purpose: {purp} &nbsp;·&nbsp; "
                f"Org: {org}")

    st.markdown(f"""
    <div class="consent-banner {cls}">
      <div class="consent-icon">{icon}</div>
      <div>
        <div class="consent-title">{title}</div>
        <div class="consent-meta">{meta}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def field_row(label: str, value: str):
    st.markdown(f"""
    <div class="field-row">
      <span class="field-label">{label}</span>
      <span class="field-value">{value}</span>
    </div>
    """, unsafe_allow_html=True)


def step_bar(steps: list[str], current: int):
    """current is 1-indexed."""
    items = ""
    for i, s in enumerate(steps, 1):
        if i < current:
            cls = "done"; num_icon = "✓"
        elif i == current:
            cls = "active"; num_icon = str(i)
        else:
            cls = "inactive"; num_icon = str(i)
        items += f"""
        <div class="step-item {cls}">
          <span class="step-num">{num_icon}</span>
          <span class="step-label">{s}</span>
        </div>"""
    st.markdown(f'<div class="step-bar">{items}</div>', unsafe_allow_html=True)

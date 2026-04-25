"""
pages/6_Duplicate_Review.py  —  SCR-06  Duplicate Review Queue
"""
import streamlit as st
import pandas as pd

try:
    from src.data_loader import load_tables
    from src.consent_gate import consent_gate
    from src.styles import inject_css, page_header, section_header, pill, field_row
    _STUB = False
except ImportError:
    _STUB = True

inject_css()

# KPI CARD CSS
st.markdown("""
<style>
div[data-testid="stButton"].kpi-default > button,
div[data-testid="stButton"].kpi-alert   > button,
div[data-testid="stButton"].kpi-warn    > button,
div[data-testid="stButton"].kpi-ok      > button {
    width: 100% !important; height: auto !important; min-height: unset !important;
    text-align: left !important; padding: 0.9rem 1rem 0.8rem 1rem !important;
    border-radius: 6px !important; border: 1px solid var(--border) !important;
    border-left-width: 3px !important; box-shadow: none !important; cursor: pointer !important;
    transition: box-shadow 0.15s, transform 0.1s !important;
    background: var(--white) !important; display: flex !important; flex-direction: column !important;
    gap: 0 !important; white-space: pre-wrap !important; line-height: 1.2 !important;
}
div[data-testid="stButton"].kpi-default > button { border-left-color: var(--navy) !important; }
div[data-testid="stButton"].kpi-alert   > button { border-left-color: var(--red)   !important; }
div[data-testid="stButton"].kpi-warn    > button { border-left-color: var(--amber) !important; }
div[data-testid="stButton"].kpi-ok      > button { border-left-color: var(--green) !important; }

div[data-testid="stButton"].kpi-default > button:hover, div[data-testid="stButton"].kpi-alert > button:hover,
div[data-testid="stButton"].kpi-warn > button:hover, div[data-testid="stButton"].kpi-ok > button:hover {
    box-shadow: 0 3px 12px rgba(15,41,66,0.12) !important; transform: translateY(-1px) !important;
}
div[data-testid="stButton"].kpi-default > button:active, div[data-testid="stButton"].kpi-alert > button:active,
div[data-testid="stButton"].kpi-warn > button:active, div[data-testid="stButton"].kpi-ok > button:active {
    transform: translateY(0) !important;
}

div[data-testid="stButton"].kpi-default > button p, div[data-testid="stButton"].kpi-alert > button p,
div[data-testid="stButton"].kpi-warn > button p, div[data-testid="stButton"].kpi-ok > button p {
    margin: 0 !important; font-family: 'IBM Plex Sans', sans-serif !important; text-align: left !important;
}

div[data-testid="stButton"].kpi-default > button p:first-child, div[data-testid="stButton"].kpi-alert > button p:first-child,
div[data-testid="stButton"].kpi-warn > button p:first-child, div[data-testid="stButton"].kpi-ok > button p:first-child {
    font-size: 0.62rem !important; font-weight: 600 !important; text-transform: uppercase !important;
    letter-spacing: 0.07em !important; color: var(--text-sm) !important; margin-bottom: 0.3rem !important;
}

.kpi-label-txt { font-size: 0.62rem !important; font-weight: 600 !important; text-transform: uppercase !important; letter-spacing: 0.07em !important; color: var(--text-sm) !important; display: block !important; margin-bottom: 0.3rem !important; }
.kpi-value-txt { font-size: 2.1rem !important; font-weight: 300 !important; line-height: 1 !important; font-family: 'IBM Plex Mono', monospace !important; display: block !important; margin-bottom: 0.3rem !important; text-decoration: underline dotted !important; text-underline-offset: 4px !important; }
.kpi-sub-txt { font-size: 0.63rem !important; color: var(--text-sm) !important; display: block !important; font-family: 'IBM Plex Sans', sans-serif !important; }

.kpi-default .kpi-value-txt { color: var(--navy) !important; text-decoration-color: rgba(15,41,66,0.3) !important; }
.kpi-alert   .kpi-value-txt { color: var(--red)   !important; text-decoration-color: rgba(192,57,43,0.3) !important; }
.kpi-warn    .kpi-value-txt { color: var(--amber) !important; text-decoration-color: rgba(192,112,0,0.3) !important; }
.kpi-ok      .kpi-value-txt { color: var(--green) !important; text-decoration-color: rgba(26,107,58,0.3) !important; }

div[data-testid="stButton"].kpi-default > button:hover .kpi-value-txt, div[data-testid="stButton"].kpi-alert > button:hover .kpi-value-txt,
div[data-testid="stButton"].kpi-warn > button:hover .kpi-value-txt, div[data-testid="stButton"].kpi-ok > button:hover .kpi-value-txt {
    color: var(--teal) !important; text-decoration-style: solid !important; text-decoration-color: var(--teal) !important;
}
</style>
""", unsafe_allow_html=True)

def kpi_card(col, css_cls, label, value, sub, btn_key, dialog_fn, *dialog_args):
    accent = "var(--red)" if css_cls == "kpi-alert" else "var(--amber)" if css_cls == "kpi-warn" else "var(--green)" if css_cls == "kpi-ok" else "var(--navy)"
    dec_color = "rgba(192,57,43,0.25)" if css_cls == "kpi-alert" else "rgba(192,112,0,0.25)" if css_cls == "kpi-warn" else "rgba(26,107,58,0.25)" if css_cls == "kpi-ok" else "rgba(15,41,66,0.25)"
    
    with col:
        st.markdown(f"""<style>
        div[data-testid="stButton"]:has(> div > button[data-testid="{btn_key}"]) {{ margin-top: -6.2rem !important; height: 6.2rem !important; overflow: hidden !important; }}
        button[data-testid="{btn_key}"] {{ width: 100% !important; height: 6.2rem !important; min-height: 0 !important; background: transparent !important; border: none !important; box-shadow: none !important; opacity: 0 !important; cursor: pointer !important; padding: 0 !important; margin: 0 !important; font-size: 0 !important; color: transparent !important; display: block !important; }}
        div[data-testid="stVerticalBlock"]:has(button[data-testid="{btn_key}"]:hover) .kpi-{btn_key} {{ box-shadow: 0 3px 12px rgba(15,41,66,0.12) !important; transform: translateY(-1px) !important; }}
        </style>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div class="kpi-{btn_key}" style="background: var(--white); border: 1px solid var(--border); border-left: 3px solid {accent}; border-radius: 6px; padding: 0.85rem 1rem 0.75rem 1rem; transition: box-shadow 0.15s, transform 0.1s;">
          <div style="font-size:0.62rem;font-weight:600;text-transform:uppercase;letter-spacing:0.07em;color:var(--text-sm);font-family:'IBM Plex Sans',sans-serif;margin-bottom:0.3rem">{label}</div>
          <div style="font-size:2.1rem;font-weight:300;line-height:1;font-family:'IBM Plex Mono',monospace;color:{accent};text-decoration:underline dotted;text-decoration-color:{dec_color};text-underline-offset:4px;margin-bottom:0.25rem">{value}</div>
          <div style="font-size:0.63rem;color:var(--text-sm);font-family:'IBM Plex Sans',sans-serif">{sub}</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("open", key=btn_key, use_container_width=True):
            dialog_fn(*dialog_args)

# Dialogs
def _show_df(df, cols):
    if df.empty:
        st.info("No records to display.")
    else:
        show_cols = [c for c in cols if c in df.columns]
        st.dataframe(df[show_cols].reset_index(drop=True), use_container_width=True, hide_index=True)

@st.dialog("Pending Pairs", width="large")
def dialog_pending(df):
    st.caption(f"{len(df)} pair(s) awaiting review")
    _show_df(df, ["duplicate_flag_id", "client_id_primary", "client_id_secondary", "match_score", "possible_duplicate_reason"])

@st.dialog("Reviewed Pairs Today", width="large")
def dialog_reviewed(df):
    st.caption(f"{len(df)} pair(s) reviewed this session")
    _show_df(df, ["duplicate_flag_id", "client_id_primary", "client_id_secondary", "review_status", "review_decision_date"])

@st.dialog("Total Candidate Pairs", width="large")
def dialog_total(df):
    st.caption(f"{len(df)} pair(s) in dataset")
    _show_df(df, ["duplicate_flag_id", "client_id_primary", "client_id_secondary", "match_score", "review_status"])

@st.dialog("High Confidence Pairs", width="large")
def dialog_high_confidence(df):
    st.caption(f"{len(df)} pair(s) with match score ≥ 85%")
    _show_df(df, ["duplicate_flag_id", "client_id_primary", "client_id_secondary", "match_score", "possible_duplicate_reason"])

@st.cache_data(show_spinner=False)
def get_tables():
    return {} if _STUB else load_tables()

tables         = get_tables()
requesting_org = st.session_state.get("caseworker_org","ORG-001")

page_header("Duplicate Review Queue", subtitle="Pending candidate pairs · sorted by match score")
if st.button("← Dashboard", key="dr_back"):
    st.switch_page("pages/1_Dashboard.py")
st.divider()

if _STUB:
    st.warning("Stub mode"); st.stop()

dup_df     = tables.get("dup_flags", pd.DataFrame())
clients_df = tables.get("clients",   pd.DataFrame())

if dup_df.empty:
    pill("No duplicate flag data available", "gray"); st.stop()

# Real data-driven logic
pending_col = "review_status" if "review_status" in dup_df.columns else None
pending = dup_df[dup_df[pending_col]=="unreviewed"].copy() if pending_col else dup_df.copy()
if "match_score" in pending.columns:
    pending = pending.sort_values("match_score", ascending=False)

reviewed_df = dup_df[dup_df[pending_col].isin(["confirmed_duplicate", "not_duplicate", "merged"])].copy() if pending_col else pd.DataFrame()
reviewed_today = len(reviewed_df)

high_conf = pending[pending.get("match_score", pd.Series(dtype=float)) >= 0.85] if not pending.empty and "match_score" in pending.columns else pd.DataFrame()

# Render clickabke KPI Cards
k1, k2, k3, k4 = st.columns(4)
kpi_card(k1, "kpi-warn" if len(pending)>0 else "kpi-ok", "Pending Pairs", len(pending), "awaiting review", "dr_kpi_pend", dialog_pending, pending)
kpi_card(k2, "kpi-default", "Reviewed Today", reviewed_today, "this session", "dr_kpi_rev", dialog_reviewed, reviewed_df)
kpi_card(k3, "kpi-default", "Total Pairs", len(dup_df), "in dataset", "dr_kpi_tot", dialog_total, dup_df)
kpi_card(k4, "kpi-alert" if len(high_conf)>0 else "kpi-ok", "High Confidence", len(high_conf), "score ≥ 85%", "dr_kpi_high", dialog_high_confidence, high_conf)

st.markdown("<br>", unsafe_allow_html=True)

if pending.empty:
    pill("✅  No pending duplicate pairs", "green"); st.stop()

section_header(f"Pending Review — {len(pending)} pair(s)")

for idx, pair in pending.head(10).iterrows():
    primary_id   = str(pair.get("client_id_primary",""))
    secondary_id = str(pair.get("client_id_secondary",""))
    score        = pair.get("match_score", 0)
    reason       = pair.get("possible_duplicate_reason","Unknown signals")
    score_pct    = int(float(score)*100) if score else 0
    icon = "🔴" if score_pct>=85 else "🟠" if score_pct>=70 else "🟡"

    with st.expander(f"{score_pct}% match — {primary_id} vs {secondary_id} · {reason}", expanded=idx==pending.index[0]):
        gate_p, msg_p = consent_gate(primary_id,   requesting_org, tables)
        gate_s, msg_s = consent_gate(secondary_id, requesting_org, tables)

        def get_client(cid, allowed):
            if not allowed: return None
            rows = clients_df[clients_df["client_id"]==cid]
            return rows.iloc[0].to_dict() if not rows.empty else None

        cp = get_client(primary_id,   gate_p=="ALLOW")
        cs = get_client(secondary_id, gate_s=="ALLOW")

        col_l, col_r = st.columns(2)
        PROFILE_FIELDS = [("Name","first_name","last_name"),("DOB","dob",None),("Aliases","aliases",None),("Org","primary_org_id",None),("Housing","housing_status",None)]

        with col_l:
            section_header(f"Primary · {primary_id}")
            if gate_p=="ALLOW" and cp:
                for lbl, k1, k2 in PROFILE_FIELDS:
                    v = f"{cp.get(k1,'')} {cp.get(k2,'') if k2 else ''}".strip()
                    if v and v not in ("nan",""):
                        field_row(lbl, str(v)[:30])
            else:
                pill(f"🚫 {msg_p}", "red")

        with col_r:
            section_header(f"Secondary · {secondary_id}")
            if gate_s=="ALLOW" and cs:
                for lbl, k1, k2 in PROFILE_FIELDS:
                    v = f"{cs.get(k1,'')} {cs.get(k2,'') if k2 else ''}".strip()
                    if v and v not in ("nan",""):
                        field_row(lbl, str(v)[:30])
            else:
                pill(f"🚫 {msg_s}", "red")

        st.markdown("<br>", unsafe_allow_html=True)
        d1, d2, d3 = st.columns(3)
        with d1:
            if st.button("✅ Confirm Duplicate", key=f"dr_confirm_{idx}", type="primary"):
                pill("✅ Marked as confirmed duplicate (demo session)", "green")
        with d2:
            if st.button("❌ Not a Duplicate",   key=f"dr_not_{idx}"):
                pill("Marked as not a duplicate (demo session)", "gray")
        with d3:
            if st.button("❓ Need More Info",     key=f"dr_info_{idx}"):
                pill("Flagged for additional information (demo session)", "amber")

"""
pages/6_Duplicate_Review.py  —  SCR-06  Duplicate Review Queue
"""
import streamlit as st
import pandas as pd

try:
    from src.data_loader import load_tables
    from src.consent_gate import consent_gate
    from src.styles import inject_css, page_header, section_header, pill, field_row, kpi_bar
    _STUB = False
except ImportError:
    _STUB = True

inject_css()

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

pending_col = "review_status" if "review_status" in dup_df.columns else None
pending = dup_df[dup_df[pending_col]=="pending"].copy() if pending_col else dup_df.copy()
if "match_score" in pending.columns:
    pending = pending.sort_values("match_score", ascending=False)

reviewed_today = len(dup_df) - len(pending) if pending_col else 0
kpi_bar([
    {"label": "Pending Pairs",    "value": len(pending),    "sub": "awaiting review",  "cls": "warn" if len(pending)>0 else "ok"},
    {"label": "Reviewed Today",   "value": reviewed_today,  "sub": "this session",     "cls": ""},
    {"label": "Total Pairs",      "value": len(dup_df),     "sub": "in dataset",       "cls": ""},
    {"label": "High Confidence",  "value": len(pending[pending.get("match_score",pd.Series(dtype=float))>=0.85]) if not pending.empty and "match_score" in pending.columns else 0, "sub": "score ≥ 85%", "cls": "alert"},
])

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

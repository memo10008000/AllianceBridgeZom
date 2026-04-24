"""
pages/6_Duplicate_Review.py  —  SCR-06  Duplicate Review Queue
Side-by-side comparison of candidate duplicate pairs.
Consent Gate governs cross-org visibility of each side.

Developer B owns this file.
"""
import streamlit as st
import pandas as pd

try:
    from src.data_loader import load_tables
    from src.consent_gate import consent_gate
    _STUB = False
except ImportError:
    _STUB = True

st.set_page_config(
    page_title="Duplicate Review — Coordinated Care Console",
    page_icon="🔀",
    layout="wide",
)

@st.cache_data(show_spinner="Loading duplicate queue…")
def get_tables():
    if _STUB:
        return {}
    return load_tables()

tables = get_tables()
requesting_org = st.session_state.get("caseworker_org", "ORG-001")

st.markdown("## 🔀 Duplicate Review Queue")
if st.button("← Back to Dashboard"):
    st.switch_page("pages/1_Dashboard.py")
st.divider()

if _STUB:
    st.warning("⚠️ Running in stub mode — copy CSVs into data/ and restart.")
    st.stop()

dup_df     = tables.get("dup_flags", pd.DataFrame())
clients_df = tables.get("clients",   pd.DataFrame())

if dup_df.empty:
    st.info("No duplicate flag data available.")
    st.stop()

# Filter to pending pairs, sort by match_score descending
pending_col = "review_status" if "review_status" in dup_df.columns else None
if pending_col:
    pending = dup_df[dup_df[pending_col] == "pending"].copy()
else:
    pending = dup_df.copy()

if "match_score" in pending.columns:
    pending = pending.sort_values("match_score", ascending=False)

st.caption(f"**{len(pending)}** pair(s) awaiting review")

if pending.empty:
    st.success("✅ No pending duplicate pairs.")
    st.stop()

# ── Review pairs ──────────────────────────────────────────────────────────────
for idx, pair in pending.head(10).iterrows():
    primary_id   = str(pair.get("client_id_primary", ""))
    secondary_id = str(pair.get("client_id_secondary", ""))
    score        = pair.get("match_score", 0)
    reason       = pair.get("possible_duplicate_reason", "Unknown match signals")

    score_pct = int(float(score) * 100) if score else 0
    color = "🔴" if score_pct >= 85 else "🟠" if score_pct >= 70 else "🟡"

    with st.expander(
        f"{color} **{score_pct}% match** — `{primary_id}` vs `{secondary_id}` · {reason}",
        expanded=idx == pending.index[0]
    ):
        # Check consent gate for each side
        gate_primary,   msg_primary   = consent_gate(primary_id,   requesting_org, tables)
        gate_secondary, msg_secondary = consent_gate(secondary_id, requesting_org, tables)

        def get_client_info(cid, gate_ok):
            if not gate_ok:
                return None
            rows = clients_df[clients_df["client_id"] == cid]
            return rows.iloc[0].to_dict() if not rows.empty else None

        c_primary   = get_client_info(primary_id,   gate_primary   == "ALLOW")
        c_secondary = get_client_info(secondary_id, gate_secondary == "ALLOW")

        col_left, col_right = st.columns(2)

        # Left side — primary
        with col_left:
            st.markdown(f"**PRIMARY: `{primary_id}`**")
            if gate_primary == "ALLOW" and c_primary:
                fields = ["first_name", "last_name", "dob", "aliases",
                          "primary_org_id", "housing_status"]
                for f in fields:
                    val = c_primary.get(f, "")
                    if val and str(val) not in ("nan", ""):
                        st.write(f"**{f}:** {val}")
            else:
                st.warning(f"🚫 Access blocked: {msg_primary}")
                st.caption("Contact the client's primary org for access.")

        # Right side — secondary
        with col_right:
            st.markdown(f"**SECONDARY: `{secondary_id}`**")
            if gate_secondary == "ALLOW" and c_secondary:
                fields = ["first_name", "last_name", "dob", "aliases",
                          "primary_org_id", "housing_status"]
                for f in fields:
                    val = c_secondary.get(f, "")
                    if val and str(val) not in ("nan", ""):
                        st.write(f"**{f}:** {val}")
            else:
                st.warning(f"🚫 Access blocked: {msg_secondary}")
                st.caption("Contact the client's primary org for access.")

        st.divider()

        # Decision buttons
        d1, d2, d3 = st.columns(3)
        with d1:
            if st.button("✅ Confirm Duplicate", key=f"confirm_{idx}"):
                st.success("Marked as confirmed duplicate (demo session only)")
        with d2:
            if st.button("❌ Not a Duplicate", key=f"notdup_{idx}"):
                st.info("Marked as not a duplicate (demo session only)")
        with d3:
            if st.button("❓ Need More Info", key=f"info_{idx}"):
                st.warning("Flagged for additional information (demo session only)")

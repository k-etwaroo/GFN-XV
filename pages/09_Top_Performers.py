import os
import pandas as pd
import streamlit as st

st.set_page_config(page_title="🌟 Top Performers", layout="wide")
st.title("🌟 Top Performers")
DATA_DIR = "data"


def safe_read_csv(p):
    try:
        return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


years = sorted([
    int(f.split("_")[2].split(".")[0])
    for f in os.listdir(DATA_DIR)
    if f.startswith("player_stats_") and f.split("_")[2].split(".")[0].isdigit()
])

if not years:
    st.info("Add player_stats_<year>.csv.")
    st.stop()

y = st.selectbox("Season", years, index=len(years)-1)
ps = safe_read_csv(os.path.join(DATA_DIR, f"player_stats_{y}.csv"))
if ps.empty:
    st.warning("No player stats found.")
    st.stop()

# NOTE: your player file has no per-player points. We'll show flexible views.
st.markdown(
    "_Per-player fantasy points were not provided; showing roster insights._")

pos = st.multiselect(
    "Positions", sorted(ps["position"].dropna().unique().tolist()), default=None
)
df = ps if not pos else ps[ps["position"].isin(pos)]

cols = ["team", "manager", "player_name",
        "position", "eligible_positions", "week"]
if "team_abbr" in df.columns:  # optional
    cols.insert(2, "team_abbr")

st.dataframe(df[cols], hide_index=True, use_container_width=True, height=460)

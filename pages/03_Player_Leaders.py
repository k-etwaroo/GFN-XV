import os
import pandas as pd
import streamlit as st
import plotly.express as px
import yaml
from components.header import render_header
from tools.data_loader import load_scores_all, load_franchise, attach_franchise

scores = load_scores_all()
frmap = load_franchise_map()
scores = attach_franchise(scores, frmap)

if scores.empty:
    st.warning("No scores found in /data yet.")
    st.stop()

# Common filters
all_seasons = sorted(scores["season"].dropna().unique().tolist())
season = st.sidebar.selectbox("Season", ["All"] + all_seasons, index=len(all_seasons))
view = scores if season == "All" else scores[scores["season"] == season]

# ===============================================================
# PAGE CONFIGURATION
# ===============================================================
st.set_page_config(page_title="🏅 Player Leaders", layout="wide")
render_header("Goodell For Nothing XV")
st.title("🏅 Player Leaders")
DATA_DIR = "data"

# ===============================================================
# LOAD PLAYER DATA
# ===============================================================
def safe_read_csv(path):
    try:
        return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading {path}: {e}")
        return pd.DataFrame()

def load_stat_map():
    yaml_path = os.path.join(DATA_DIR, "stat_id_map.yaml")
    if os.path.exists(yaml_path):
        with open(yaml_path, "r") as f:
            return yaml.safe_load(f)
    return {}

# ===============================================================
# FILES & YEAR SELECTION
# ===============================================================
years = sorted([
    int(f.split("_")[2].split(".")[0])
    for f in os.listdir(DATA_DIR)
    if f.startswith("player_stats_") and f.split("_")[2].split(".")[0].isdigit()
])

if not years:
    st.info("Add `player_stats_<YEAR>.csv` to `/data`.")
    st.stop()

selected_year = st.selectbox("Select Season", years, index=len(years) - 1)
player_path = os.path.join(DATA_DIR, f"player_stats_{selected_year}.csv")
ps = safe_read_csv(player_path)

if ps.empty:
    st.warning("No player stats found for this season.")
    st.stop()

# ===============================================================
# LOAD STAT MAP & BUILD LIST OF AVAILABLE STATS
# ===============================================================
stat_map = load_stat_map()
core_stats = [
    "actual_points",
    "projected_points",
    "passing_yards",
    "passing_touchdowns",
    "rushing_yards",
    "rushing_touchdowns",
    "receptions",
    "receiving_yards",
    "receiving_touchdowns",
]

available_stats = [s for s in core_stats if s in ps.columns]
if not available_stats:
    # Fallback to all numeric stats
    available_stats = ps.select_dtypes("number").columns.tolist()

# Build friendly labels using the YAML map
display_names = {
    s: stat_map.get(s.replace("stat_", ""), s.replace("_", " ").title())
    for s in available_stats
}
selected_stat = st.selectbox("Select Stat to Rank By", options=available_stats, format_func=lambda x: display_names.get(x, x))

# ===============================================================
# FILTER & AGGREGATE
# ===============================================================
pos_filter = st.multiselect(
    "Filter by Position (optional)",
    sorted(ps["position"].dropna().unique()),
    default=None,
)

df = ps.copy()
if pos_filter:
    df = df[df["position"].isin(pos_filter)]

# Aggregate by player
top_players = (
    df.groupby(["player_name", "position"], dropna=False)[selected_stat]
    .sum()
    .reset_index()
    .sort_values(selected_stat, ascending=False)
    .head(20)
)

# ===============================================================
# DISPLAY RESULTS
# ===============================================================
st.subheader(f"Top 20 — {display_names.get(selected_stat, selected_stat).title()} ({selected_year})")
st.dataframe(top_players, use_container_width=True, height=380)

# --- Chart Visualization ---
fig = px.bar(
    top_players,
    x="player_name",
    y=selected_stat,
    color="position",
    title=f"Top 20 Players by {display_names.get(selected_stat, selected_stat).title()} — {selected_year}",
)
fig.update_layout(
    xaxis_title="Player",
    yaxis_title=display_names.get(selected_stat, selected_stat).title(),
    xaxis_tickangle=45,
    template="plotly_white",
)
st.plotly_chart(fig, use_container_width=True)

# ===============================================================
# FOOTER
# ===============================================================
st.caption("Data source: Yahoo Fantasy API — updated via fetch_yahoo_data.py")
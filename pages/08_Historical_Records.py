import pandas as pd
import streamlit as st
import os
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

st.set_page_config(page_title="📚 Historical Records", layout="wide")
st.title("📚 Historical Records")
st.caption("Highest and lowest weekly scores across all seasons")

DATA_DIR = "data"

scores_files = [f for f in os.listdir(DATA_DIR) if f.startswith("scores_") and f.endswith(".csv")]
if not scores_files:
    st.error("❌ No matchup files found.")
    st.stop()

dfs = []
for f in scores_files:
    df = pd.read_csv(os.path.join(DATA_DIR, f))
    if not df.empty:
        dfs.append(df)

df = pd.concat(dfs, ignore_index=True)

# --- Fix column names ---
if "points" in df.columns and "points_for" not in df.columns:
    df = df.rename(columns={"points": "points_for"})

# --- Compute best and worst weeks ---
best_week = df.sort_values("points_for", ascending=False).head(10)
worst_week = df.sort_values("points_for", ascending=True).head(10)

col1, col2 = st.columns(2)
with col1:
    st.markdown("### 🥇 Top 10 Highest Scores")
    st.dataframe(best_week[["season", "week", "team", "points_for", "opponent"]], hide_index=True, use_container_width=True)
with col2:
    st.markdown("### 💀 10 Lowest Scores")
    st.dataframe(worst_week[["season", "week", "team", "points_for", "opponent"]], hide_index=True, use_container_width=True)
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
st.set_page_config(page_title="🏈 Record Book", layout="wide")
st.title("🏈 GFN XV Record Book")
st.caption("Franchise records by wins, points, and streaks")

DATA_DIR = "data"
scores_files = [f for f in os.listdir(DATA_DIR) if f.startswith("scores_") and f.endswith(".csv")]

if not scores_files:
    st.error("❌ No matchup data found in /data.")
    st.stop()

dfs = []
for f in scores_files:
    df = pd.read_csv(os.path.join(DATA_DIR, f))
    if not df.empty:
        dfs.append(df)

df = pd.concat(dfs, ignore_index=True)

# --- Derived Columns ---
df["win"] = (df["points_for"] > df["points_against"]).astype(int)
df["loss"] = (df["points_for"] < df["points_against"]).astype(int)

# --- Franchise summaries ---
agg = df.groupby("team").agg(
    games=("week", "count"),
    wins=("win", "sum"),
    losses=("loss", "sum"),
    total_points=("points_for", "sum"),
    avg_points=("points_for", "mean"),
    avg_margin=(lambda x: (df.loc[x.index, "points_for"] - df.loc[x.index, "points_against"]).mean())
).reset_index()

agg["win_pct"] = (agg["wins"] / agg["games"]).round(3)

st.markdown("### 🏆 Franchise Summary")
st.dataframe(agg.sort_values("win_pct", ascending=False),
             use_container_width=True, hide_index=True)

# --- Top Franchise Records ---
st.markdown("### 🥇 Most Wins & High Scoring Teams")

most_wins = agg.sort_values("wins", ascending=False).head(5)
highest_avg = agg.sort_values("avg_points", ascending=False).head(5)

col1, col2 = st.columns(2)
with col1:
    st.metric("Most Wins", most_wins.iloc[0]["team"], f"{int(most_wins.iloc[0]['wins'])} Wins")
with col2:
    st.metric("Highest Avg Points", highest_avg.iloc[0]["team"], f"{highest_avg.iloc[0]['avg_points']:.1f} PPG")

st.info("💡 Record Book now automatically adapts to any number of seasons.")
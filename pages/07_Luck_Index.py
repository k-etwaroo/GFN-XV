import os
import pandas as pd
import numpy as np
import streamlit as st

# Shared helpers expected to exist in your repo
from tools.data_loader import (
    load_scores_all, load_scores_year, load_player_stats,
    load_franchise_map, attach_franchise, seasons_available
)
from components.header import render_header

st.set_page_config(page_title="🍀 Luck Index", layout="wide")
render_header("Goodell For Nothing XV")
import plotly.express as px

st.title("🍀 Luck Index")

seasons = seasons_available("data")
if not seasons: st.info("Add scores files."); st.stop()
season = st.selectbox("Season", sorted(seasons), index=len(seasons)-1)
df = load_scores_year(season)
if df.empty:
    st.warning("No data."); st.stop()

required_cols = {"team", "points_for", "points_against", "week"}
missing = required_cols - set(df.columns)
if missing:
    st.error(
        f"Missing columns {missing} in scores for season {season}; this usually means scores_{season}.csv is empty or malformed. "
        "Try re-running your data sync or temporarily removing the bad file."
    )
    st.stop()

exp = []
for w, g in df.groupby("week"):
    s = g[["team","points_for"]].copy()
    for _, r in s.iterrows():
        exp.append({"team": r["team"], "exp": (s["points_for"] < r["points_for"]).sum()/max(len(s)-1,1)})
exp = pd.DataFrame(exp).groupby("team", as_index=False)["exp"].mean().rename(columns={"exp":"expected_win_pct"})

df["win_val"] = (df["points_for"] > df["points_against"]).map(lambda x: 1.0 if x else 0.0)
act = df.groupby("team", as_index=False)["win_val"].mean().rename(columns={"win_val":"actual_win_pct"})
luck = exp.merge(act, on="team", how="left")
luck["luck"] = luck["actual_win_pct"] - luck["expected_win_pct"]
st.dataframe(luck.sort_values("luck", ascending=False), hide_index=True, width="stretch")

fig = px.scatter(luck, x="expected_win_pct", y="actual_win_pct", text="team", title=f"Luck Map — {season}")
st.plotly_chart(
    fig,
    width="stretch",
    key="luck_index_scatter",
)

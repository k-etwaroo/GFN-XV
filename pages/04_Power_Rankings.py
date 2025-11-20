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

st.set_page_config(page_title="🏆 Power Rankings", layout="wide")
render_header("Goodell For Nothing XV")

st.title("🏆 Power Rankings & Luck")

seasons = seasons_available("data")
if not seasons: st.error("No scores files found."); st.stop()
season = st.selectbox("Season", sorted(seasons), index=len(seasons)-1)
df = load_scores_year(season)
if df.empty:
    st.warning("No matchup data."); st.stop()

frmap = load_franchise_map()
df = attach_franchise(df, frmap)

required_cols = {"points_for", "points_against", "week", "team", "manager"}
missing = required_cols - set(df.columns)
if missing:
    st.error(
        f"Missing columns {missing} in scores for season {season}; this usually means scores_{season}.csv is empty or malformed. "
        "Try re-running your data sync or temporarily removing the bad file."
    )
    st.stop()

df["win"] = (df["points_for"] > df["points_against"]).astype(int)
df["loss"] = (df["points_for"] < df["points_against"]).astype(int)

exp_rows = []
for w, g in df.groupby("week"):
    scores = g[["team","points_for"]].reset_index(drop=True)
    for _, r in scores.iterrows():
        exp_rows.append({"team": r["team"], "expected": (scores["points_for"] < r["points_for"]).sum()/max(len(scores)-1,1)})
exp = pd.DataFrame(exp_rows).groupby("team", as_index=False)["expected"].sum().rename(columns={"expected":"expected_wins"})

tbl = (df.groupby(["team","manager","logo_url","felo_tier"], dropna=False)
         .agg(wins=("win","sum"), losses=("loss","sum"),
              pf=("points_for","sum"), pa=("points_against","sum"),
              games=("week","count"), avg_pf=("points_for","mean"))
         .reset_index()
)
tbl = tbl.merge(exp, on="team", how="left")
tbl["win_pct"] = tbl["wins"]/tbl["games"]
tbl["luck_index"] = tbl["wins"] - tbl["expected_wins"]
tbl["power_score"] = tbl["avg_pf"]*0.6 + (tbl["win_pct"]*100)*0.3 + tbl["luck_index"]*5

tbl = tbl.sort_values("power_score", ascending=False).reset_index(drop=True)
tbl["rank"] = np.arange(1, len(tbl)+1)

st.dataframe(tbl[[ "rank","team","manager","wins","losses","win_pct","avg_pf","luck_index","power_score"]].round(3),
             hide_index=True, width="stretch")

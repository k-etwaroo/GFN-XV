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

st.set_page_config(page_title="📊 Franchise History", layout="wide")
render_header("Goodell For Nothing XV")
import plotly.express as px

st.title("📊 Franchise Power Index — Multi-Year")

scores = load_scores_all()
if scores.empty:
    st.info("No combined scores found."); st.stop()

frmap = load_franchise_map()
scores = attach_franchise(scores, frmap)

required_cols = {"points_for", "points_against", "week", "season", "team", "manager"}
missing = required_cols - set(scores.columns)
if missing:
    st.error(
        f"Missing columns {missing} in combined scores; this usually means one of the scores_*.csv files is empty or malformed. "
        "Try re-running your data sync or temporarily removing the bad file."
    )
    st.stop()

scores["win"] = (scores["points_for"] > scores["points_against"]).astype(int)
summary = (scores.groupby(["season","team","manager"], dropna=False)
                 .agg(games=("week","count"),
                      wins=("win","sum"),
                      pf=("points_for","sum"),
                      pa=("points_against","sum"),
                      avg_pf=("points_for","mean"))
                 .reset_index())
summary["win_pct"] = summary["wins"]/summary["games"]
max_season = summary["season"].max()
summary["recency_weight"] = summary["season"].apply(lambda s: 0.9**(max_season - s))
summary["power"] = summary["avg_pf"]*0.6 + summary["win_pct"]*60 + 0.4*(summary["pf"]-summary["pa"])/summary["games"]

st.subheader("Power over time")
teams = (
    summary["team"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)
team = st.selectbox("Team (optional)", ["All"] + sorted(teams))
metric = st.selectbox("Metric", ["power","win_pct","avg_pf"])

data = summary if team=="All" else summary[summary["team"]==team]
fig = px.line(data, x="season", y=metric, color=None if team!="All" else "team", markers=True)
st.plotly_chart(
    fig,
    width="stretch",
    key="franchise_power_chart",
)

legacy = (summary.groupby(["team","manager"], dropna=False)
          .apply(lambda x: np.average(x["power"], weights=x["recency_weight"]))
          .reset_index(name="legacy_index")
         ).sort_values("legacy_index", ascending=False).reset_index(drop=True)
legacy["rank"] = np.arange(1, len(legacy)+1)
st.subheader("🏛️ Legacy Index (recency-weighted)")
st.dataframe(legacy[["rank","team","manager","legacy_index"]].round(2), hide_index=True, width="stretch")

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

st.set_page_config(page_title="📊 Advanced Analytics", layout="wide")
render_header("Goodell For Nothing XV")
import altair as alt

st.title("📊 Advanced Analytics — Efficiency & Luck")

scores = load_scores_all()
if scores.empty: st.info("No scores found."); st.stop()

required = {"season","week","team","points_for"}
if not required.issubset(set(scores.columns)):
    st.error(f"Missing required columns: {required - set(scores.columns)}"); st.stop()

proj_col = "projected_points" if "projected_points" in scores.columns else None
if proj_col is None:
    st.info("Projected points not found. Some charts will be limited.")

if proj_col:
    scores["luck"] = scores["points_for"] - scores[proj_col]
    with np.errstate(divide="ignore", invalid="ignore"):
        scores["efficiency"] = scores["points_for"] / scores[proj_col]
else:
    scores["luck"] = np.nan
    scores["efficiency"] = np.nan

with st.sidebar:
    seasons = sorted(scores["season"].unique())
    season_choice = st.multiselect("Season(s)", seasons, default=seasons[-1:])
    teams = sorted(scores["team"].dropna().unique().tolist())
    team_choice = st.multiselect("Team(s)", teams, default=teams)

if season_choice:
    scores = scores[scores["season"].isin(season_choice)]
if team_choice:
    scores = scores[scores["team"].isin(team_choice)]

summary = (
    scores.dropna(subset=["points_for"])
          .groupby(["season","team"], dropna=False)
          .agg(games=("week","nunique"),
               avg_points=("points_for","mean"),
               avg_luck=("luck","mean"),
               eff=("efficiency","mean"),
               consistency=("points_for","std"))
          .reset_index()
)
summary["consistency"] = summary["consistency"].fillna(0.0)
summary["power"] = summary["avg_points"]*0.6 + summary["eff"].fillna(0)*30 + summary["avg_luck"].fillna(0)*0.3 - summary["consistency"]*0.1

c1,c2 = st.columns(2)
with c1:
    st.subheader("Top Efficiency")
    st.dataframe(summary.sort_values("eff", ascending=False).head(5).round(3), hide_index=True, width="stretch")
with c2:
    st.subheader("Top Power")
    st.dataframe(summary.sort_values("power", ascending=False).head(5).round(3), hide_index=True, width="stretch")

if proj_col:
    st.subheader("Luck by Week")
    chart = (alt.Chart(scores.dropna(subset=["luck"]))
             .mark_circle(size=80, opacity=0.7)
             .encode(x="week:O", y="luck:Q", color="team:N",
                     tooltip=["season","team","week","points_for",proj_col,"luck"])
             .properties(height=320).interactive())
    st.altair_chart(chart, use_container_width=True)

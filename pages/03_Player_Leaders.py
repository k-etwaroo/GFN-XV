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

st.set_page_config(page_title="🏅 Player Leaders", layout="wide")
render_header("Goodell For Nothing XV")

st.title("🏅 Player Leaders")

seasons = seasons_available("data", pattern="player_stats_*.csv")
if not seasons:
    st.info("Add player_stats_<YEAR>.csv to /data."); st.stop()

season = st.selectbox("Season", sorted(seasons), index=len(seasons)-1)
ps = load_player_stats(season=season)
if ps.empty:
    st.warning("No player stats found."); st.stop()

if "actual_points" not in ps.columns:
    st.info("This page needs 'actual_points' in player_stats. Re-run fetch to include player totals."); st.stop()

st.subheader(f"Top 20 Scorers — {season}")
top = (ps.groupby(["player_name","position"], dropna=False)["actual_points"]
         .sum().reset_index()
         .sort_values("actual_points", ascending=False).head(20))
st.dataframe(top, hide_index=True, width="stretch")

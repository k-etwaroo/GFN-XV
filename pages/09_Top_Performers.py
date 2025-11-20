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

st.set_page_config(page_title="🌟 Top Performers", layout="wide")
render_header("Goodell For Nothing XV")

st.title("🌟 Top Performers (Players)")

seasons = seasons_available("data", pattern="player_stats_*.csv")
if not seasons: st.info("Add player_stats files."); st.stop()
season = st.selectbox("Season", sorted(seasons), index=len(seasons)-1)
ps = load_player_stats(season=season)
if ps.empty: st.warning("No player stats."); st.stop()

if "actual_points" not in ps.columns:
    st.info("Player stats missing 'actual_points'. Re-run fetch."); st.stop()

st.subheader("Top 20 single-week (players)")
topw = ps.sort_values("actual_points", ascending=False).head(20)
cols = ["player_name","position","team","week","actual_points"]
st.dataframe(topw[[c for c in cols if c in topw.columns]], hide_index=True, width="stretch")

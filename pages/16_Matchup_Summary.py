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

st.set_page_config(page_title="📅 Matchup Summary", layout="wide")
render_header("Goodell For Nothing XV")
import plotly.express as px

st.title("📅 Matchup Summary")

seasons = seasons_available("data")
if not seasons: st.info("No scores files."); st.stop()
season = st.selectbox("Season", sorted(seasons), index=len(seasons)-1)
df = load_scores_year(season)
if df.empty:
    st.warning("No data."); st.stop()

required_cols = {"week", "team", "manager", "opponent", "points_for", "points_against"}
missing = required_cols - set(df.columns)
if missing:
    st.error(
        f"Missing columns {missing} in scores for season {season}; this usually means scores_{season}.csv is empty or malformed. "
        "Try re-running your data sync or temporarily removing the bad file."
    )
    st.stop()

week = st.selectbox("Week", sorted(df["week"].unique()), index=len(df["week"].unique())-1)
wk = df[df["week"]==week].copy()
wk["margin"] = wk["points_for"] - wk["points_against"]

st.subheader(f"Week {week} — All Matchups")
st.dataframe(wk[["team","manager","opponent","points_for","points_against","margin"]].sort_values("points_for", ascending=False),
             hide_index=True, width="stretch")

df = df.sort_values(["team","week"])
df["pf_ma3"] = df.groupby("team")["points_for"].transform(lambda s: s.rolling(3, min_periods=1).mean())
wk_mom = df[df["week"]==week][["team","pf_ma3"]].sort_values("pf_ma3", ascending=False)
st.subheader("🔥 Momentum (3-week avg points)")
st.dataframe(wk_mom, hide_index=True, width="stretch")

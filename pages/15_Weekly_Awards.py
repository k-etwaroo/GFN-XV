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

st.set_page_config(page_title="🏅 Weekly Awards", layout="wide")
render_header("Goodell For Nothing XV")

st.title("🏅 Weekly Awards")

seasons = seasons_available("data")
if not seasons: st.info("Add scores files."); st.stop()
season = st.selectbox("Season", sorted(seasons), index=len(seasons)-1)
df = load_scores_year(season)
if df.empty:
    st.warning("No data."); st.stop()

required_cols = {"week", "team", "manager", "points_for", "points_against"}
missing = required_cols - set(df.columns)
if missing:
    st.error(
        f"Missing columns {missing} in scores for season {season}; this usually means scores_{season}.csv is empty or malformed. "
        "Try re-running your data sync or temporarily removing the bad file."
    )
    st.stop()

week = st.selectbox("Week", sorted(df["week"].unique()), index=0)
wk = df[df["week"]==week].copy()
wk["margin"] = wk["points_for"] - wk["points_against"]

awards = {
    "High Score": wk.loc[wk["points_for"].idxmax()][["team","manager","points_for"]].to_dict(),
    "Low Score": wk.loc[wk["points_for"].idxmin()][["team","manager","points_for"]].to_dict(),
    "Biggest Blowout": wk.loc[wk["margin"].idxmax()][["team","manager","margin"]].to_dict()
}
for name, vals in awards.items():
    st.write(f"**{name}** — {vals}")

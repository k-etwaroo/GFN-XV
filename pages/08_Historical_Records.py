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

st.set_page_config(page_title="📚 Historical Records", layout="wide")
render_header("Goodell For Nothing XV")

st.title("📚 Historical Records")

scores = load_scores_all()
if scores.empty: st.info("No scores found."); st.stop()

best = scores.sort_values("points_for", ascending=False).head(10)
worst = scores.sort_values("points_for", ascending=True).head(10)
margin = (scores.assign(margin=scores["points_for"]-scores["points_against"])
                .sort_values("margin", ascending=False).head(10))
st.subheader("Top 10 Team Weeks (Points)")
st.dataframe(best[["season","week","team","manager","points_for","opponent"]], hide_index=True, width="stretch")
st.subheader("Lowest 10 Team Weeks (Points)")
st.dataframe(worst[["season","week","team","manager","points_for","opponent"]], hide_index=True, width="stretch")
st.subheader("Largest 10 Blowouts (Margin)")
st.dataframe(margin[["season","week","team","manager","margin","opponent"]], hide_index=True, width="stretch")

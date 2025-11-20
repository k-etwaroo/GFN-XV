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

st.set_page_config(page_title="📓 Record Book", layout="wide")
render_header("Goodell For Nothing XV")

st.title("📓 Record Book — All Time")

scores = load_scores_all()
if scores.empty: st.info("No scores."); st.stop()

scores["margin"] = scores["points_for"] - scores["points_against"]
st.subheader("Highest Team Weeks")
st.dataframe(scores.sort_values("points_for", ascending=False).head(25)[["season","week","team","manager","points_for","opponent"]],
             hide_index=True, width="stretch")

st.subheader("Biggest Blowouts (Margin)")
st.dataframe(scores.sort_values("margin", ascending=False).head(25)[["season","week","team","manager","margin","opponent"]],
             hide_index=True, width="stretch")

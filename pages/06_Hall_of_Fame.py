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

st.set_page_config(page_title="🏛️ Hall of Fame", layout="wide")
render_header("Goodell For Nothing XV")

st.title("🏛️ Hall of Fame")

scores = load_scores_all()
if scores.empty:
    st.info("Add multiple seasons of scores_<YEAR>.csv to populate."); st.stop()

scores["win_val"] = (scores["points_for"] > scores["points_against"]).map(lambda x: 1.0 if x else 0.0)
champs = (scores.groupby(["season","team"], as_index=False)["win_val"].sum()
               .sort_values(["season","win_val"], ascending=[True, False])
               .groupby("season", as_index=False).head(1))
st.subheader("Season Champions (by wins proxy)")
st.dataframe(champs, hide_index=True, width="stretch")

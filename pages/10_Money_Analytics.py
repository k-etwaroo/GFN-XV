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

st.set_page_config(page_title="🧾 Money Analytics", layout="wide")
render_header("Goodell For Nothing XV")

st.title("🧾 Money Analytics")
st.info("Connect Google Sheets in a later step. For now, this page is a placeholder.")

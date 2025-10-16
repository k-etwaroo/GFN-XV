import os
import streamlit as st
import pandas as pd
from tools.data_loader import load_scores_all, load_franchise, attach_franchise

scores = load_scores_all()
frmap = load_franchise_map()
scores = attach_franchise(scores, frmap)

if scores.empty:
    st.warning("No scores found in /data yet.")
    st.stop()

# Common filters
all_seasons = sorted(scores["season"].dropna().unique().tolist())
season = st.sidebar.selectbox("Season", ["All"] + all_seasons, index=len(all_seasons))
view = scores if season == "All" else scores[scores["season"] == season]

st.set_page_config(page_title="🧾 Money Analytics", layout="wide")
st.title("🧾 Money Analytics — Goodell For Nothing XV")

st.caption("Uses Google Sheet: 'GFN Money'.")
st.write("See the 💸 *Payout Leaderboard* tab for full ROI & category breakdowns.")

if "money" not in st.secrets:
    st.error(
        "Missing Google Sheets credentials in `.streamlit/secrets.toml`.\n\nExample:\n```toml\n[money]\nsheet_name = \"GFN Money\"\n```")

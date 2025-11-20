# app.py — GFN XV Dashboard
import streamlit as st
import pandas as pd
import os
import subprocess
from components.header import render_header
from tools.data_loader import (
    load_data_universal,
    load_franchise_map,
)

# ----------------------------
# 🔧 CONFIGURATION
# ----------------------------
st.set_page_config(
    page_title="GFN XV Dashboard",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------
# 🧩 LOAD CORE DATASETS
# ----------------------------
data_dir = "data"

# Use the universal loader (returns all seasons)
scores_df, players_df = load_data_universal(data_dir=data_dir)

# Derive available seasons from the scores dataframe
if not scores_df.empty and "season" in scores_df.columns:
    years = sorted(scores_df["season"].dropna().unique().tolist())
else:
    years = []

selected_year = years[-1] if years else 2025

# Franchise map and logos
frmap = load_franchise_map(data_dir=data_dir)
logos_path = os.path.join(data_dir, "team_logos.json")

# ----------------------------
# 🔁 REFRESH DATA BUTTON
# ----------------------------
st.markdown("### 🔄 Data Controls")
if st.button("Fetch Latest Yahoo Data"):
    with st.spinner("Fetching data from Yahoo Fantasy API..."):
        try:
            subprocess.run(["python3", "fetch_yahoo_data.py"], check=True)
            st.success("✅ Data refreshed successfully! Please reload the app.")
        except Exception as e:
            st.error(f"❌ Error fetching data: {e}")

# ----------------------------
# 🕒 SYNC FULL HISTORY
# ----------------------------
st.markdown("### 📚 Historical Sync")

if st.button("🔄 Sync Full Yahoo History"):
    with st.spinner("Syncing all historical Yahoo data..."):
        try:
            # 1) Fetch raw history
            fetch = subprocess.run(
                ["python3", "scripts/fetch_historical_data.py"],
                capture_output=True,
                text=True
            )

            # 2) Validate raw history
            validate = subprocess.run(
                ["python3", "scripts/validate_historical_data.py"],
                capture_output=True,
                text=True
            )

            # 3) Process into combined tables
            process = subprocess.run(
                ["python3", "scripts/process_historical_data.py"],
                capture_output=True,
                text=True
            )

            st.success("✅ Historical sync complete!")

            with st.expander("Fetch Log"):
                st.code(fetch.stdout + fetch.stderr, language="bash")
            with st.expander("Validation Log"):
                st.code(validate.stdout + validate.stderr, language="bash")
            with st.expander("Processing Log"):
                st.code(process.stdout + process.stderr, language="bash")

        except Exception as e:
            st.error(f"❌ Error during historical sync: {e}")

# ----------------------------
# 🏈 HEADER
# ----------------------------
render_header("GFN XV League Dashboard")

# ----------------------------
# 🚀 AUTO-REDIRECT TO LEAGUE OVERVIEW
# ----------------------------
if "redirected" not in st.session_state:
    st.session_state.redirected = True
    st.switch_page("pages/01_League_Overview.py")

# ----------------------------
# DATA VALIDATION & FEEDBACK
# ----------------------------
if scores_df.empty:
    st.error("❌ No score data found. Please ensure `scores_<year>.csv` exists in `/data/`.")
else:
    st.success(f"✅ Loaded {len(scores_df)} score records for {selected_year}")

if players_df.empty:
    st.warning("⚠️ Player data missing — please run `fetch_yahoo_data.py` to generate `player_stats_<year>.csv`.")
else:
    st.success(f"✅ Loaded {len(players_df)} player stats for {selected_year}")

if not os.path.exists(logos_path):
    st.warning("⚠️ Team logos not found. Ensure `team_logos.json` exists in the `/data/` directory.")
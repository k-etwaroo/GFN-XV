import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
from components.header import render_header

st.set_page_config(page_title="🏅 Record Book", layout="wide")
render_header("Goodell For Nothing XV")
st.title("🏅 Record Book — All-Time Highlights")

DATA_DIR = "data"
combined_path = os.path.join(DATA_DIR, "combined_seasons_scores.csv")
current_path = os.path.join(DATA_DIR, "scores_2025.csv")

# --- Load data ---
if os.path.exists(combined_path):
    df = pd.read_csv(combined_path)
elif os.path.exists(current_path):
    df = pd.read_csv(current_path)
else:
    st.error("❌ No matchup data found. Run fetch_yahoo_data.py first.")
    st.stop()

if df.empty:
    st.warning("No data available.")
    st.stop()

# --- Clean numeric fields ---
for c in ["points_for", "points_against"]:
    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)

# --- Derived columns ---
df["margin"] = df["points_for"] - df["points_against"]
df["total_pts"] = df["points_for"] + df["points_against"]

# --- Season filter ---
if "season" in df.columns:
    seasons = sorted(df["season"].unique())
    selected_season = st.selectbox(
        "Select Season", ["All-Time"] + [str(s) for s in seasons])
    if selected_season != "All-Time":
        df = df[df["season"] == int(selected_season)]

# --- Compute Records ---
records = {
    "Highest Team Score": df.loc[df["points_for"].idxmax()],
    "Lowest Team Score": df.loc[df["points_for"].idxmin()],
    "Largest Blowout": df.loc[df["margin"].idxmax()],
    "Closest Win": df.loc[df["margin"][df["margin"] > 0].idxmin()],
    "Highest Combined Total": df.loc[df["total_pts"].idxmax()],
}

# --- Display ---
st.subheader("🏆 All-Time (or Season) Records")

for label, rec in records.items():
    st.markdown(f"### {label}")
    cols = st.columns([1, 3, 3])
    with cols[0]:
        if pd.notna(rec.get("logo_url")) and str(rec["logo_url"]).startswith("http"):
            st.image(rec["logo_url"], width=80)
        else:
            st.markdown("🏈")
    with cols[1]:
        st.markdown(
            f"**Team:** {rec['team']}  \n**Manager:** {rec.get('manager', '')}  ")
        st.markdown(
            f"**Opponent:** {rec['opponent']}  \n**Week:** {rec['week']}")
        if "season" in rec:
            st.markdown(f"**Season:** {int(rec['season'])}")
    with cols[2]:
        st.metric(
            label="Points For",
            value=f"{rec['points_for']:.2f}",
            delta=f"vs {rec['points_against']:.2f}",
        )
    st.divider()

# --- Bonus chart: Top 10 single-game scores ---
st.subheader("🔥 Top 10 Single-Game Scores")
top10 = df.nlargest(10, "points_for")[
    ["season", "week", "team", "points_for", "opponent"]]
fig = px.bar(
    top10,
    x="team",
    y="points_for",
    color="season" if "season" in df.columns else None,
    hover_data=["opponent", "week"],
    title="Top 10 Highest Scoring Performances",
)
st.plotly_chart(fig, use_container_width=True)

st.caption("Data: Yahoo Fantasy API → fetch_yahoo_data.py")

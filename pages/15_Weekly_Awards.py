import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
from components.header import render_header

st.set_page_config(page_title="🏅 Weekly Awards", layout="wide")
render_header("Goodell For Nothing XV")
st.title("🏅 Weekly Awards — GFN XV")

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

# --- Numeric cleanup ---
for c in ["points_for", "points_against"]:
    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)

df["margin"] = df["points_for"] - df["points_against"]

# --- Season selector ---
if "season" in df.columns:
    seasons = sorted(df["season"].unique())
    selected_season = st.selectbox(
        "Select Season", ["All-Time"] + [str(s) for s in seasons])
    if selected_season != "All-Time":
        df = df[df["season"] == int(selected_season)]

weeks = sorted(df["week"].unique())
selected_week = st.selectbox(
    "Select Week", ["All Weeks"] + [str(w) for w in weeks])

if selected_week != "All Weeks":
    df = df[df["week"] == int(selected_week)]

# --- Awards per week ---


def weekly_awards(df):
    awards = []
    for week, wk in df.groupby("week"):
        wk = wk.copy()
        wk["margin"] = wk["points_for"] - wk["points_against"]

        if wk.empty:
            continue

        def safe_row(metric, func, label):
            try:
                return wk.loc[func(wk[metric]), :].assign(Award=label)
            except Exception:
                return pd.DataFrame()

        winners = [
            safe_row("points_for", lambda s: s.idxmax(), "Team of the Week 🥇"),
            safe_row("points_for", lambda s: s.idxmin(), "Lowest Score 💀"),
            safe_row("margin", lambda s: s.idxmax(), "Biggest Win 💥"),
        ]

        close_games = wk[wk["margin"] > 0]
        if not close_games.empty:
            winners.append(close_games.loc[close_games["margin"].idxmin(
            ), :].to_frame().T.assign(Award="Closest Game 🧊"))

        losers = wk[wk["points_for"] < wk["points_against"]]
        if not losers.empty:
            winners.append(losers.loc[losers["points_for"].idxmax(
            ), :].to_frame().T.assign(Award="Unluckiest Loss 💩"))

        all_awards = pd.concat(winners, ignore_index=True)
        all_awards["week"] = week
        awards.append(all_awards)

    return pd.concat(awards, ignore_index=True) if awards else pd.DataFrame()


awards_df = weekly_awards(df)

if awards_df.empty:
    st.warning("No awards available for the selected filters.")
    st.stop()

# --- Display Weekly Awards ---
st.subheader("🏆 Weekly Awards Summary")

if selected_week == "All Weeks":
    weeks_to_show = awards_df["week"].unique()[::-1]
else:
    weeks_to_show = [int(selected_week)]

for week in weeks_to_show:
    wk_df = awards_df[awards_df["week"] == week]
    st.markdown(f"### Week {int(week)}")
    for _, row in wk_df.iterrows():
        cols = st.columns([1, 3, 2])
        with cols[0]:
            if pd.notna(row.get("logo_url")) and str(row["logo_url"]).startswith("http"):
                st.image(row["logo_url"], width=70)
            else:
                st.markdown("🏈")
        with cols[1]:
            st.markdown(f"**{row['Award']}** — {row['team']}")
            st.markdown(f"🆚 {row['opponent']}  |  {row.get('manager', '')}")
        with cols[2]:
            st.metric("Points", f"{row['points_for']:.2f}",
                      delta=f"vs {row['points_against']:.2f}")
    st.divider()

# --- Bonus chart: Top 10 weekly scores ---
st.subheader("🔥 Top 10 Weekly Scores (All Weeks)")
top10 = df.nlargest(10, "points_for")[
    ["season", "week", "team", "points_for", "opponent"]]
fig = px.bar(
    top10,
    x="team",
    y="points_for",
    color="week",
    hover_data=["opponent", "season"],
    title="Top 10 Single-Week Performances",
)
st.plotly_chart(fig, use_container_width=True)

st.caption("Generated dynamically from Yahoo Fantasy matchups.")

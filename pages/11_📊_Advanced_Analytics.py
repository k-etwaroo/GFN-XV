import os
import numpy as np
import pandas as pd
import altair as alt
import streamlit as st
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

st.set_page_config(page_title="Advanced Analytics", layout="wide")

DATA_DIR = "data"
COMBINED = os.path.join(DATA_DIR, "combined_seasons_scores.csv")
CURRENT = os.path.join(DATA_DIR, "scores_2025.csv")

# Prefer combined; it lacks projected_points, so we’ll keep rows that have it when present
if os.path.exists(COMBINED):
    df = pd.read_csv(COMBINED)
else:
    df = pd.read_csv(CURRENT)

# Normalize
for c in ["points_for", "points_against", "projected_points"]:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

df["season"] = pd.to_numeric(df["season"], errors="coerce").astype("Int64")
df["week"] = pd.to_numeric(df["week"], errors="coerce").astype("Int64")

has_proj = "projected_points" in df.columns and df["projected_points"].notna(
).any()

if not has_proj:
    st.warning(
        "No projected_points available in this dataset. Showing limited analytics (actual points only).")

st.title("📈 Advanced Analytics — Efficiency & Luck")
st.caption("Goodell For Nothing XV")

# Filters
with st.sidebar:
    st.header("Filters")
    seasons = sorted([int(x) for x in df["season"].dropna().unique()])
    season_choice = st.multiselect(
        "Season(s)", seasons, default=seasons[-1:] if seasons else [])
    teams = sorted(df["team"].dropna().unique().tolist())
    team_choice = st.multiselect("Team(s)", teams, default=teams)

if season_choice:
    df = df[df["season"].isin(season_choice)]
if team_choice:
    df = df[df["team"].isin(team_choice)]

df["points_for"] = pd.to_numeric(df["points_for"], errors="coerce").fillna(0.0)

if has_proj:
    df["luck"] = df["points_for"] - df["projected_points"]
    df["efficiency"] = np.where(
        df["projected_points"] > 0, df["points_for"]/df["projected_points"], np.nan)
else:
    df["luck"] = np.nan
    df["efficiency"] = np.nan

# Summary (only rows with efficiency when available)
base = df.dropna(subset=["efficiency"]) if has_proj else df.copy()
summary = (
    base.groupby(["season", "team"], dropna=False)
    .agg(
        games=("week", "nunique"),
        avg_points=("points_for", "mean"),
        avg_proj=("projected_points", "mean") if has_proj else (
            "points_for", "mean"),
        avg_luck=("luck", "mean"),
        eff=("efficiency", "mean"),
        consistency=("points_for", "std"),
    ).reset_index()
)
summary["consistency"] = summary["consistency"].fillna(0.0)
summary["power"] = (
    summary["avg_points"]*0.6 +
    (summary["eff"]*100).fillna(0)*0.25 +
    (summary["avg_luck"]).fillna(0)*0.1 -
    summary["consistency"]*0.05
)

left, right = st.columns(2)
with left:
    st.subheader("Top Teams by Power")
    st.dataframe(summary.sort_values("power", ascending=False).head(5).round(3),
                 hide_index=True, width="stretch")
with right:
    st.subheader("Top Teams by Avg Points")
    st.dataframe(summary.sort_values("avg_points", ascending=False).head(5).round(3),
                 hide_index=True, width="stretch")

st.divider()

st.subheader("🎯 Luck by Week (Actual - Projected)")
if has_proj and df["luck"].notna().any():
    luck_chart = (
        alt.Chart(df.dropna(subset=["luck"]))
        .mark_circle(size=80, opacity=0.7)
        .encode(
            x=alt.X("week:O", title="Week"),
            y=alt.Y("luck:Q", title="Luck (Pts Above/Below Projection)"),
            color=alt.Color("team:N", legend=None),
            tooltip=["season", "team", "week",
                     "points_for", "projected_points", "luck"],
        )
        .properties(height=320)
        .interactive()
    )
    st.altair_chart(luck_chart, use_container_width=True)
else:
    st.info("Not enough projected data to plot luck.")

st.subheader("⚡ Efficiency Over Time")
if has_proj and df["efficiency"].notna().any():
    eff_chart = (
        alt.Chart(df.dropna(subset=["efficiency"]))
        .mark_line(point=True)
        .encode(
            x=alt.X("week:O", title="Week"),
            y=alt.Y("efficiency:Q", title="Efficiency (Actual / Projected)"),
            color=alt.Color("team:N", legend=None),
            tooltip=["season", "team", "week", "efficiency",
                     "points_for", "projected_points"],
        )
        .properties(height=320)
        .interactive()
    )
    st.altair_chart(eff_chart, use_container_width=True)
else:
    st.info("Not enough projected data to plot efficiency.")

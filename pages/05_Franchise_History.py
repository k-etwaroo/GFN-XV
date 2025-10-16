import os
import numpy as np
import pandas as pd
import plotly.express as px
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

st.set_page_config(page_title="Franchise History", layout="wide")

DATA_DIR = "data"
COMBINED = os.path.join(DATA_DIR, "combined_seasons_scores.csv")
if not os.path.exists(COMBINED):
    st.error(
        "No combined_seasons_scores.csv found. Create it (or add multiple scores_<year>.csv).")
    st.stop()

df = pd.read_csv(COMBINED)
if df.empty:
    st.warning("Combined file is empty.")
    st.stop()

# Normalize
for c in ["points_for", "points_against"]:
    df[c] = pd.to_numeric(df.get(c), errors="coerce").fillna(0.0)
df["win"] = (df["points_for"] > df["points_against"]).astype(int)
df["loss"] = (df["points_for"] < df["points_against"]).astype(int)

st.title("📊 Franchise Power Index — Multi-Year View")
st.caption("Goodell For Nothing XV — Historical Metrics Dashboard")

summary = (
    df.groupby(["season", "team", "manager"], dropna=False)
      .agg(
          games=("week", "count"),
          wins=("win", "sum"),
          losses=("loss", "sum"),
          points_for=("points_for", "sum"),
          points_against=("points_against", "sum"),
    ).reset_index()
)
summary["win_pct"] = np.where(
    summary["games"] > 0, summary["wins"]/summary["games"], 0.0)
summary["avg_points"] = np.where(
    summary["games"] > 0, summary["points_for"]/summary["games"], 0.0)
summary["pf_diff"] = summary["points_for"] - summary["points_against"]

# Luck Index (season-relative)
season_means = summary.groupby(
    "season")["points_for"].transform("mean").replace(0, np.nan)
summary["expected_wins"] = np.where(
    season_means.notna(),
    (summary["points_for"]/season_means) * (summary["games"] /
                                            summary.groupby("season")["team"].transform("count")),
    0.0,
)
summary["luck_index"] = summary["wins"] - summary["expected_wins"]

summary["power_score"] = (
    (summary["avg_points"] * 0.6)
    + (summary["win_pct"] * 100 * 0.3)
    + (summary["luck_index"] * 10 * 0.1)
)

# Filters
teams = sorted(summary["team"].dropna().unique())
seasons = sorted(summary["season"].dropna().unique())

c1, c2 = st.columns(2)
with c1:
    selected_team = st.selectbox("Select a team", ["All Teams"] + list(teams))
with c2:
    metric_name = st.selectbox(
        "Select metric", ["Power Score", "Win %", "Average Points", "Luck Index"])

metric_map = {"Power Score": "power_score", "Win %": "win_pct",
              "Average Points": "avg_points", "Luck Index": "luck_index"}
mcol = metric_map[metric_name]

st.subheader(f"📈 {metric_name} by Season")
plot_df = summary if selected_team == "All Teams" else summary[summary["team"] == selected_team]
fig = px.line(plot_df, x="season", y=mcol, color="team", markers=True,
              title=f"{metric_name} over time" + ("" if selected_team == "All Teams" else f" — {selected_team}"))
fig.update_layout(template="plotly_white", hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

st.subheader("🍀 Historical Luck Trends")
fig2 = px.box(summary, x="season", y="luck_index", points="all",
              color="season", title="Luck Index by Season")
fig2.update_layout(template="plotly_white")
st.plotly_chart(fig2, use_container_width=True)

st.subheader("🏆 Power Rankings by Season")
rankings = summary.copy()
rankings["rank"] = rankings.groupby(
    "season")["power_score"].rank(ascending=False, method="first")
rank_table = rankings.sort_values(["season", "rank"])
st.dataframe(
    rank_table[["season", "rank", "team", "manager", "wins",
                "losses", "avg_points", "power_score"]].round(3),
    hide_index=True, use_container_width=True
)

st.markdown("---")
st.subheader("🏛️ Franchise Legacy Index — All-Time Power Ranking")
max_season = summary["season"].max()
summary["recency_weight"] = summary["season"].apply(
    lambda s: 0.9 ** (max_season - s))

legacy = (
    summary.groupby(["team", "manager"], dropna=False)
           .apply(lambda x: np.average(x["power_score"], weights=x["recency_weight"]))
           .reset_index(name="legacy_index")
           .sort_values("legacy_index", ascending=False)
           .reset_index(drop=True)
)
legacy["rank"] = np.arange(1, len(legacy)+1)

fig3 = px.bar(
    legacy, x="team", y="legacy_index", color="legacy_index",
    color_continuous_scale="sunset", title="🏆 All-Time Franchise Legacy Index"
)
fig3.update_layout(template="plotly_white", height=550)
st.plotly_chart(fig3, use_container_width=True)

st.dataframe(legacy[["rank", "team", "manager", "legacy_index"]].round(
    3), hide_index=True, use_container_width=True)
st.caption("Data source: Yahoo Fantasy API — updated via fetch_yahoo_data.py")

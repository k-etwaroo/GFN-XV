import os
import pandas as pd
import streamlit as st
import plotly.express as px
import numpy as np

st.set_page_config(page_title="📊 Matchup Summary & Power Rankings", layout="wide")
st.title("📊 Matchup Summary — GFN XV")
st.caption("Power Rankings, Luck Index, Consistency, Momentum & Weekly Trends")

DATA_DIR = "data"
scores_path = os.path.join(DATA_DIR, "scores_2025.csv")

# ===============================================================
# LOAD & VALIDATE DATA
# ===============================================================
if not os.path.exists(scores_path):
    st.error("❌ No matchup data found. Please run fetch_yahoo_data.py first.")
    st.stop()

df = pd.read_csv(scores_path)
if df.empty:
    st.warning("No matchup data available yet.")
    st.stop()

# Basic cleanup
df = df.dropna(subset=["team", "points_for", "points_against"])
df["points_for"] = df["points_for"].astype(float)
df["points_against"] = df["points_against"].astype(float)
df["projected_points"] = df.get("projected_points", 0.0)
df["margin"] = df["points_for"] - df["points_against"]
df["win"] = (df["points_for"] > df["points_against"]).astype(int)
df["luck_diff"] = df["points_for"] - df["projected_points"]

# ===============================================================
# 🍀 LUCK INDEX
# ===============================================================
st.subheader("🍀 Luck Index — Actual vs. Expected Performance")

luck_df = (
    df.groupby(["team", "manager"], as_index=False)
    .agg({
        "points_for": "mean",
        "projected_points": "mean",
        "luck_diff": "mean",
        "win": "mean",
    })
)
luck_df["Luck Index"] = luck_df["luck_diff"].round(2)
luck_df["Win %"] = (luck_df["win"] * 100).round(1)

fig_luck = px.bar(
    luck_df.sort_values("Luck Index", ascending=False),
    x="team",
    y="Luck Index",
    color="Luck Index",
    color_continuous_scale=["#e74c3c", "#2ecc71"],
    title="Luck Index (Points Above/Below Projection)",
)
st.plotly_chart(fig_luck, use_container_width=True)

# ===============================================================
# ⚖️ CONSISTENCY INDEX
# ===============================================================
st.subheader("⚖️ Consistency Index — Week-to-Week Stability")

consistency_df = (
    df.groupby(["team", "manager"], as_index=False)
    .agg({"points_for": ["mean", "std"], "projected_points": ["mean", "std"]})
)
consistency_df.columns = ["team", "manager", "actual_mean", "actual_std", "proj_mean", "proj_std"]

consistency_df["Consistency Score"] = (1 / (1 + consistency_df["actual_std"])).round(3)
consistency_df["Profile"] = consistency_df["Consistency Score"].apply(
    lambda x: "🧊 Ice Cold" if x > 0.9 else ("⚖️ Steady" if x > 0.7 else ("🎢 Boom-or-Bust" if x > 0.5 else "💥 Chaotic"))
)

st.dataframe(
    consistency_df[["team", "manager", "Consistency Score", "Profile", "actual_std"]],
    use_container_width=True,
    height=320,
)

# ===============================================================
# 🏆 POWER INDEX (COMPOSITE RANKING)
# ===============================================================
st.subheader("🏆 Power Index — Composite Team Strength")

power_df = (
    df.groupby(["team", "manager"], as_index=False)
    .agg({
        "points_for": "mean",
        "points_against": "mean",
        "projected_points": "mean",
        "luck_diff": "mean",
    })
)

power_df = power_df.merge(consistency_df[["team", "Consistency Score"]], on="team", how="left")
win_rates = df.groupby("team")["win"].mean().reset_index().rename(columns={"win": "win_rate"})
power_df = power_df.merge(win_rates, on="team", how="left")

# Normalize + Weighted Composite
for col in ["points_for", "Consistency Score", "luck_diff", "win_rate"]:
    min_val, max_val = power_df[col].min(), power_df[col].max()
    power_df[f"{col}_norm"] = (power_df[col] - min_val) / (max_val - min_val) if max_val != min_val else 0.5

power_df["Power Index"] = (
    0.40 * power_df["points_for_norm"]
    + 0.25 * power_df["win_rate_norm"]
    + 0.20 * power_df["Consistency Score_norm"]
    + 0.15 * ((power_df["luck_diff_norm"]) * 0.5 + 0.5)
)
power_df["Power Rank"] = power_df["Power Index"].rank(ascending=False, method="min").astype(int)
power_df = power_df.sort_values("Power Rank")

st.dataframe(
    power_df[["Power Rank", "team", "manager", "Power Index", "points_for", "win_rate", "Consistency Score", "luck_diff"]],
    use_container_width=True,
    height=400,
)

fig_power = px.bar(
    power_df,
    x="team",
    y="Power Index",
    color="Power Rank",
    color_continuous_scale="blues",
    title="GFN XV Power Index — Overall Team Strength",
)
fig_power.update_layout(xaxis_title="Team", yaxis_title="Power Index (0–1 Scale)")
st.plotly_chart(fig_power, use_container_width=True)

# ===============================================================
# 📈 WEEKLY POWER TREND
# ===============================================================
st.subheader("📈 Power Rank Trend — Week-by-Week Progression")

trend_records = []
for week, wdf in df.groupby("week"):
    temp = (
        wdf.groupby(["team", "manager"], as_index=False)
        .agg({"points_for": "mean", "points_against": "mean", "projected_points": "mean"})
    )
    temp["margin"] = temp["points_for"] - temp["points_against"]
    temp["efficiency"] = (temp["points_for"] / temp["projected_points"]).clip(upper=2)
    temp["Power Index"] = 0.5 * temp["points_for"] + 0.3 * temp["margin"] + 0.2 * temp["efficiency"] * 100
    temp["week"] = week
    trend_records.extend(temp.to_dict(orient="records"))

trend_df = pd.DataFrame(trend_records)
if trend_df.empty:
    st.info("No weekly matchup data found yet. Play a few weeks to see Power Trends!")
    st.stop()

trend_df["Power Index (norm)"] = trend_df.groupby("week")["Power Index"].transform(
    lambda x: (x - x.min()) / (x.max() - x.min()) if x.max() != x.min() else 0.5
)
trend_df["Power Rank"] = trend_df.groupby("week")["Power Index"].rank(ascending=False, method="min").astype(int)

# Trend chart
all_teams = ["All Teams"] + sorted(trend_df["team"].unique())
selected_team = st.selectbox("Filter by Team", all_teams, index=0)
display_df = trend_df if selected_team == "All Teams" else trend_df[trend_df["team"] == selected_team]

fig_trend = px.line(
    display_df,
    x="week",
    y="Power Rank",
    color="team",
    markers=True,
    title="📊 Weekly Power Rank Trend",
    color_discrete_sequence=px.colors.qualitative.Bold,
)
fig_trend.update_yaxes(autorange="reversed", title="Power Rank (1 = Best)")
st.plotly_chart(fig_trend, use_container_width=True)

# ===============================================================
# ⚡ MOMENTUM SCORE (3-WEEK MOVING AVERAGE)
# ===============================================================
st.subheader("⚡ Momentum Score — 3-Week Weighted Power Trend")

trend_df["Momentum"] = (
    trend_df.groupby("team")["Power Index (norm)"].transform(lambda x: x.rolling(3, min_periods=1).mean())
)
momentum_latest = (
    trend_df.sort_values("week").groupby("team").tail(1)[["team", "Momentum", "Power Index (norm)", "Power Rank"]]
)
momentum_latest["Momentum %"] = (momentum_latest["Momentum"] * 100).round(1)
momentum_latest = momentum_latest.sort_values("Momentum", ascending=False)

fig_momentum = px.bar(
    momentum_latest,
    x="team",
    y="Momentum",
    color="Momentum",
    color_continuous_scale="Viridis",
    title="Current Momentum — Rolling 3-Week Power Index Trend",
)
st.plotly_chart(fig_momentum, use_container_width=True)

# ===============================================================
# 🧱 POWER MOVERS (Week-over-Week Changes)
# ===============================================================
st.subheader("🧱 Power Movers — Biggest Risers & Fallers")

trend_df["Rank Change"] = trend_df.groupby("team")["Power Rank"].diff(-1) * -1
movers = (
    trend_df.groupby("team", as_index=False)
    .agg({"Rank Change": "mean", "Power Rank": "last"})
    .sort_values("Rank Change", ascending=False)
)

movers["Trend"] = movers["Rank Change"].apply(
    lambda x: "📈 Rising" if x > 0 else ("📉 Falling" if x < 0 else "➖ Steady")
)

st.dataframe(
    movers[["team", "Rank Change", "Trend", "Power Rank"]],
    use_container_width=True,
    height=300,
)

# ===============================================================
# 🎨 POWER HEATMAP
# ===============================================================
st.subheader("🎨 Power Index Heatmap — Team vs. Week")

heatmap_df = trend_df.pivot(index="team", columns="week", values="Power Index (norm)").fillna(0)
fig_heatmap = px.imshow(
    heatmap_df,
    color_continuous_scale="RdYlGn",
    title="Power Index Heatmap — Each Team’s Week-to-Week Strength",
    aspect="auto",
)
fig_heatmap.update_layout(xaxis_title="Week", yaxis_title="Team")
st.plotly_chart(fig_heatmap, use_container_width=True)

st.caption("""
🏈 **Power Index Dashboard Summary**
- *Power Index*: weighted by Points, Wins, Consistency & Luck  
- *Momentum*: 3-week moving average of normalized Power Index  
- *Power Movers*: identifies biggest week-to-week risers/fallers  
- *Heatmap*: visual overview of team dominance by week
""")

from components.header import render_header, render_footer

# ... your page code ...

render_footer()
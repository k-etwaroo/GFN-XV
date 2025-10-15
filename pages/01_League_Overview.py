import pandas as pd
import streamlit as st
import os
import matplotlib.pyplot as plt

st.set_page_config(page_title="League Overview", layout="wide")
st.title("🏆 League Overview — GFN XV")
st.caption("Season summary, Power Rankings, and Luck Index insights")

DATA_DIR = "data"
scores_path = os.path.join(DATA_DIR, "scores_2025.csv")

# -----------------------------
# Load Data
# -----------------------------
if not os.path.exists(scores_path):
    st.error("❌ No matchup data found. Run fetch_yahoo_data.py first.")
    st.stop()

df = pd.read_csv(scores_path)
if df.empty:
    st.warning("No matchup data found. Run fetch_yahoo_data.py first.")
    st.stop()

# Ensure numeric
for c in ["points_for", "points_against"]:
    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)

# -----------------------------
# Compute Metrics
# -----------------------------
df["win"] = (df["points_for"] > df["points_against"]).astype(int)
df["loss"] = (df["points_for"] < df["points_against"]).astype(int)
df["margin"] = df["points_for"] - df["points_against"]
df["weekly_power"] = df["points_for"] * 0.6 + df["margin"] * 0.4

agg = df.groupby("team", dropna=False).agg(
    games=("week", "count"),
    wins=("win", "sum"),
    losses=("loss", "sum"),
    points_for=("points_for", "sum"),
    points_against=("points_against", "sum"),
    avg_points=("points_for", "mean"),
    avg_margin=("margin", "mean"),
).reset_index()

agg["win_pct"] = agg["wins"] / agg["games"]

# Expected Wins (all-play method)
expected_wins = []
for week, group in df.groupby("week"):
    for _, row in group.iterrows():
        expected = (group["points_for"] < row["points_for"]
                    ).sum()  # exclude self
        expected_wins.append({
            "team": row["team"],
            "week": week,
            "expected_win_equiv": expected / (len(group) - 1)
        })
expected_df = pd.DataFrame(expected_wins)
exp_sum = expected_df.groupby("team")["expected_win_equiv"].sum().reset_index()
exp_sum.rename(columns={"expected_win_equiv": "expected_wins"}, inplace=True)

agg = agg.merge(exp_sum, on="team", how="left")
agg["luck_index"] = agg["wins"] - agg["expected_wins"]

# Power Rank
agg["power_score"] = (
    0.6 * agg["avg_points"].rank(ascending=False, method="min")
    + 0.4 * agg["avg_margin"].rank(ascending=False, method="min")
)
agg["power_rank"] = agg["power_score"].rank(ascending=True, method="min")

# -----------------------------
# Top Callouts
# -----------------------------
top_teams = agg.sort_values("power_rank").head(3)
luckiest = agg.loc[agg["luck_index"].idxmax()]
unluckiest = agg.loc[agg["luck_index"].idxmin()]

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("### 🥇 Top 3 Power Teams")
    for _, row in top_teams.iterrows():
        st.write(
            f"**{int(row['power_rank'])}. {row['team']}** — {row['avg_points']:.1f} PPG")

with col2:
    st.markdown("### 🍀 Luckiest Manager")
    st.metric(luckiest["team"], f"+{luckiest['luck_index']:.2f} wins")

with col3:
    st.markdown("### 💀 Unluckiest Manager")
    st.metric(unluckiest["team"], f"{unluckiest['luck_index']:.2f} wins")

st.divider()

# -----------------------------
# League Summary Table
# -----------------------------
st.markdown("### 📊 League Summary (Power & Luck)")

summary_cols = [
    "power_rank", "team", "wins", "losses", "win_pct", "points_for",
    "points_against", "avg_points", "avg_margin", "expected_wins", "luck_index",
]
st.dataframe(
    agg.sort_values("power_rank")[summary_cols].round(2),
    hide_index=True,
    width="stretch"
)

# -----------------------------
# Luck Index Visualization
# -----------------------------
st.markdown("### 🍀 Luck Index Distribution")

fig, ax = plt.subplots(figsize=(7, 4))
sorted_df = agg.sort_values("luck_index", ascending=True)
ax.barh(
    sorted_df["team"],
    sorted_df["luck_index"],
    color=["#B22222" if x < 0 else "#228B22" for x in sorted_df["luck_index"]],
    edgecolor="black",
)
ax.axvline(0, color="black", linewidth=1)
ax.set_xlabel("Luck Index (Wins – Expected Wins)")
ax.set_title("Luck Index Across Teams", fontsize=13, weight="bold")
st.pyplot(fig)

st.info("💡 Includes Power Rank, Win%, and Luck Index — your at-a-glance league health check.")

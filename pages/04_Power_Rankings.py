import os
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Power Rankings", layout="wide")

DATA_DIR = "data"
CURRENT = os.path.join(DATA_DIR, "scores_2025.csv")
if not os.path.exists(CURRENT):
    st.error("No scores_2025.csv found. Run fetch_yahoo_data.py first.")
    st.stop()

df = pd.read_csv(CURRENT)
if df.empty:
    st.warning("No matchup data found in scores_2025.csv.")
    st.stop()

# Normalize
df["points_for"] = pd.to_numeric(df["points_for"], errors="coerce").fillna(0.0)
df["points_against"] = pd.to_numeric(
    df["points_against"], errors="coerce").fillna(0.0)
df["projected_points"] = pd.to_numeric(
    df.get("projected_points"), errors="coerce")

df["win"] = (df["points_for"] > df["points_against"]).astype(int)
df["loss"] = (df["points_for"] < df["points_against"]).astype(int)
df["result"] = np.where(df["win"] == 1, "W",
                        np.where(df["loss"] == 1, "L", "T"))

st.title("🏆 Power Rankings & Luck Index")
st.caption("Goodell For Nothing XV — Automated League Metrics (2025)")

team_summary = (
    df.groupby(["team", "manager", "felo_tier", "logo_url"], dropna=False)
      .agg(
          games=("week", "count"),
          wins=("win", "sum"),
          losses=("loss", "sum"),
          points_for=("points_for", "sum"),
          points_against=("points_against", "sum"),
    ).reset_index()
)
team_summary["avg_points"] = team_summary["points_for"] / team_summary["games"]
team_summary["win_pct"] = team_summary["wins"] / team_summary["games"]

avg_pf = team_summary["points_for"].mean() if len(team_summary) else 0.0
team_summary["expected_wins"] = np.where(
    avg_pf > 0,
    team_summary["points_for"] / avg_pf *
    (team_summary["games"] / len(team_summary)),
    0.0,
)
team_summary["luck_index"] = team_summary["wins"] - \
    team_summary["expected_wins"]

team_summary["power_score"] = (
    (team_summary["avg_points"] * 0.6)
    + (team_summary["win_pct"] * 100 * 0.3)
    + (team_summary["luck_index"] * 10 * 0.1)
)

team_summary = team_summary.sort_values(
    "power_score", ascending=False).reset_index(drop=True)
team_summary["rank"] = np.arange(1, len(team_summary) + 1)

st.subheader("🏈 League Power Rankings")
for _, row in team_summary.iterrows():
    col1, col2, col3 = st.columns([1, 5, 3])
    with col1:
        if pd.notna(row["logo_url"]) and str(row["logo_url"]).startswith("http"):
            st.image(row["logo_url"], width=70)
        else:
            st.markdown("🏈")
    with col2:
        st.markdown(f"### {row['rank']}. {row['team']}")
        st.markdown(f"**Manager:** {row['manager']}")
        if pd.notna(row["felo_tier"]) and row["felo_tier"]:
            st.markdown(f"**Tier:** {str(row['felo_tier']).title()}")
    with col3:
        st.metric("Power Score", f"{row['power_score']:.1f}",
                  delta=f"Luck {row['luck_index']:+.1f}")
    st.divider()

with st.expander("📊 Full Stats Table"):
    st.dataframe(
        team_summary[
            ["rank", "team", "manager", "felo_tier", "wins",
                "losses", "avg_points", "luck_index", "power_score"]
        ].round(3),
        hide_index=True, width="stretch",
    )
from components.header import render_header, render_footer

# ... your page code ...

render_footer()
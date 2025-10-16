import streamlit as st
import pandas as pd
from tools.loaders import load_all_scores, load_league_map
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
st.set_page_config(page_title="🏅 Hall of Fame", layout="wide")
st.title("🏅 Hall of Fame — All-Time Greats")

# --- Load data ---
df = load_all_scores()
if df.empty:
    st.warning("No matchup data found.")
    st.stop()

league_map = load_league_map()
league_name = next(iter(league_map.values()))["name"] if league_map else "League"

st.caption(f"{league_name} | {df['season'].min()} – {df['season'].max()} Seasons")

# --- Season filter ---
years = sorted(df["season"].unique())
multi_select = st.multiselect("Filter by Seasons", years, default=years)

df = df[df["season"].isin(multi_select)]

# --- Derived stats ---
df["win"] = (df["points_for"] > df["points_against"]).astype(int)
df["loss"] = (df["points_for"] < df["points_against"]).astype(int)
df["margin"] = df["points_for"] - df["points_against"]

agg = df.groupby("team").agg(
    games=("week", "count"),
    wins=("win", "sum"),
    losses=("loss", "sum"),
    points_for=("points_for", "sum"),
    points_against=("points_against", "sum"),
    avg_margin=("margin", "mean"),
).reset_index()

agg["win_pct"] = (agg["wins"] / agg["games"]).round(3)
agg["hof_score"] = (agg["wins"] * 2) + (agg["avg_margin"] / 10)
agg = agg.sort_values("hof_score", ascending=False)

st.subheader("🏆 All-Time Win Leaders")
st.dataframe(
    agg[["team", "games", "wins", "losses", "win_pct", "avg_margin", "hof_score"]].round(2),
    use_container_width=True,
    hide_index=True
)
import streamlit as st
import pandas as pd
import json
import os
from tools.data_loader import load_data_universal
from tools.fetch_nfl_matchups import should_refresh, fetch_nfl_matchups

# -------------------------------
# Page Config
# -------------------------------
st.set_page_config(page_title="GFN XV Dashboard", layout="wide")

DATA_DIR = "data"
SCORES_FILE = os.path.join(DATA_DIR, "scores_2025.csv")
TEAM_LOGOS_FILE = os.path.join(DATA_DIR, "team_logos.json")
NFL_FILE = os.path.join(DATA_DIR, "nfl_weekly_matchups.json")

# -------------------------------
# Load Data
# -------------------------------
df_scores = load_data_universal("scores", year=2025, data_dir=DATA_DIR)
if df_scores.empty:
    st.error("❌ No scores data found. Run fetch_yahoo_data.py first.")
    st.stop()

# Load team logos
TEAM_LOGOS = {}
if os.path.exists(TEAM_LOGOS_FILE):
    with open(TEAM_LOGOS_FILE, "r") as f:
        TEAM_LOGOS = json.load(f)

# Refresh NFL data if needed
if should_refresh(NFL_FILE, days=3):
    fetch_nfl_matchups()

with open(NFL_FILE, "r") as f:
    nfl_matchups = json.load(f)


# -------------------------------
# Calculate League Standings
# -------------------------------
def calculate_standings(scores_df: pd.DataFrame):
    """Calculate standings from per-game scores dataframe."""
    if scores_df is None or scores_df.empty:
        return pd.DataFrame()

    # Work on a copy so we don't mutate the cached dataframe
    df = scores_df.copy()

    # Normalize points column for backwards compatibility
    if "points" not in df.columns:
        if "points_for" in df.columns:
            df["points"] = df["points_for"]
        elif "pf" in df.columns:
            df["points"] = df["pf"]
        else:
            st.error("Scores data is missing a 'points' or 'points_for' column.")
            return pd.DataFrame()

    # Normalize team name column (older/newer schemas may differ)
    if "team_name" not in df.columns:
        if "team" in df.columns:
            df["team_name"] = df["team"]
        else:
            st.error("Scores data is missing a 'team_name' or 'team' column.")
            return pd.DataFrame()

    # Only include completed weeks
    weeks = sorted(df["week"].unique())
    completed_weeks = []
    for w in weeks:
        week_df = df[df["week"] == w]
        if all(week_df["points"] > 0):
            completed_weeks.append(w)

    teams = df["team_name"].unique()
    records = {t: {"W": 0, "L": 0, "PF": 0, "PA": 0, "results": []} for t in teams}

    for w in completed_weeks:
        week_df = df[df["week"] == w].reset_index(drop=True)
        for i in range(0, len(week_df), 2):
            if i + 1 >= len(week_df):
                continue
            t1, t2 = week_df.loc[i], week_df.loc[i + 1]
            records[t1["team_name"]]["PF"] += t1["points"]
            records[t1["team_name"]]["PA"] += t2["points"]
            records[t2["team_name"]]["PF"] += t2["points"]
            records[t2["team_name"]]["PA"] += t1["points"]
            if t1["points"] > t2["points"]:
                records[t1["team_name"]]["W"] += 1
                records[t2["team_name"]]["L"] += 1
                records[t1]["results"].append("W")
                records[t2]["results"].append("L")
            else:
                records[t2["team_name"]]["W"] += 1
                records[t1["team_name"]]["L"] += 1
                records[t2["team_name"]]["results"].append("W")
                records[t1["team_name"]]["results"].append("L")

    def get_streak(results):
        if not results:
            return "-"
        current = results[-1]
        count = 1
        for r in reversed(results[:-1]):
            if r == current:
                count += 1
            else:
                break
        return f"{current}{count}"

    standings = []
    for team, rec in records.items():
        logo = TEAM_LOGOS.get(team, "")
        standings.append({
            "Logo": logo,
            "Team": team,
            "W": rec["W"],
            "L": rec["L"],
            "PF": round(rec["PF"], 2),
            "PA": round(rec["PA"], 2),
            "Streak": get_streak(rec["results"])
        })

    df_out = pd.DataFrame(standings).sort_values(by=["W", "PF"], ascending=[False, False])
    return df_out


standings_df = calculate_standings(df_scores)


# -------------------------------
# Page Layout
# -------------------------------
st.title("🏈 GFN XV — 2025 League Dashboard")

# --- Fantasy Matchup Ticker ---
st.markdown("### 🎞️ Weekly Fantasy Matchups")
ticker_items = []
for week in sorted(df_scores["week"].unique()):
    week_df = df_scores[df_scores["week"] == week]
    for i in range(0, len(week_df), 2):
        if i + 1 >= len(week_df):
            continue
        t1 = week_df.iloc[i]
        t2 = week_df.iloc[i + 1]
        ticker_items.append(f"{t1['team_name']} vs {t2['team_name']}")

ticker_html = " • ".join(ticker_items)
st.markdown(
    f"""
    <div style="white-space: nowrap; overflow-x: hidden; padding: 16px 20px; margin-bottom: 25px;
                border-radius: 10px; background: rgb(255,200,0);
                color: #000; font-weight: 900; font-size: 30px; text-transform: uppercase;
                box-shadow: 0 0 25px rgba(255,200,0,0.5);">
        <marquee behavior="scroll" direction="left" scrollamount="5">{ticker_html}</marquee>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("---")

# --- League Highlights ---
st.markdown("### 🪙 League Highlights")

top_team = standings_df.iloc[0]
top_team_name = top_team["Team"]
top_team_record = f"{top_team['W']}-{top_team['L']}"
top_team_pf = top_team["PF"]

highest_pf_team = standings_df.loc[standings_df["PF"].idxmax()]
luck_placeholder = "🔮 Coming soon"

tile_style = """
    background: rgba(255,215,0,0.1);
    border-radius: 14px;
    padding: 16px 18px;
    margin-bottom: 12px;
    box-shadow: 0 0 20px rgba(255,200,0,0.3);
    border: 1px solid rgba(255,215,0,0.3);
    font-weight: bold;
"""

st.markdown(
    f"""
    <div style="display:flex; gap:20px; justify-content:space-between; flex-wrap:wrap;">
        <div style="{tile_style}; flex:1; min-width:220px;">
            <h4>🥇 Power Rankings Leader</h4>
            <p><b>{top_team_name}</b> — {top_team_record} (PF: {top_team_pf})</p>
        </div>
        <div style="{tile_style}; flex:1; min-width:220px;">
            <h4>🍀 Luck Index</h4>
            <p>{luck_placeholder}</p>
        </div>
        <div style="{tile_style}; flex:1; min-width:220px;">
            <h4>💥 Highest Scoring Team</h4>
            <p><b>{highest_pf_team['Team']}</b> — {highest_pf_team['PF']} pts</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Layout: Standings + NFL Matchups ---
col1, col2 = st.columns([0.68, 0.32], gap="large")

with col1:
    st.markdown("### 🏆 League Standings")

    styled_df = standings_df.style.format({
        "Logo": lambda x: f"<img src='{x}' width='40'>" if x else "",
    }).set_table_styles([
        {"selector": "th", "props": [("background-color", "rgba(255,215,0,0.2)"), ("font-weight", "bold")]},
        {"selector": "td", "props": [("padding", "8px"), ("text-align", "center"), ("font-size", "14px")]}
    ], overwrite=False).hide(axis="index")

    st.markdown("<div style='overflow-x:auto;'>", unsafe_allow_html=True)
    st.markdown(styled_df.to_html(escape=False), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("### 🏈 NFL Week Matchups")
    for game in nfl_matchups:
        st.markdown(
            f"""
            <div style="
                background: rgb(255,200,0);
                border-radius: 14px;
                padding: 14px 18px;
                margin-bottom: 12px;
                box-shadow: 0 0 20px rgba(255,200,0,0.4);
                color: #000;
                font-weight: bold;
            ">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div style="flex:1; text-align:center;">
                        <img src="{game['away_logo']}" width="40"><br>
                        <b>{game['away_abbr']}</b><br>
                        <small>{game['away_record']}</small>
                    </div>
                    <div style="flex:1; text-align:center;">
                        <b>vs</b><br>
                        <small>{game.get('broadcast', '')}</small>
                    </div>
                    <div style="flex:1; text-align:center;">
                        <img src="{game['home_logo']}" width="40"><br>
                        <b>{game['home_abbr']}</b><br>
                        <small>{game['home_record']}</small>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

st.markdown("---")
st.caption("GFN XV Fantasy League © 2025 — Live Yahoo + NFL Integration")
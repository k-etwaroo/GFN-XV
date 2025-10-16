import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
st.set_page_config(page_title="🍀 Luck Index", layout="wide")
st.title("🍀 Luck Index")
DATA_DIR = "data"
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

def safe_read_csv(p):
    try:
        return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def list_years(prefix):
    years = []
    for f in os.listdir(DATA_DIR):
        if f.startswith(prefix) and f.split("_")[1].split(".")[0].isdigit():
            years.append(int(f.split("_")[1].split(".")[0]))
    return sorted(years)


years = list_years("scores_")
if not years:
    st.info("Add scores files.")
    st.stop()

y = st.selectbox("Season", years, index=len(years)-1)
sc = safe_read_csv(os.path.join(DATA_DIR, f"scores_{y}.csv"))
if sc.empty:
    st.warning("No data.")
    st.stop()

required = {"team", "week", "points_for", "points_against"}
missing = required - set(sc.columns)
if missing:
    st.error(f"Missing columns: {missing}")
    st.stop()

# derive results
sc["win_val"] = np.where(sc["points_for"] > sc["points_against"], 1.0,
                         np.where(sc["points_for"] < sc["points_against"], 0.0, 0.5))

teams = sorted(sc['team'].dropna().unique())
weeks = sorted(sc['week'].dropna().unique())

# expected win % by all-play each week
expected = {t: 0.0 for t in teams}
for w in weeks:
    wk = sc[sc['week'] == w][["team", "points_for"]]
    # for each team: count how many teams it outscored this week
    for t, pts in wk.values:
        expected[t] += (wk["points_for"] < pts).sum() + 0.5*(wk["points_for"]
                                                             # half credit for ties, exclude self
                                                             == pts).sum() - 0.5

max_allplay_per_week = len(teams) - 1 if len(teams) > 1 else 1
total_possible = max_allplay_per_week * \
    len(weeks) if max_allplay_per_week > 0 else 1
exp_pct = {t: (expected[t]/total_possible) for t in teams}

actual = sc.groupby('team', as_index=False)['win_val'].mean().rename(
    columns={'win_val': 'actual_win_pct'})
luck = pd.DataFrame({'team': teams, 'expected_win_pct': [
                    exp_pct[t] for t in teams]}).merge(actual, on='team', how='left')
luck['luck'] = luck['actual_win_pct'] - luck['expected_win_pct']

st.dataframe(luck.sort_values('luck', ascending=False),
             use_container_width=True, height=420)
fig = px.scatter(luck, x='expected_win_pct', y='actual_win_pct', text='team',
                 title=f"Luck Map — {y}",
                 labels={"expected_win_pct": "Expected Win % (All-Play)", "actual_win_pct": "Actual Win %"})
fig.update_traces(textposition="top center")
st.plotly_chart(fig, use_container_width=True)

import re
import os
import pandas as pd
import streamlit as st
import plotly.express as px
from components.header import render_header

st.set_page_config(page_title="🏅 Player Leaders", layout="wide")
render_header("Goodell For Nothing XV")
st.title("🏅 Player Leaders")

DATA_DIR = "data"


def safe_read_csv(p):
    return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()


# 🔧 FIXED SECTION (replaces your old years = sorted([...]) line)
years = sorted([
    int(m.group(1))
    for f in os.listdir(DATA_DIR)
    if (m := re.match(r"player_stats_(\d{4})\.csv$", f))
])

# 🔧 END FIXED SECTION

if not years:
    st.info("Add `player_stats_<YEAR>.csv` to /data.")
    st.stop()

y = st.selectbox("Season", years, index=len(years)-1)
ps = safe_read_csv(os.path.join(DATA_DIR, f"player_stats_{y}.csv"))
if ps.empty:
    st.warning("No player stats found.")
    st.stop()

# If you haven’t added actual player scoring yet, don’t crash:
if "actual_points" not in ps.columns:
    st.info("This view needs 'actual_points' in player_stats. Page will stay quiet until you add it.")
    st.stop()

st.subheader("Top 20 by Total Points")
top = (
    ps.groupby(['player_name', 'position'], as_index=False)['actual_points']
    .sum()
    .sort_values('actual_points', ascending=False)
    .head(20)
)
st.dataframe(top, use_container_width=True, height=380)

fig = px.bar(
    top,
    x='player_name',
    y='actual_points',
    color='position',
    title=f"Top Scorers — {y}"
)
st.plotly_chart(fig, use_container_width=True)

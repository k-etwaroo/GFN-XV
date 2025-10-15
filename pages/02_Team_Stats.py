import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import os

st.set_page_config(page_title="Team Stats", layout="wide")
st.title("🏈 Team Stats Dashboard")
st.caption("Goodell For Nothing XV — Team Rosters, Managers, and Logos")

DATA_DIR = "data"
player_path = os.path.join(DATA_DIR, "player_stats_2025.csv")

if not os.path.exists(player_path):
    st.error("Player data not found. Run fetch_yahoo_data.py first.")
    st.stop()


@st.cache_data(ttl=600)
def load_players(p):
    return pd.read_csv(p)


df = load_players(player_path)
if df.empty:
    st.warning("No player data available.")
    st.stop()

position_col = "selected_position" if "selected_position" in df.columns else "position"
df[position_col] = df[position_col].fillna("Unknown")

# -----------------------------
# Sidebar Controls
# -----------------------------
st.sidebar.title("Global Dashboard Controls")
show_percent = st.sidebar.toggle("Show Percentages", value=True)
compact_view = st.sidebar.toggle("Compact View (Smaller Charts)", value=True)

# -----------------------------
# League-Wide Breakdown
# -----------------------------
st.markdown("### 🏆 League-Wide Position Breakdown")
position_counts = df[position_col].value_counts().sort_values(ascending=True)
total_players = position_counts.sum()

figsize = (5.5, 2.5) if compact_view else (7, 4)
fig, ax = plt.subplots(figsize=figsize)
bars = ax.barh(position_counts.index, position_counts.values,
               color="#FFD700", edgecolor="#000")

ax.set_title("Total Players per Position Across the League",
             fontsize=11, weight="bold")
ax.set_xlabel("Players", fontsize=9)
ax.grid(axis="x", linestyle="--", alpha=0.4)
ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

for bar, pos in zip(bars, position_counts.index):
    width = bar.get_width()
    pct = width / total_players * 100
    label = f"{int(width)} ({pct:.1f}%)" if show_percent else f"{int(width)}"
    ax.text(width + 0.3, bar.get_y() + bar.get_height()/2,
            label, va="center", fontsize=8.5, weight="bold")

st.pyplot(fig)
st.divider()

# -----------------------------
# Team Breakdown
# -----------------------------
for team_name, group in df.groupby("team"):
    manager = group["manager"].iloc[0]
    logo = group["logo_url"].iloc[0] if "logo_url" in group.columns else ""
    felo = group["manager_felo"].iloc[0].title() if "manager_felo" in group.columns and pd.notna(
        group["manager_felo"].iloc[0]) else "N/A"
    manager_pic = group["manager_image"].iloc[0] if "manager_image" in group.columns else ""

    with st.container():
        cols = st.columns([1, 4])
        with cols[0]:
            if logo:
                st.image(logo, width=90)
            else:
                st.markdown("🏈")
        with cols[1]:
            st.markdown(f"### {team_name}")
            st.markdown(f"**Manager:** {manager}")
            st.markdown(f"**Tier:** {felo}")
            if manager_pic:
                st.image(manager_pic, width=60, caption=manager)

        # Stats
        roster_size = len(group)
        positions = group[position_col].nunique()
        pos_list = ", ".join(sorted(group[position_col].unique()))
        st.markdown(
            f"**Roster Size:** {roster_size} **Unique Positions:** {positions} ({pos_list})")

        # Chart
        counts = group[position_col].value_counts()
        fig, ax = plt.subplots(
            figsize=(5.5, 2.5) if compact_view else (6.5, 3.5))
        bars = ax.barh(counts.index, counts.values,
                       color="#FFD700", edgecolor="#000")
        ax.set_title("Position Breakdown", fontsize=11, weight="bold")
        ax.grid(axis="x", linestyle="--", alpha=0.5)
        for bar, pos in zip(bars, counts.index):
            width = bar.get_width()
            pct = width / counts.sum() * 100
            label = f"{int(width)} ({pct:.1f}%)" if show_percent else f"{int(width)}"
            ax.text(width + 0.1, bar.get_y() + bar.get_height()/2,
                    label, va="center", fontsize=8.5, weight="bold")
        st.pyplot(fig)

        with st.expander("Show Roster"):
            st.dataframe(group[["player_name", position_col, "eligible_positions"]],
                         hide_index=True, use_container_width=True)
        st.divider()

from components.header import render_header, render_footer

# ... your page code ...

render_footer()
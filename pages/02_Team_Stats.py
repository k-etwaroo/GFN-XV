import streamlit as st
import pandas as pd
import plotly.express as px
from tools.data_loader import load_player_stats, seasons_available

# Load latest available player stats automatically
DATA_DIR = "data"
years = seasons_available(DATA_DIR)
latest_year = max(years) if years else 2025
ps_latest = load_player_stats(DATA_DIR, latest_year)

if ps_latest is None or ps_latest.empty:
    st.error(f"⚠️ No player stats found in {DATA_DIR}. Please run fetch_yahoo_data.py or check your data folder.")
else:
    latest_week = ps_latest["week"].max()
    ps_latest = ps_latest[ps_latest["week"] == latest_week]

    teams = sorted(ps_latest["team_name"].dropna().unique())

    color_map = {
        "QB": "#F4A261",
        "RB": "#2A9D8F",
        "WR": "#E76F51",
        "TE": "#F9C74F",
        "FLEX": "#90BE6D",
        "K": "#577590",
        "DEF": "#B5838D"
    }
    order = ["QB", "RB", "WR", "TE", "FLEX", "K", "DEF"]

    # Iterate over teams in pairs for two cards per row
    for i in range(0, len(teams), 2):
        cols = st.columns(2)
        for j in range(2):
            idx = i + j
            if idx >= len(teams):
                break
            team = teams[idx]
            g = ps_latest[ps_latest["team_name"] == team].copy()

            logo = g["team_logo"].iloc[0] if "team_logo" in g.columns and pd.notna(g["team_logo"].iloc[0]) else ""
            manager_name = g["manager_name"].iloc[0] if "manager_name" in g.columns and pd.notna(g["manager_name"].iloc[0]) else None

            # Compute roster composition
            comp = (
                g["position"]
                .replace({"D/ST": "DEF", "DST": "DEF"})
                .value_counts()
                .reindex(order, fill_value=0)
            )
            comp = comp[comp > 0]

            fig = px.pie(
                names=comp.index,
                values=comp.values,
                color=comp.index,
                color_discrete_map=color_map,
                hole=0.4,
            )

            fig.update_traces(
                textinfo="label+percent",
                hovertemplate="%{label}: %{value} players (%{percent})",
                marker=dict(line=dict(color="white", width=1))
            )
            fig.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=180,
            )

            with cols[j]:
                st.markdown(f"""
                    <div style="
                        background: rgba(255, 255, 255, 0.7);
                        border-radius: 12px;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
                        padding: 12px 16px 16px 16px;
                        text-align: center;
                        backdrop-filter: blur(6px);
                        margin-bottom: 12px;
                    ">
                        {"<img src='" + logo + "' style='width:60px; height:auto; border-radius:8px; object-fit:cover; border:1px solid #e5e5e5; margin-bottom:6px;'/>" if isinstance(logo,str) and logo.startswith("http") else "<div style='font-size:48px; margin-bottom:6px;'>🏈</div>"}
                        <div style="font-weight:700; font-size:18px; margin-bottom:2px;">{team}</div>
                        <div style="font-size:12px; color:#555; margin-bottom:8px;">{manager_name if manager_name else ''}</div>
                    </div>
                """, unsafe_allow_html=True)

                st.plotly_chart(
                    fig,
                    width="stretch",
                    config={"displayModeBar": False, "responsive": True},
                    key=f"{team}_{idx}_chart"
                )

                display_df = g[["player_name", "position", "nfl_team"]].rename(
                    columns={
                        "player_name": "Player",
                        "position": "Position",
                        "nfl_team": "NFL Team",
                    }
                ).sort_values(by=["Position", "Player"])

                # Small transparent table styling
                st.dataframe(display_df, hide_index=True, width="stretch", height=180, column_order=None)
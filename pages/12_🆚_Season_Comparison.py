import os
import pandas as pd
import numpy as np
import streamlit as st

# Shared helpers expected to exist in your repo
from tools.data_loader import (
    load_scores_all, load_scores_year, load_player_stats,
    load_franchise_map, attach_franchise, seasons_available
)
from components.header import render_header

st.set_page_config(page_title="🆚 Season Comparison", layout="wide")
render_header("Goodell For Nothing XV")
import plotly.express as px

st.title("🆚 Season Comparison")

seasons = seasons_available("data")
if len(seasons) < 2:
    st.info("Need at least two seasons of scores to compare."); st.stop()

c1,c2 = st.columns(2)
with c1:
    a = st.selectbox("Season A", sorted(seasons), index=0)
with c2:
    b = st.selectbox("Season B", sorted(seasons), index=1)

def build(year):
    sc = load_scores_year(year)
    if sc.empty: return pd.DataFrame()
    sc["win_val"] = (sc["points_for"] > sc["points_against"]).map(lambda x: 1.0 if x else 0.0)
    winp = sc.groupby("team", as_index=False)["win_val"].mean().rename(columns={"win_val":"winp"})
    pts = sc.groupby("team", as_index=False)["points_for"].sum().rename(columns={"points_for":"total_points"})
    return winp.merge(pts, on="team", how="left")

A, B = build(a), build(b)
if A.empty or B.empty:
    st.warning("Missing data for one of the seasons."); st.stop()

c1, c2 = st.columns(2)
with c1:
    fig1 = px.scatter(A, x="winp", y=A["total_points"]/A["total_points"].max(), hover_name="team", title=f"Season {a}")
    st.plotly_chart(fig1, use_container_width=True)
with c2:
    fig2 = px.scatter(B, x="winp", y=B["total_points"]/B["total_points"].max(), hover_name="team", title=f"Season {b}")
    st.plotly_chart(fig2, use_container_width=True)

merged = A.merge(B, on="team", suffixes=(f"_{a}", f"_{b}"))
merged["Δ Win%"] = (merged[f"winp_{b}"] - merged[f"winp_{a}"]).round(3)
merged["Δ Points"] = (merged[f"total_points_{b}"] - merged[f"total_points_{a}"]).round(1)
st.subheader("Δ Metrics")
st.dataframe(merged[["team", f"winp_{a}", f"winp_{b}", "Δ Win%", f"total_points_{a}", f"total_points_{b}", "Δ Points"]],
             hide_index=True, width="stretch")

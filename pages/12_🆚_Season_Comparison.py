import os
import pandas as pd
import streamlit as st
import plotly.express as px
st.set_page_config(page_title="Season Comparison", layout="wide")
st.title("🆚 Season Comparison Dashboard")
DATA_DIR = "data"


def load_scores(y):
    p = os.path.join(DATA_DIR, f"scores_{y}.csv")
    return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()


years = sorted([int(f.split("_")[1].split(".")[0])
               for f in os.listdir(DATA_DIR) if f.startswith("scores_")])
if len(years) < 2:
    st.info("Need at least two seasons of scores_<year>.csv to compare.")
    st.stop()

c1, c2 = st.columns(2)
with c1:
    y1 = st.selectbox("Season A", years, index=0)
with c2:
    y2 = st.selectbox("Season B", years, index=min(1, len(years)-1))


def build_frame(year):
    sc = load_scores(year)
    if sc.empty:
        return pd.DataFrame()
    if {"team", "points_for", "points_against"} - set(sc.columns):
        return pd.DataFrame()
    sc["win_val"] = (sc["points_for"] > sc["points_against"]).astype(float)
    winp = sc.groupby("team", as_index=False)[
        "win_val"].mean().rename(columns={"win_val": "winp"})
    pts = sc.groupby("team", as_index=False)["points_for"].sum().rename(
        columns={"points_for": "total_points"})
    return winp.merge(pts, on="team", how="left")


a = build_frame(y1)
b = build_frame(y2)
if a.empty or b.empty:
    st.info("Missing or incompatible season files; cannot build comparison.")
    st.stop()

l1, l2 = st.columns(2)
with l1:
    a["winnings"] = a.get("winnings", 0)
    fig1 = px.scatter(a, x="winp", y=a["total_points"]/a["total_points"].max(),
                      size="winnings", hover_name="team",
                      labels={"winp": "Win %", "y": "Points (normalized)"},
                      title=f"Season {y1}")
    st.plotly_chart(fig1, use_container_width=True)
with l2:
    b["winnings"] = b.get("winnings", 0)
    fig2 = px.scatter(b, x="winp", y=b["total_points"]/b["total_points"].max(),
                      size="winnings", hover_name="team",
                      labels={"winp": "Win %", "y": "Points (normalized)"},
                      title=f"Season {y2}")
    st.plotly_chart(fig2, use_container_width=True)

merged = a.merge(b, on="team", suffixes=(f"_{y1}", f"_{y2}"))
merged["Δ Win%"] = (merged[f"winp_{y2}"] - merged[f"winp_{y1}"]).round(3)
merged["Δ Points"] = (
    merged[f"total_points_{y2}"] - merged[f"total_points_{y1}"]).round(1)
st.subheader("Δ Metrics Table")
st.dataframe(
    merged[["team", f"winp_{y1}", f"winp_{y2}", "Δ Win%",
            f"total_points_{y1}", f"total_points_{y2}", "Δ Points"]],
    use_container_width=True
)

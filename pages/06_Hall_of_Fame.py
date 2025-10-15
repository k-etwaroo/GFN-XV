import os
import pandas as pd
import numpy as np
import streamlit as st
st.set_page_config(page_title="🏛️ Hall of Fame", layout="wide")
st.title("🏛️ Hall of Fame")
DATA_DIR = "data"


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
    st.info("Add multiple seasons to populate Hall of Fame.")
    st.stop()

frames = []
for y in years:
    sc = safe_read_csv(os.path.join(DATA_DIR, f"scores_{y}.csv"))
    if sc.empty:
        continue
    sc["Year"] = y
    # derive win_val without relying on a 'result' column
    sc["win_val"] = np.where(sc["points_for"] > sc["points_against"], 1.0,
                             np.where(sc["points_for"] < sc["points_against"], 0.0, 0.5))
    frames.append(sc)

if not frames:
    st.info("No data loaded.")
    st.stop()

hist = pd.concat(frames, ignore_index=True)

# Simple champion proxy: most wins in that season
season_totals = hist.groupby(["Year", "team"], as_index=False)["win_val"].sum()
champions = season_totals.sort_values(["Year", "win_val"], ascending=[
                                      True, False]).groupby("Year").head(1)

st.subheader("Season Champions (by win value proxy)")
st.dataframe(champions.rename(
    columns={"win_val": "wins"}), use_container_width=True, height=380)

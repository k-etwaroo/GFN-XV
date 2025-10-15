import os
import pandas as pd
import streamlit as st
st.set_page_config(page_title="📚 Historical Records", layout="wide")
st.title("📚 Historical Records")
DATA_DIR = "data"


def safe_read_csv(p):
    return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()


def list_years(prefix):
    years = []
    for f in os.listdir(DATA_DIR):
        if f.startswith(prefix) and f.split("_")[1].split(".")[0].isdigit():
            years.append(int(f.split("_")[1].split(".")[0]))
    return sorted(years)


years = list_years("scores_")
if not years:
    st.info("Add scores files across multiple years.")
    st.stop()

records = []
for y in years:
    sc = safe_read_csv(os.path.join(DATA_DIR, f"scores_{y}.csv"))
    if sc.empty or "points_for" not in sc.columns:
        continue
    best_week = sc.sort_values("points_for", ascending=False).head(1)
    if not best_week.empty:
        r = best_week.iloc[0].to_dict()
        r["Year"] = y
        r["Record"] = "Best Team Single Week (points_for)"
        records.append(r)

if records:
    df_rec = pd.DataFrame(records)
    cols = ["Year", "team", "week", "points_for", "Record"]
    show = [c for c in cols if c in df_rec.columns]
    st.dataframe(df_rec[show], use_container_width=True, height=360)
else:
    st.info("No records found.")

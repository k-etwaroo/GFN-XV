import os
import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from components.header import render_header
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
st.set_page_config(page_title="💸 Payout Leaderboard", layout="wide")
render_header("Goodell For Nothing XV")
st.title("💸 Payout Leaderboard")

# --- Safety checks ---
if "gcp_service_account" not in st.secrets or "money" not in st.secrets:
    st.error(
        "Missing Google credentials or money.sheet_name in `.streamlit/secrets.toml`.")
    st.stop()

SHEET_NAME = st.secrets["money"]["sheet_name"]
DATA_DIR = "data"


def _client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scopes)
    return gspread.authorize(creds)


@st.cache_data(ttl=300)
def load_money_all_worksheets(sheet_name):
    gc = _client()
    book = gc.open(sheet_name)
    frames = []
    for ws in book.worksheets():
        df = pd.DataFrame(ws.get_all_records())
        if not df.empty:
            df["Year"] = ws.title
            frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


money = load_money_all_worksheets(SHEET_NAME)
if money.empty:
    st.warning("No Money data found in Google Sheets.")
    st.stop()

for col in ["Year", "Week", "Category", "Winner", "Amount", "Entry Fee", "Paid"]:
    if col not in money.columns:
        money[col] = None

money["Amount"] = pd.to_numeric(money["Amount"], errors="coerce").fillna(0.0)
money["Entry Fee"] = pd.to_numeric(
    money["Entry Fee"], errors="coerce").fillna(0.0)

years = sorted(money["Year"].dropna().unique())
current_year = datetime.now().year
default_year = str(current_year) if str(
    current_year) in years else (years[-1] if years else None)

view = st.radio("View Scope", ["Season", "All-Time"], horizontal=True)
df_view = money[money["Year"] == default_year] if view == "Season" else money


def compute_overview(dfm):
    pot = dfm["Entry Fee"].sum()
    payouts = dfm["Amount"].sum()
    balance = pot - payouts
    per_owner = (
        dfm.groupby("Winner", as_index=False)
           .agg(winnings=("Amount", "sum"), fees=("Entry Fee", "sum"))
    )
    per_owner["net"] = per_owner["winnings"] - per_owner["fees"]
    per_owner["roi_pct"] = per_owner.apply(lambda r: (
        r["net"]/r["fees"]*100) if r["fees"] > 0 else None, axis=1)
    pending = dfm[(dfm["Amount"] > 0) & (dfm["Paid"].astype(
        str).str.lower().isin(["no", "pending", "false", "0", ""]))].shape[0]
    return pot, payouts, balance, per_owner, pending


pot, payouts, balance, per_owner, pending = compute_overview(df_view)

c1, c2, c3, c4 = st.columns(4)
c1.metric("💰 League Pot", f"${pot:,.0f}")
c2.metric("💵 Payouts Issued", f"${payouts:,.0f}")
c3.metric("🏦 Balance Remaining", f"${balance:,.0f}")
top_roi = per_owner.dropna(subset=["roi_pct"]).sort_values(
    "roi_pct", ascending=False).head(1)
if not top_roi.empty:
    c4.metric("🥇 ROI Leader",
              top_roi.iloc[0]["Winner"], f"{top_roi.iloc[0]['roi_pct']:.0f}% ROI")

st.subheader("ROI Standings")
display = per_owner.sort_values("net", ascending=False).copy()
display["ROI %"] = display["roi_pct"].map(
    lambda x: f"{x:.1f}%" if pd.notna(x) else "—")
display["Net"] = display["net"].map("${:,.0f}".format)
display["Winnings"] = display["winnings"].map("${:,.0f}".format)
display["Fees"] = display["fees"].map("${:,.0f}".format)
st.dataframe(display[["Winner", "Winnings", "Fees", "Net",
             "ROI %"]], use_container_width=True, height=380)

st.subheader("Category Breakdown")
cat = df_view.groupby("Category", as_index=False).agg(
    Payouts=("Amount", "sum"), Count=("Amount", "size"))
fig = px.pie(cat, names="Category", values="Payouts",
             title="Payout Share by Category")
st.plotly_chart(fig, use_container_width=True)

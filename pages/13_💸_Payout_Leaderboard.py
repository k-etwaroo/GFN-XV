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

st.set_page_config(page_title="💸 Payout Leaderboard", layout="wide")
render_header("Goodell For Nothing XV")
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px

st.title("💸 Payout Leaderboard")

if "gcp_service_account" not in st.secrets or "money" not in st.secrets:
    st.info("Google Sheets not configured. Add credentials in .streamlit/secrets.toml.")
    st.stop()

SHEET_NAME = st.secrets["money"]["sheet_name"]

def _client():
    scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    creds = Credentials.from_service_account_info(st.secrets['gcp_service_account'], scopes=scopes)
    return gspread.authorize(creds)

@st.cache_data(ttl=300)
def load_money_all_worksheets(sheet_name: str):
    gc = _client()
    book = gc.open(sheet_name)
    frames = []
    for ws in book.worksheets():
        df = pd.DataFrame(ws.get_all_records())
        if df.empty: continue
        df["Year"] = ws.title
        frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

money = load_money_all_worksheets(SHEET_NAME)
if money.empty:
    st.warning("No payout rows found."); st.stop()

for col in ['Year','Week','Category','Winner','Amount','Entry Fee','Paid']:
    if col not in money.columns: money[col]=None
money['Amount'] = pd.to_numeric(money['Amount'], errors='coerce').fillna(0.0)
money['Entry Fee'] = pd.to_numeric(money['Entry Fee'], errors='coerce').fillna(0.0)

view = st.radio("Scope", ["Season","All-Time"], horizontal=True)
if view=="Season":
    years = sorted(money['Year'].dropna().unique().tolist())
    season = st.selectbox("Season", years, index=len(years)-1)
    dfv = money[money['Year']==season].copy()
else:
    dfv = money.copy()

pot = dfv['Entry Fee'].sum(); payouts = dfv['Amount'].sum(); balance = pot - payouts
c1,c2,c3 = st.columns(3)
c1.metric("💰 Pot", f"${pot:,.0f}")
c2.metric("💵 Payouts", f"${payouts:,.0f}")
c3.metric("🏦 Balance", f"${balance:,.0f}")

per_owner = dfv.groupby('Winner', as_index=False).agg(winnings=('Amount','sum'), fees=('Entry Fee','sum'))
per_owner['net'] = per_owner['winnings'] - per_owner['fees']
st.subheader("ROI Standings")
st.dataframe(per_owner.sort_values('net', ascending=False), hide_index=True, width="stretch")

cat = dfv.groupby('Category', as_index=False)['Amount'].sum().rename(columns={'Amount':'Payouts'})
st.subheader("Category Breakdown")
fig = px.pie(cat, names='Category', values='Payouts')
st.plotly_chart(fig, use_container_width=True)

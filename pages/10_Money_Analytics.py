import os
import streamlit as st
import pandas as pd

st.set_page_config(page_title="🧾 Money Analytics", layout="wide")
st.title("🧾 Money Analytics — Goodell For Nothing XV")

st.caption("Uses Google Sheet: 'GFN Money'.")
st.write("See the 💸 *Payout Leaderboard* tab for full ROI & category breakdowns.")

if "money" not in st.secrets:
    st.error(
        "Missing Google Sheets credentials in `.streamlit/secrets.toml`.\n\nExample:\n```toml\n[money]\nsheet_name = \"GFN Money\"\n```")

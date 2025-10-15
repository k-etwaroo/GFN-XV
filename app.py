import streamlit as st
from components.splash import render_splash
from components.header import render_header
from compatibility_utils import setup_streamlit_page  # ✅ NEW import

# --- Set up page layout ---
# ✅ replaces manual set_page_config
setup_streamlit_page("GFN XV", "Fantasy Analytics Dashboard")

# --- Keep your intro visuals ---
render_splash(5)
render_header("GFN XV")

# --- Welcome section ---
st.title("Welcome to GFN XV — Fantasy Analytics")
st.markdown("""
Use the sidebar to navigate between pages. Drop your Yahoo exports in the `/data` folder:

- `scores_<YEAR>.csv`
- `player_stats_<YEAR>.csv`
- optional: `owner_map.json`

If using **GFN Money**, connect your Google Sheet via `.streamlit/secrets.toml`.

---

💡 **Tip:** All pages automatically normalize your data (points, projected points, etc.)  
so you can mix historical and current seasons with no setup needed.
""")

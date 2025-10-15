
import streamlit as st

def render_header(title: str = "Goodell For Nothing XV"):
    st.markdown(f"""
        <div style="position:sticky; top:0; z-index:9999; background:#0D0D0D;
                    padding:12px 16px; border-bottom:1px solid #2a2a2a;">
            <h1 style="margin:0; text-align:center; color:#C5A300; font-family:Poppins, sans-serif;
                       font-weight:700; letter-spacing:0.5px;">
                {title}
            </h1>
        </div>
    """, unsafe_allow_html=True)
import os
import streamlit as st

def render_footer():
    """Display last updated timestamp footer."""
    timestamp_path = "data/last_updated.txt"

    st.markdown("---")  # separator line

    if os.path.exists(timestamp_path):
        with open(timestamp_path, "r") as f:
            last_updated = f.read().strip()
        st.markdown(
            f"<p style='text-align:center; color:gray; font-size:0.9em;'>"
            f"🕓 Data last updated: <b>{last_updated}</b>"
            f"</p>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<p style='text-align:center; color:gray; font-size:0.9em;'>"
            "🕓 Data last updated: <b>unknown</b>"
            "</p>",
            unsafe_allow_html=True,
        )
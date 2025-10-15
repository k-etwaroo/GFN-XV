
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

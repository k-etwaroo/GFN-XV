
import streamlit as st

def render_header(title: str = "GFN XV"):
    st.markdown(
        f"""
        <div style='background: linear-gradient(90deg, #a83279, #d38312);
                    padding: 1rem; border-radius: 8px; margin-bottom: 1.2rem;'>
            <h1 style='color:white; text-align:center; margin:0;'>{title}</h1>
        </div>
        """, unsafe_allow_html=True
    )


import streamlit as st
HORN_URL = "https://cdn.gfnxv.com/audio/nfl_horn.mp3"
CROWD_URL = "https://cdn.gfnxv.com/audio/stadium_crowd.mp3"
def render_splash(seconds: int = 5):
    if "splash_done" not in st.session_state:
        st.session_state["splash_done"] = False
    if st.session_state["splash_done"]:
        return
    st.sidebar.checkbox("Enable intro sound", key="intro_sound", value=False)
    html = f"""
    <style>
    .splash-wrap {{
        position: fixed; inset: 0; background: #0D0D0D; display:flex; 
        align-items:center; justify-content:center; z-index: 10000;
        animation: fadeout {seconds}s forwards ease-in;
    }}
    .splash-content {{
        text-align:center; color:#C5A300; font-family:Poppins, sans-serif;
        filter: drop-shadow(0 0 6px rgba(197,163,0,0.45));
    }}
    .splash-title {{ font-size: 2rem; font-weight: 800; margin-bottom: 8px; }}
    .splash-sub {{ font-size: 0.95rem; color:#E8E2B0; }}
    @keyframes fadeout {{
        0% {{ opacity: 1; }}
        85% {{ opacity: 1; }}
        100% {{ opacity: 0; visibility: hidden; }}
    }}
    .pulse-ring {{
        width: 220px; height: 220px; border-radius: 50%;
        border: 2px solid rgba(197,163,0,0.45);
        margin: 0 auto 16px auto;
        animation: pulsegold 2.5s infinite ease-in-out;
    }}
    @keyframes pulsegold {{
        0% {{ transform: scale(0.9); opacity: .7; }}
        50% {{ transform: scale(1.05); opacity: 1; }}
        100% {{ transform: scale(0.9); opacity: .7; }}
    }}
    </style>
    <div class="splash-wrap">
      <div class="splash-content">
        <div class="pulse-ring"></div>
        <div class="splash-title">Goodell For Nothing XV Fantasy Analytics</div>
        <div class="splash-sub">Loading dashboard…</div>
        {"<audio autoplay><source src='"+HORN_URL+"' type='audio/mpeg'><source src='"+CROWD_URL+"' type='audio/mpeg'></audio>" if st.session_state.get("intro_sound") else ""}
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
    st.session_state["splash_done"] = True

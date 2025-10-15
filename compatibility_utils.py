# compatibility_utils.py
import pandas as pd
import streamlit as st


def normalize_fantasy_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize fantasy football datasets across all Streamlit pages.
    Ensures consistent column names, numeric coercion, and derived fields.
    """

    # --- Alias common variants ---
    if "points_for" in df.columns and "points" not in df.columns:
        df["points"] = df["points_for"]

    if "points_against" not in df.columns and "points_allowed" in df.columns:
        df["points_against"] = df["points_allowed"]

    # --- Compute W/L/T results if missing ---
    if "result" not in df.columns and "points_for" in df.columns and "points_against" in df.columns:
        df["result"] = df.apply(
            lambda x: "W" if x["points_for"] > x["points_against"]
            else "L" if x["points_for"] < x["points_against"]
            else "T",
            axis=1
        )

    # --- Ensure projected_points exists ---
    if "projected_points" not in df.columns:
        df["projected_points"] = 0.0

    # --- Coerce numeric columns safely ---
    numeric_cols = ["points", "points_for",
                    "points_against", "projected_points"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # --- Add missing text columns for consistency ---
    for text_col in ["team", "manager", "felo_tier", "opponent"]:
        if text_col not in df.columns:
            df[text_col] = "Unknown"

    # --- Sort chronologically if possible ---
    if "season" in df.columns and "week" in df.columns:
        df = df.sort_values(["season", "week"], ascending=[False, True])

    return df


def setup_streamlit_page(title: str, subtitle: str = None):
    """
    Applies consistent Streamlit layout, titles, captions, and styling.
    """
    st.set_page_config(page_title=title, layout="wide")

    st.title(title)
    if subtitle:
        st.caption(subtitle)
    st.caption("GFN XV League Analytics — Clean & Stable Version")


def safe_dataframe_display(df: pd.DataFrame, label: str = "📊 Data"):
    """
    Safely display a dataframe with consistent formatting and deprecation-safe width.
    """
    if df.empty:
        st.warning(f"No data available for {label}.")
    else:
        st.dataframe(df, width="stretch")

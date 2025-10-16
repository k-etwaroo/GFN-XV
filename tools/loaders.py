# tools/data_loader.py
import os
import pandas as pd

DATA_DIR = "data"

def load_scores_all():
    """Load all scores_*.csv and return one cleaned dataframe."""
    frames = []
    for fname in os.listdir(DATA_DIR):
        if fname.startswith("scores_") and fname.endswith(".csv"):
            try:
                df = pd.read_csv(os.path.join(DATA_DIR, fname))
                frames.append(df)
            except Exception:
                pass
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    # Normalize columns expected across pages
    wanted = ["season","week","team","manager","felo_tier","logo_url",
              "opponent","points_for","points_against","projected_points"]
    for c in wanted:
        if c not in out.columns:
            out[c] = None
    # Types
    out["season"] = pd.to_numeric(out["season"], errors="coerce").astype("Int64")
    out["week"] = pd.to_numeric(out["week"], errors="coerce").astype("Int64")
    out["points_for"] = pd.to_numeric(out["points_for"], errors="coerce").fillna(0.0)
    out["points_against"] = pd.to_numeric(out["points_against"], errors="coerce").fillna(0.0)
    out["projected_points"] = pd.to_numeric(out["projected_points"], errors="coerce")
    return out

def load_player_stats_all():
    """Load all player_stats_*.csv and return one cleaned dataframe."""
    frames = []
    for fname in os.listdir(DATA_DIR):
        if fname.startswith("player_stats_") and fname.endswith(".csv"):
            try:
                df = pd.read_csv(os.path.join(DATA_DIR, fname))
                frames.append(df)
            except Exception:
                pass
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    # Normalize expected columns
    wanted = ["season","week","team","manager","player_name","position","eligible_positions",
              "logo_url","manager_image","manager_felo","actual_points","projected_points"]
    for c in wanted:
        if c not in out.columns:
            out[c] = None
    out["season"] = pd.to_numeric(out["season"], errors="coerce").astype("Int64")
    out["week"] = pd.to_numeric(out["week"], errors="coerce").astype("Int64")
    out["actual_points"] = pd.to_numeric(out["actual_points"], errors="coerce").fillna(0.0)
    out["projected_points"] = pd.to_numeric(out["projected_points"], errors="coerce")
    return out

def load_franchise_map():
    """Return franchise map if present; empty df otherwise."""
    p = os.path.join(DATA_DIR, "franchise_map.csv")
    if not os.path.exists(p):
        return pd.DataFrame(columns=["franchise_id","manager_name","aliases"])
    fm = pd.read_csv(p).fillna("")
    # explode aliases to help matching later (optional)
    return fm

def attach_franchise(df_scores, franchise_map):
    """
    Attach franchise_id to scores using simple matching rules:
    - exact manager match, else
    - team name appears in any aliases (case-insensitive)
    """
    if df_scores.empty or franchise_map.empty:
        return df_scores.assign(franchise_id=None)

    # 1) exact manager match
    left = df_scores.copy()
    left["manager_l"] = left["manager"].fillna("").str.lower().str.strip()
    fm = franchise_map.copy()
    fm["manager_l"] = fm["manager_name"].fillna("").str.lower().str.strip()
    merged = left.merge(fm[["franchise_id","manager_l"]], on="manager_l", how="left")

    # 2) fill missing by alias contains team
    mask = merged["franchise_id"].isna()
    if mask.any():
        sub = merged[mask].copy()
        sub["team_l"] = sub["team"].fillna("").str.lower().str.strip()
        fm2 = franchise_map.copy()
        fm2["aliases_l"] = fm2["aliases"].fillna("").str.lower()
        # simple contains (fast); if you need fuzzy, run the suggest tool we made earlier
        def match_alias(team):
            for _, r in fm2.iterrows():
                if team and r["aliases_l"] and team in r["aliases_l"]:
                    return r["franchise_id"]
            return None
        merged.loc[mask, "franchise_id"] = sub["team_l"].map(match_alias)

    return merged.drop(columns=["manager_l"], errors="ignore")
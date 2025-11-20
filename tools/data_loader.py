import streamlit as st
import os
import pandas as pd
import yaml

# Fallback: ensure DATA_DIR is defined if not imported elsewhere
try:
    from tools.constants import DATA_DIR
except Exception:
    DATA_DIR = "data"


# --- Franchise map loader supporting YAML and CSV ---
@st.cache_data(show_spinner=False)
def load_franchise_map(data_dir: str = DATA_DIR):
    """Load team-to-franchise mappings, supporting YAML and CSV.

    Returns
    -------
    dict
        Mapping from team/manager/alias to franchise_id (or label).
    """
    # 1) Try YAML first
    yaml_candidates = [
        os.path.join(data_dir, "franchise_map.yaml"),
        os.path.join(data_dir, "franchise_map.yml"),
    ]

    for path in yaml_candidates:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                try:
                    data = yaml.safe_load(f) or {}
                    if isinstance(data, dict):
                        return data
                    if isinstance(data, list):
                        try:
                            return dict(data)
                        except Exception:
                            pass
                    print(f"⚠️ Unexpected YAML structure in {path}; expected dict or list of pairs.")
                except yaml.YAMLError as e:
                    print(f"⚠️ Error parsing YAML at {path}: {e}")

    # 2) Fallback: CSV (e.g., data/franchise_map.csv)
    csv_path = os.path.join(data_dir, "franchise_map.csv")
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            # Normalize column names for flexibility
            df.columns = [c.strip().lower() for c in df.columns]

            # Expected columns for your current CSV:
            # franchise_id, manager_name, start_year, end_year, aliases
            cols = set(df.columns)
            if {"franchise_id", "manager_name", "aliases"}.issubset(cols):
                mapping = {}
                for _, row in df.iterrows():
                    fid = str(row.get("franchise_id", "")).strip()
                    manager = str(row.get("manager_name", "")).strip()
                    aliases_val = row.get("aliases", "")

                    # Map manager name -> franchise_id
                    if manager:
                        mapping[manager] = fid

                    # Map each alias (team name variants) -> franchise_id
                    if isinstance(aliases_val, str):
                        for raw_alias in aliases_val.split(";"):
                            alias = raw_alias.strip()
                            if alias:
                                mapping[alias] = fid

                # Also map franchise_id -> itself
                for _, row in df.iterrows():
                    fid = str(row.get("franchise_id", "")).strip()
                    if fid:
                        mapping[fid] = fid

                return mapping
            else:
                print(
                    f"⚠️ franchise_map.csv at {csv_path} is missing expected columns "
                    f"(need at least franchise_id, manager_name, aliases); "
                    f"found columns: {list(df.columns)}"
                )
        except Exception as e:
            print(f"⚠️ Error reading franchise_map.csv at {csv_path}: {e}")

    # 3) Nothing found
    checked = yaml_candidates + [csv_path]
    print(f"⚠️ Missing franchise map. Checked: {checked}")
    return {}
@st.cache_data(show_spinner=False)
def load_data_universal(data_dir: str = DATA_DIR):
    """
    Backwards-compatible helper used by app.py.

    Returns
    -------
    tuple
        (scores_df, players_df)

    - scores_df: all seasons from data/scores_*.csv with a `season` column
    - players_df: all seasons from data/player_stats_*.csv with a `season` column
    """
    import glob

    # Resolve data_dir to a real folder
    if not isinstance(data_dir, str) or not data_dir:
        data_dir = DATA_DIR

    # --- Load scores_*.csv ---
    score_files = sorted(glob.glob(os.path.join(data_dir, "scores_*.csv")))
    all_scores = []
    seasons_scores = []

    if score_files:
        print(f"📆 Found {len(score_files)} available seasons for scores_*.csv:")
        for path in score_files:
            fname = os.path.basename(path)
            # Expect filenames like scores_2019.csv
            try:
                year = int(fname.split("_")[1].split(".")[0])
            except Exception:
                print(f"⚠️ Skipping unrecognized scores file name: {fname}")
                continue

            try:
                df = pd.read_csv(path)
                df["season"] = year
                all_scores.append(df)
                seasons_scores.append(year)
            except Exception as e:
                print(f"⚠️ Error reading {path}: {e}")

    scores_df = pd.concat(all_scores, ignore_index=True) if all_scores else pd.DataFrame()

    if seasons_scores:
        seasons_scores = sorted(set(seasons_scores))
        print(f"📆 Loaded score seasons: {seasons_scores}")

    # --- Load player_stats_*.csv ---
    player_files = sorted(glob.glob(os.path.join(data_dir, "player_stats_*.csv")))
    all_players = []
    seasons_players = []

    if player_files:
        print(f"📆 Found {len(player_files)} available seasons for player_stats_*.csv:")
        for path in player_files:
            fname = os.path.basename(path)
            # Expect filenames like player_stats_2019.csv
            try:
                year = int(fname.split("_")[2].split(".")[0])
            except Exception:
                print(f"⚠️ Skipping unrecognized player stats file name: {fname}")
                continue

            try:
                df = pd.read_csv(path)
                df["season"] = year
                all_players.append(df)
                seasons_players.append(year)
            except Exception as e:
                print(f"⚠️ Error reading {path}: {e}")

    players_df = pd.concat(all_players, ignore_index=True) if all_players else pd.DataFrame()

    if seasons_players:
        seasons_players = sorted(set(seasons_players))
        print(f"📆 Loaded player stats seasons: {seasons_players}")

    return scores_df, players_df
"""
Suggest likely franchise matches for unmatched team/manager names
across all scores/player_stats data.
"""

import pandas as pd
import os, glob
from difflib import SequenceMatcher

DATA_DIR = "data"
COMBINED_DIR = os.path.join(DATA_DIR, "combined")
MAP_PATH = os.path.join(DATA_DIR, "franchise_map.csv")

# -------------------------------
# Load combined data
# -------------------------------
score_files = glob.glob(os.path.join(DATA_DIR, "scores_*.csv"))
stats_files = glob.glob(os.path.join(DATA_DIR, "player_stats_*.csv"))

frames = []
for f in score_files + stats_files:
    try:
        df = pd.read_csv(f)
        frames.append(df)
    except Exception as e:
        print(f"⚠️ Could not read {f}: {e}")

if not frames:
    raise SystemExit("❌ No data found. Run fetch_all_years.py first.")

all_data = pd.concat(frames, ignore_index=True)
print(f"[Data] Loaded {len(all_data)} rows from {len(frames)} files.")

# -------------------------------
# Load known franchise map
# -------------------------------
if not os.path.exists(MAP_PATH):
    raise SystemExit("❌ franchise_map.csv not found.")
franchises = pd.read_csv(MAP_PATH)
franchises["manager_name"] = franchises["manager_name"].fillna("").str.lower()
franchises["aliases"] = franchises["aliases"].fillna("").str.lower()

# -------------------------------
# Get all unique team/manager names
# -------------------------------
teams = (
    all_data[["team", "manager"]]
    .drop_duplicates()
    .reset_index(drop=True)
)
teams["team"] = teams["team"].fillna("").str.strip()
teams["manager"] = teams["manager"].fillna("").str.strip()
teams = teams[(teams["team"] != "") | (teams["manager"] != "")]
print(f"[Scan] Found {len(teams)} unique team/manager combos to check.")

# -------------------------------
# Helper: fuzzy score
# -------------------------------
def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

# -------------------------------
# Suggest matches
# -------------------------------
suggestions = []

for _, row in teams.iterrows():
    team = row["team"]
    manager = row["manager"]
    best_score = 0
    best_franchise = None

    for _, f in franchises.iterrows():
        name_score = similar(manager, f["manager_name"])
        alias_score = max(
            [similar(team, a.strip()) for a in f["aliases"].split(";") if a.strip()],
            default=0
        )
        total_score = max(name_score, alias_score)

        if total_score > best_score:
            best_score = total_score
            best_franchise = f["franchise_id"]

    if best_score > 0.55:  # adjust threshold as needed
        suggestions.append({
            "team": team,
            "manager": manager,
            "suggested_franchise": best_franchise,
            "confidence": round(best_score, 2)
        })

# -------------------------------
# Output results
# -------------------------------
if suggestions:
    out_df = pd.DataFrame(suggestions).sort_values("confidence", ascending=False)
    out_path = os.path.join(DATA_DIR, "franchise_suggestions.csv")
    out_df.to_csv(out_path, index=False)
    print(f"\n✅ Suggestions exported to {out_path}")
    print(f"Top matches:\n{out_df.head(10)}")
else:
    print("🎉 All teams/managers matched or no close matches found.")
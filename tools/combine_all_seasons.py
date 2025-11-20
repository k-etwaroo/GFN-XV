"""
Combine all season CSVs (scores + player stats)
and attach franchise IDs from data/franchise_map.csv
"""

import pandas as pd
import os, glob

DATA_DIR = "data"
OUTPUT_DIR = "data/combined"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Load Franchise Map ---
franchise_path = os.path.join(DATA_DIR, "franchise_map.csv")
if os.path.exists(franchise_path):
    franchise_df = pd.read_csv(franchise_path)
    franchise_df["manager_name"] = franchise_df["manager_name"].str.lower().fillna("")
    franchise_df["aliases"] = franchise_df["aliases"].fillna("")
else:
    print("⚠️ No franchise_map.csv found — proceeding without ID mapping.")
    franchise_df = pd.DataFrame(columns=["franchise_id", "manager_name", "aliases"])

# --- Helper function to find franchise ID ---
def find_franchise(row):
    team = str(row.get("team", "")).lower()
    manager = str(row.get("manager", "")).lower()

    for _, f in franchise_df.iterrows():
        if f["manager_name"] and f["manager_name"] in manager:
            return f["franchise_id"]

        aliases = [a.strip().lower() for a in f["aliases"].split(";") if a.strip()]
        if any(a in team for a in aliases):
            return f["franchise_id"]
    return "UNMATCHED"

# --- Combine all scores ---
score_files = sorted(glob.glob(os.path.join(DATA_DIR, "scores_*.csv")))
all_scores = []
for f in score_files:
    df = pd.read_csv(f)
    df["source_file"] = os.path.basename(f)
    df["franchise_id"] = df.apply(find_franchise, axis=1)
    all_scores.append(df)

if all_scores:
    combined_scores = pd.concat(all_scores, ignore_index=True)
    combined_scores.to_csv(os.path.join(OUTPUT_DIR, "all_scores.csv"), index=False)
    print(f"✅ Combined scores saved: {len(combined_scores)} rows")
else:
    print("⚠️ No scores files found.")

# --- Combine all player stats ---
stat_files = sorted(glob.glob(os.path.join(DATA_DIR, "player_stats_*.csv")))
all_stats = []
for f in stat_files:
    df = pd.read_csv(f)
    df["source_file"] = os.path.basename(f)
    df["franchise_id"] = df.apply(find_franchise, axis=1)
    all_stats.append(df)

if all_stats:
    combined_stats = pd.concat(all_stats, ignore_index=True)
    combined_stats.to_csv(os.path.join(OUTPUT_DIR, "all_player_stats.csv"), index=False)
    print(f"✅ Combined player stats saved: {len(combined_stats)} rows")
else:
    print("⚠️ No player_stats files found.")

print("\n🎉 Merge complete — data/combined now contains:")
print(" - all_scores.csv")
print(" - all_player_stats.csv")
import os
import pandas as pd

DATA_DIR = "data"
OUT_PATH = os.path.join(DATA_DIR, "combined_seasons_scores.csv")

# Find all yearly score files
score_files = [
    f for f in os.listdir(DATA_DIR)
    if f.startswith("scores_") and f.endswith(".csv") and f.split("_")[1].split(".")[0].isdigit()
]

if not score_files:
    print("❌ No scores_<year>.csv files found in /data.")
    exit()

frames = []
for f in sorted(score_files):
    path = os.path.join(DATA_DIR, f)
    try:
        df = pd.read_csv(path)
        if df.empty:
            print(f"⚠️ {f} is empty, skipping.")
            continue
        # Ensure season column exists
        if "season" not in df.columns:
            year = int(f.split("_")[1].split(".")[0])
            df["season"] = year

        # Drop projected_points if not present everywhere
        cols = ["season", "week", "team", "manager", "felo_tier",
                "logo_url", "opponent", "points_for", "points_against"]
        frames.append(df[[c for c in cols if c in df.columns]])
        print(f"✅ Added {f} ({len(df)} rows)")
    except Exception as e:
        print(f"❌ Error reading {f}: {e}")

if not frames:
    print("❌ No valid score data found.")
    exit()

combined = pd.concat(frames, ignore_index=True)
combined.to_csv(OUT_PATH, index=False)
print(f"✅ Combined file saved to {OUT_PATH} ({len(combined)} total rows)")

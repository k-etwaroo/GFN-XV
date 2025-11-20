import json
import os
import pandas as pd

DATA_DIR = "data"
ROSTER_FILE = os.path.join(DATA_DIR, "player_stats_2025.csv")
LOGO_FILE = os.path.join(DATA_DIR, "team_logos.json")

def generate_team_logos():
    if not os.path.exists(ROSTER_FILE):
        print("❌ player_stats_2025.csv not found. Run fetch_yahoo_data.py first.")
        return

    df = pd.read_csv(ROSTER_FILE)
    if "team_name" not in df.columns or "team_logo" not in df.columns:
        print("❌ Missing required columns in player_stats_2025.csv.")
        print("Make sure your fetch script exports team_name and team_logo columns.")
        return

    team_logos = {}
    for team in df[["team_name", "team_logo"]].drop_duplicates().values.tolist():
        name, logo = team
        if pd.notna(name) and pd.notna(logo):
            team_logos[name] = logo

    with open(LOGO_FILE, "w") as f:
        json.dump(team_logos, f, indent=2)

    print(f"✅ Generated {len(team_logos)} team logos → {LOGO_FILE}")

if __name__ == "__main__":
    generate_team_logos()
import os
import yaml
import pandas as pd
from datetime import datetime
from yahoo_oauth import OAuth2
import yahoo_fantasy_api as yfa

DATA_DIR = "data"

def fetch_league_data(league_key, season):
    """Fetch scores and player stats for a single league/year."""
    print(f"\n[League] 🏈 Fetching {season} — {league_key}")

    sc = OAuth2(None, None, from_file="oauth2.json")
    gm = yfa.Game(sc, "nfl")
    lg = gm.to_league(league_key)

    info = lg.settings()
    num_teams = info["num_teams"]
    current_week = int(info.get("current_week", 17))
    total_weeks = int(info.get("end_week", 17))
    print(f"[Info] {num_teams} teams, {total_weeks} weeks, current week = {current_week}")

    # --- Fetch matchups ---
    all_scores = []
    for week in range(1, current_week + 1):
        try:
            data = lg.yhandler.get(f"league/{league_key}/scoreboard;week={week}")
            matchups = data["fantasy_content"]["league"][1]["scoreboard"]
            if "0" not in matchups:
                print(f"⚠️ No matchups found for week {week}")
                continue

            week_matchups = []
            for midx in range(int(matchups["count"])):
                matchup = matchups[str(midx)]["matchup"]
                teams = matchup["0"]["teams"]
                home = teams["0"]["team"][0][2]["name"]
                away = teams["1"]["team"][0][2]["name"]
                home_proj = teams["0"]["team"][1]["team_projected_points"]["total"]
                away_proj = teams["1"]["team"][1]["team_projected_points"]["total"]
                week_matchups.append({
                    "season": season,
                    "week": week,
                    "home": home,
                    "away": away,
                    "home_proj": float(home_proj),
                    "away_proj": float(away_proj)
                })
            all_scores.extend(week_matchups)
            print(f"✅ Week {week}: {len(week_matchups)} matchups processed.")

        except Exception as e:
            print(f"⚠️ Error week {week}: {e}")

    df_scores = pd.DataFrame(all_scores)
    out_file = os.path.join(DATA_DIR, f"scores_{season}.csv")
    df_scores.to_csv(out_file, index=False)
    print(f"[Export] ✅ Saved scores to {out_file}")


# --- Helper: Load leagues.yaml safely ---
def load_leagues_yaml(filepath="data/leagues.yaml"):
    with open(filepath, "r") as f:
        content = yaml.safe_load(f)

    # Detect format and clean invalid entries
    if not isinstance(content, dict):
        raise ValueError("YAML format invalid — expected {year: league_key}")

    # Handle both possible formats
    if "leagues" in content and isinstance(content["leagues"], dict):
        leagues = content["leagues"]
    else:
        leagues = content

    clean = {}
    for k, v in leagues.items():
        try:
            yr = int(str(k).strip())
            clean[yr] = str(v).strip()
        except Exception:
            print(f"⚠️ Skipping invalid entry: {k}: {v}")
    return clean


if __name__ == "__main__":
    print("[Init] 🗓️ Loading league definitions from data/leagues.yaml")
    try:
        leagues = load_leagues_yaml()
    except Exception as e:
        print(f"❌ Failed to read leagues.yaml: {e}")
        exit(1)

    print(f"[Init] ✅ Found {len(leagues)} valid seasons")

    sc = OAuth2(None, None, from_file="oauth2.json")
    print("[Auth] 🔐 Loading OAuth2 credentials...")
    if not sc.token_is_valid():
        sc.refresh_access_token()
    print("[Auth] ✅ OAuth2 ready")

    for season, league_key in leagues.items():
        fetch_league_data(str(league_key), int(season))

    print("\n🎉 Done! All seasons processed successfully.")
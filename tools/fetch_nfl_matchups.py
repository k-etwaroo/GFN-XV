import requests
import json
import os
from datetime import datetime, timedelta

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(DATA_DIR, "nfl_weekly_matchups.json")

def fetch_nfl_matchups():
    """
    Fetches current week NFL matchups from ESPN's public API and saves to JSON.
    """
    print("🏈 Fetching current NFL matchups from ESPN...")

    url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"❌ Failed to fetch data: {response.status_code}")
        return

    data = response.json()
    events = data.get("events", [])
    matchups = []

    for event in events:
        competition = event.get("competitions", [{}])[0]
        teams = competition.get("competitors", [])
        if len(teams) != 2:
            continue

        home = teams[0]
        away = teams[1]

        # Helper for record lookup
        def safe_record(team):
            recs = team.get("records", [])
            if recs and isinstance(recs, list):
                return recs[0].get("summary", "")
            return ""

        matchup = {
            "date": competition.get("date", ""),
            "venue": competition.get("venue", {}).get("fullName", ""),
            "broadcast": ", ".join([c.get("shortName", "") for c in competition.get("geoBroadcasts", []) if c.get("shortName")]),
            "home_team": home["team"]["displayName"],
            "home_abbr": home["team"].get("abbreviation", ""),
            "home_logo": home["team"].get("logo", ""),
            "home_record": safe_record(home["team"]),
            "away_team": away["team"]["displayName"],
            "away_abbr": away["team"].get("abbreviation", ""),
            "away_logo": away["team"].get("logo", ""),
            "away_record": safe_record(away["team"]),
        }

        matchups.append(matchup)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(matchups, f, indent=2)

    print(f"✅ Saved {len(matchups)} matchups → {OUTPUT_FILE}")

def should_refresh(file_path, days=3):
    """
    Check if a file is older than X days.
    """
    if not os.path.exists(file_path):
        return True
    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
    return datetime.now() - file_time > timedelta(days=days)

if __name__ == "__main__":
    if should_refresh(OUTPUT_FILE, days=3):
        fetch_nfl_matchups()
    else:
        print("🕒 NFL matchups file is recent — no update needed.")
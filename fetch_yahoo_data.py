import os
import json
import time
import argparse
import pandas as pd
import requests
from yahoo_oauth import OAuth2
from tqdm import tqdm

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

LEAGUE_KEY = "461.l.23054"
YEAR = 2025
BASE_URL = "https://fantasysports.yahooapis.com/fantasy/v2"


# ------------------------------------------------------
# Utilities
# ------------------------------------------------------
def safe_float(v):
    try:
        return float(v)
    except Exception:
        return 0.0


def save_json(obj, path):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)


def auth_headers(sc):
    return {"Authorization": f"Bearer {sc.access_token}"}


def get_json(sc, url, debug_name=None, debug=False):
    r = requests.get(url, headers=auth_headers(sc))
    if r.status_code == 401:
        raise PermissionError("Unauthorized (401)")
    r.raise_for_status()
    data = r.json()
    if debug and debug_name:
        save_json(data, os.path.join(DATA_DIR, f"{debug_name}.json"))
    return data


# ------------------------------------------------------
# Weekly scores
# ------------------------------------------------------
def parse_team_block(team_block):
    """Extract team name, total points, and projected points."""
    name, points, proj = "", 0.0, 0.0
    if not isinstance(team_block, list) or not team_block:
        return name, points, proj

    info = team_block[0]
    if isinstance(info, list):
        for d in info:
            if isinstance(d, dict) and "name" in d:
                name = d["name"]
                break

    for d in team_block[1:]:
        if isinstance(d, dict) and "team_points" in d:
            points = safe_float(d["team_points"].get("total", 0))
        if isinstance(d, dict) and "team_projected_points" in d:
            proj = safe_float(d["team_projected_points"].get("total", 0))

    return name, points, proj


def fetch_scores(sc, league_key, current_week, debug=False):
    """Fetch weekly matchups and scores."""
    all_rows = []
    print("📊 Fetching weekly matchups...")

    for week in tqdm(range(1, current_week + 1), desc="Weekly Scores"):
        url = f"{BASE_URL}/league/{league_key}/scoreboard;week={week}?format=json"
        data = get_json(sc, url, debug_name=f"debug_week{week}" if debug else None, debug=debug)

        try:
            league = data["fantasy_content"]["league"]
            scoreboard = league[1]["scoreboard"]
            sb0 = scoreboard.get("0", scoreboard)
            matchups = sb0.get("matchups", {})
            count = int(sb0.get("count", len(matchups)))
        except Exception as e:
            print(f"⚠️  Week {week} structure error: {e}")
            continue

        print(f"--- Week {week} ({count} matchups) ---")
        if not matchups:
            continue

        for i in matchups.keys():
            try:
                matchup = matchups[i]["matchup"]
                teams = matchup["0"]["teams"]
                t1 = teams["0"]["team"]
                t2 = teams["1"]["team"]

                t1_name, t1_pts, t1_proj = parse_team_block(t1)
                t2_name, t2_pts, t2_proj = parse_team_block(t2)

                print(f"🏆 {t1_name} ({t1_pts}) vs {t2_name} ({t2_pts})")

                all_rows.extend([
                    {"season": YEAR, "week": week, "team_name": t1_name, "points": t1_pts, "projected": t1_proj},
                    {"season": YEAR, "week": week, "team_name": t2_name, "points": t2_pts, "projected": t2_proj},
                ])
            except Exception as e:
                print(f"⚠️  Week {week} matchup parse error: {e}")

        time.sleep(0.2)

    return pd.DataFrame(all_rows)


# ------------------------------------------------------
# Team logos
# ------------------------------------------------------
def fetch_teams(sc, league_key, debug=False):
    """Fetch league team names and logos."""
    url = f"{BASE_URL}/league/{league_key}/teams?format=json"
    data = get_json(sc, url, debug_name="debug_teams" if debug else None, debug=debug)
    teams_data = data.get("fantasy_content", {}).get("league", [{}])[1].get("teams", {})
    team_logos = {}

    for tid, val in teams_data.items():
        if not tid.isdigit():
            continue
        team_entry = val.get("team", [])
        if not team_entry:
            continue
        info = team_entry[0]
        if isinstance(info, list):
            name, logo = "", ""
            for item in info:
                if "name" in item:
                    name = item["name"]
                if "team_logos" in item:
                    logos = item["team_logos"]
                    if logos and "team_logo" in logos[0]:
                        logo = logos[0]["team_logo"]["url"]
            if name:
                team_logos[name] = logo
    return team_logos


# ------------------------------------------------------
# Player stats (fixed roster parsing)
# ------------------------------------------------------
def fetch_player_stats(sc, league_key, current_week):
    """Fetch team rosters (player names, positions, logos)."""
    print("\n👥 Fetching rosters...")

    all_players = []
    teams_url = f"{BASE_URL}/league/{league_key}/teams?format=json"
    r = requests.get(teams_url, headers=auth_headers(sc))
    teams_data = (
        r.json()
        .get("fantasy_content", {})
        .get("league", [{}])[1]
        .get("teams", {})
    )

    for tid, t in teams_data.items():
        if not tid.isdigit():
            continue
        team_entry = t.get("team", [])
        if not team_entry:
            continue

        team_name, team_logo, team_key = "", "", ""
        manager_name, manager_img = "", ""
        for item in team_entry[0]:
            if isinstance(item, dict):
                if "team_key" in item:
                    team_key = item["team_key"]
                elif "name" in item:
                    team_name = item["name"]
                elif "team_logos" in item:
                    logos = item["team_logos"]
                    if isinstance(logos, list) and "team_logo" in logos[0]:
                        team_logo = logos[0]["team_logo"].get("url", "")
                if "managers" in item:
                    managers = item["managers"]
                    if isinstance(managers, list) and "manager" in managers[0]:
                        m = managers[0]["manager"]
                        manager_name = m.get("nickname", "")
                        manager_img = m.get("image_url", "")

        print(f"\n📦 {team_name}")

        for week in range(1, current_week + 1):
            try:
                roster_url = f"{BASE_URL}/team/{team_key}/roster;week={week}?format=json"
                rr = requests.get(roster_url, headers=auth_headers(sc))
                data = rr.json()

                team_data = data.get("fantasy_content", {}).get("team", [])
                if len(team_data) < 2:
                    print(f"⚠️  {team_name} week {week} roster missing team_data block.")
                    continue

                roster_root = team_data[1].get("roster", {})
                # Handle nested formats
                if "players" in roster_root:
                    roster = roster_root["players"]
                elif "0" in roster_root and "players" in roster_root["0"]:
                    roster = roster_root["0"]["players"]
                else:
                    roster = {}

                count = int(roster_root.get("count", len(roster)))
                print(f"  • Week {week}: found {count} players")

                for i in range(count):
                    player_entry = roster.get(str(i), {}).get("player", [])
                    if not player_entry:
                        continue

                    player_info = {}
                    # Flatten nested player info
                    for block in player_entry[0]:
                        if isinstance(block, dict):
                            player_info.update(block)

                    player_name = player_info.get("name", {}).get("full", "")
                    position = player_info.get("display_position", "")
                    nfl_team = player_info.get("editorial_team_abbr", "")
                    bye_week = player_info.get("bye_weeks", {}).get("week", "")

                    if not player_name:
                        continue

                    all_players.append({
                        "season": YEAR,
                        "week": week,
                        "team_name": team_name,
                        "team_logo": team_logo,
                        "manager_name": manager_name,
                        "manager_img": manager_img,
                        "player_name": player_name,
                        "position": position,
                        "nfl_team": nfl_team,
                        "bye_week": bye_week,
                    })

            except Exception as e:
                print(f"⚠️  {team_name} week {week} roster error: {e}")
                continue

    df_players = pd.DataFrame(all_players)
    df_players.to_csv(os.path.join(DATA_DIR, f"player_stats_{YEAR}.csv"), index=False)
    print(f"\n[Export] ✅ Saved {len(df_players)} player rows → data/player_stats_{YEAR}.csv")
    return df_players


# ------------------------------------------------------
# Main entry point
# ------------------------------------------------------
def main(debug=False):
    print(f"\n🏈 Fetching Yahoo data for {YEAR} — League {LEAGUE_KEY}")
    sc = OAuth2(None, None, from_file="oauth2.json")
    if not sc.token_is_valid():
        sc.refresh_access_token()

    meta_url = f"{BASE_URL}/league/{LEAGUE_KEY}/scoreboard?format=json"
    meta_data = get_json(sc, meta_url)
    league_info = meta_data["fantasy_content"]["league"][0]
    league_name = league_info["name"]
    current_week = int(league_info["current_week"])
    print(f"[Info] {league_name} | {current_week} active weeks\n")

    # --- Scores ---
    df_scores = fetch_scores(sc, LEAGUE_KEY, current_week, debug=debug)
    df_scores.to_csv(os.path.join(DATA_DIR, f"scores_{YEAR}.csv"), index=False)
    print(f"\n[Export] ✅ Saved {len(df_scores)} rows → data/scores_{YEAR}.csv")

    # --- Player stats ---
    df_players = fetch_player_stats(sc, LEAGUE_KEY, current_week)

    # --- Team logos ---
    team_logos = fetch_teams(sc, LEAGUE_KEY, debug=debug)
    save_json(team_logos, os.path.join(DATA_DIR, "team_logos.json"))
    print(f"[Export] ✅ Saved {len(team_logos)} team logos → data/team_logos.json")

    print("\n🎉 Done! Data ready for Streamlit.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Enable debug JSON export")
    args = parser.parse_args()
    main(debug=args.debug)
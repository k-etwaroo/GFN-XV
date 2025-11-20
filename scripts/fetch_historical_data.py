# scripts/fetch_historical_data.py

import json
import time
from pathlib import Path

from yahoo_oauth import OAuth2
import yahoo_fantasy_api as yfa

GAME_CODE = "nfl"

# 🔧 Fill this in from scripts/discover_leagues.py output
# Example:
# TARGET_LEAGUE_IDS = {
#     2011: "388.l.12345",
#     2012: "388.l.67890",
#     ...
# }
TARGET_LEAGUE_IDS = {
    2011: "257.l.114705",
    2012: "273.l.241229",
    2013: "314.l.214310",
    2014: "331.l.145833",
    2015: "348.l.225929",
    2016: "359.l.285789",
    2017: "371.l.13839",
    2018: "380.l.181541",
    2019: "390.l.650144",
    2020: "399.l.596553",
    2021: "406.l.185056",
    2022: "414.l.321722",
    2023: "423.l.132892",
    2024: "449.l.62560",
    2025: "461.l.23054",
}


def get_sc():
    # oauth2.json in repo root
    return OAuth2(None, None, from_file="oauth2.json")


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def dump_json(path: Path, data):
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def fetch_season(gm: yfa.Game, year: int, league_id: str, base_dir: Path):
    print(f"\n=== Fetching {year} (league_id={league_id}) ===")

    lg = gm.to_league(league_id)
    year_dir = base_dir / str(year)
    ensure_dir(year_dir)

    # 1️⃣ Standings
    standings = lg.standings()
    dump_json(year_dir / "standings.json", standings)

    # 2️⃣ Teams metadata
    teams = lg.teams()
    dump_json(year_dir / "teams.json", teams)

    # 3️⃣ Weekly scoreboards
    end_week = lg.end_week()
    print(f"  Season has {end_week} weeks")

    for week in range(1, end_week + 1):
        print(f"    Week {week} – scoreboard")
        try:
            scoreboard_raw = lg.matchups(week=week)
        except Exception as e:
            if "Request denied" in str(e):
                print("      Hit Yahoo rate limit while fetching scoreboards; stopping scoreboards for this season.")
                break
            else:
                print(f"      Week {week}: unexpected error getting scoreboard -> {e}")
                break
        else:
            dump_json(year_dir / f"scoreboard_week_{week}.json", scoreboard_raw)
            # Small delay to be gentle with the API
            time.sleep(0.2)

    # 4️⃣ Weekly rosters per team
    rosters_dir = year_dir / "rosters"
    ensure_dir(rosters_dir)

    team_keys = list(teams.keys())
    for team_key in team_keys:
        print(f"    Pulling rosters for {team_key}")
        tm = lg.to_team(team_key)
        team_dir = rosters_dir / team_key.replace(".", "_")
        ensure_dir(team_dir)

        for week in range(1, end_week + 1):
            try:
                roster = tm.roster(week)
            except Exception as e:
                if "Request denied" in str(e):
                    print(f"      Week {week}: Request denied (likely rate limit) – stopping roster fetch for this team.")
                    break
                else:
                    print(f"      Week {week}: error getting roster -> {e}")
                    continue

            dump_json(team_dir / f"week_{week}.json", roster)
            # Small delay to avoid hammering the API
            time.sleep(0.2)


def main():
    if not TARGET_LEAGUE_IDS:
        raise RuntimeError(
            "Fill in TARGET_LEAGUE_IDS in fetch_historical_data.py using scripts/discover_leagues.py"
        )

    sc = get_sc()
    gm = yfa.Game(sc, GAME_CODE)

    base_dir = Path("data/raw/api")
    ensure_dir(base_dir)

    for year, league_id in sorted(TARGET_LEAGUE_IDS.items()):
        try:
            fetch_season(gm, year, league_id, base_dir)
        except RuntimeError as e:
            if "Request denied" in str(e):
                print(f"\nSkipping {year} due to Yahoo 'Request denied' (likely rate limiting or access restriction). You can rerun later with just this year in TARGET_LEAGUE_IDS if needed.")
                continue
            else:
                raise


if __name__ == "__main__":
    main()
# scripts/discover_leagues.py

from yahoo_oauth import OAuth2
import yahoo_fantasy_api as yfa

GAME_CODE = "nfl"  # Yahoo game code for fantasy football


def main():
    # Uses oauth2.json in the repo root
    sc = OAuth2(None, None, from_file="oauth2.json")
    gm = yfa.Game(sc, GAME_CODE)

    # Adjust end year as needed
    for year in range(2011, 2026):  # 2011 through 2025
        try:
            league_ids = gm.league_ids(year=year)
        except Exception as e:
            print(f"{year}: error fetching leagues -> {e}")
            continue

        if not league_ids:
            continue

        print(f"\n=== {year} ===")
        for league_id in league_ids:
            lg = gm.to_league(league_id)
            settings = lg.settings()
            name = settings.get("name", "UNKNOWN_NAME")
            print(f"{league_id}  |  {name}")


if __name__ == "__main__":
    main()
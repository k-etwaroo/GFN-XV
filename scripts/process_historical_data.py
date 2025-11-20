# scripts/process_historical_data.py

import json
from pathlib import Path
import pandas as pd


RAW_BASE = Path("data/raw/api")
COMBINED_DIR = Path("data/combined")
COMBINED_DIR.mkdir(parents=True, exist_ok=True)


def iter_roster_rows():
    """
    Walks data/raw/api/<year>/rosters/*/week_*.json and yields flat rows.

    Output columns:
      - year
      - week
      - team_key
      - player_id
      - player_name
      - team_name (NFL team, if available)
      - display_position
      - selected_position (fantasy position slot)
    """
    if not RAW_BASE.exists():
        return

    for year_dir in sorted(RAW_BASE.iterdir()):
        if not year_dir.is_dir() or not year_dir.name.isdigit():
            continue
        year = int(year_dir.name)
        rosters_dir = year_dir / "rosters"
        if not rosters_dir.exists():
            continue

        for team_dir in sorted(rosters_dir.iterdir()):
            if not team_dir.is_dir():
                continue

            # team_dir name is like "390_l_650144_t_5"
            team_key = team_dir.name.replace("_", ".")  # convert back to Yahoo-style key

            for week_file in sorted(team_dir.glob("week_*.json")):
                try:
                    week_str = week_file.stem.split("_")[-1]
                    week = int(week_str)
                except Exception:
                    week = None

                with week_file.open("r", encoding="utf-8") as f:
                    players = json.load(f)

                if not isinstance(players, list):
                    continue

                for p in players:
                    # Defensive extraction of common fields from yahoo_fantasy_api roster structure
                    player_id = p.get("player_id")
                    # name might be nested as dict or plain string depending on lib version
                    name_obj = p.get("name", {})
                    if isinstance(name_obj, dict):
                        player_name = name_obj.get("full") or name_obj.get("first") or name_obj.get("last")
                    else:
                        player_name = name_obj or p.get("full_name")

                    team_name = p.get("editorial_team_full_name") or p.get("editorial_team_abbr")
                    display_pos = p.get("display_position") or p.get("position_type")
                    selected_pos = None

                    # selected_position may be a dict or list depending on structure
                    sel_pos = p.get("selected_position") or p.get("selected_position_type")
                    if isinstance(sel_pos, dict):
                        selected_pos = sel_pos.get("position")
                    elif isinstance(sel_pos, list) and sel_pos:
                        if isinstance(sel_pos[0], dict):
                            selected_pos = sel_pos[0].get("position")
                        else:
                            selected_pos = sel_pos[0]
                    else:
                        selected_pos = sel_pos

                    yield {
                        "year": year,
                        "week": week,
                        "team_key": team_key,
                        "player_id": player_id,
                        "player_name": player_name,
                        "nfl_team": team_name,
                        "display_position": display_pos,
                        "selected_position": selected_pos,
                    }


def process_rosters():
    rows = list(iter_roster_rows())
    if not rows:
        print("No roster data found under data/raw/api, nothing to process.")
        return

    df = pd.DataFrame(rows)
    out_path = COMBINED_DIR / "all_rosters.csv"
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df):,} roster rows to {out_path}")


def main():
    process_rosters()


if __name__ == "__main__":
    main()
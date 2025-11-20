import json
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd


RAW_BASE = Path("data/raw/api")
DATA_DIR = Path("data")
COMBINED_PATH = DATA_DIR / "combined" / "all_scores.csv"


def _parse_team_block(team_block: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten a single team block from the Yahoo scoreboard JSON."""
    team_arr = team_block["team"]
    # team_arr[0] is a list of small dicts, team_arr[1] has points, projections, etc.
    meta_items = team_arr[0]
    stats = team_arr[1]

    meta: Dict[str, Any] = {}
    # meta_items is a list like: [{team_key: ...}, {team_id: ...}, {name: ...}, [], {url: ...}, {...}, ...]
    for item in meta_items:
        if isinstance(item, dict):
            # This will keep later keys if duplicates appear,
            # which is usually fine for our purposes.
            meta.update(item)

    team_key = meta.get("team_key")
    team_id = meta.get("team_id")
    team_name = meta.get("name")

    # Managers is a list of {"manager": {...}}
    manager_nickname = None
    felo_tier = None
    felo_score = None
    managers = meta.get("managers")
    if isinstance(managers, list) and managers:
        mgr = managers[0].get("manager", {})
        manager_nickname = mgr.get("nickname")
        felo_tier = mgr.get("felo_tier")
        felo_score = mgr.get("felo_score")

    team_points = stats.get("team_points", {})
    total_str = team_points.get("total", "0")
    try:
        points_for = float(total_str)
    except (TypeError, ValueError):
        points_for = 0.0

    return {
        "team_key": team_key,
        "team_id": team_id,
        "team": team_name,
        "manager": manager_nickname,
        "felo_tier": felo_tier,
        "felo_score": felo_score,
        "points_for": points_for,
    }


def parse_scoreboard_file(path: Path) -> List[Dict[str, Any]]:
    """Parse a single scoreboard_week_X.json into per-team rows."""
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    fc = data.get("fantasy_content", {})
    league = fc.get("league", [])

    if not league or len(league) < 2:
        return []

    league_meta = league[0]
    scoreboard = league[1].get("scoreboard", {})

    season = int(league_meta.get("season"))
    league_id = league_meta.get("league_id")
    league_key = league_meta.get("league_key")
    league_felo_tier = league_meta.get("felo_tier")

    # week reported at scoreboard level
    scoreboard_week = int(scoreboard.get("week"))

    # In this API shape, matchups are under scoreboard["0"]["matchups"]
    # (Your sample confirms this.)
    sb0 = scoreboard.get("0", {})
    matchups = sb0.get("matchups", {})

    rows: List[Dict[str, Any]] = []

    for mk, mv in matchups.items():
        if mk == "count":
            continue

        matchup = mv.get("matchup", {})
        m_week = int(matchup.get("week", scoreboard_week))
        is_playoffs = bool(int(matchup.get("is_playoffs", "0")))
        is_consolation = bool(int(matchup.get("is_consolation", "0")))

        teams_block = matchup.get("0", {}).get("teams", {})
        team_rows = []

        for tk, tv in teams_block.items():
            if tk == "count":
                continue
            parsed = _parse_team_block(tv)
            parsed.update(
                {
                    "season": season,
                    "league_id": league_id,
                    "league_key": league_key,
                    "league_felo_tier": league_felo_tier,
                    "week": m_week,
                    "is_playoffs": is_playoffs,
                    "is_consolation": is_consolation,
                }
            )
            team_rows.append(parsed)

        # Expect 2 teams per matchup; attach opponent info.
        if len(team_rows) == 2:
            t0, t1 = team_rows[0], team_rows[1]

            t0["opponent"] = t1.get("team")
            t0["opponent_key"] = t1.get("team_key")
            t0["points_against"] = t1.get("points_for", 0.0)

            t1["opponent"] = t0.get("team")
            t1["opponent_key"] = t0.get("team_key")
            t1["points_against"] = t0.get("points_for", 0.0)

            rows.extend([t0, t1])

    return rows


def build_all_scores_from_raw() -> None:
    """Walk data/raw/api, parse all scoreboard_week_*.json, and build scores_YYYY.csv + combined/all_scores.csv."""
    all_rows: List[Dict[str, Any]] = []

    if not RAW_BASE.exists():
        raise FileNotFoundError(f"Raw API directory not found: {RAW_BASE}")

    # Each subdirectory under RAW_BASE should be a season (e.g., 2011, 2012, ...)
    for year_dir in sorted(RAW_BASE.iterdir()):
        if not year_dir.is_dir():
            continue
        try:
            season = int(year_dir.name)
        except ValueError:
            continue  # skip non-year directories

        print(f"=== Processing season {season} from {year_dir} ===")
        season_rows: List[Dict[str, Any]] = []

        # scoreboard_week_*.json
        for sb_file in sorted(year_dir.glob("scoreboard_week_*.json")):
            print(f"  - Parsing {sb_file.name}")
            rows = parse_scoreboard_file(sb_file)
            season_rows.extend(rows)

        if not season_rows:
            print(f"  ⚠️ No rows parsed for season {season} (no scoreboard files or parse failure).")
            continue

        # Create per-season DataFrame
        season_df = pd.DataFrame(season_rows)

        # Basic sanity columns to keep (plus extras if they exist)
        col_order = [
            "season",
            "league_id",
            "league_key",
            "week",
            "team_key",
            "team_id",
            "team",
            "manager",
            "opponent",
            "opponent_key",
            "points_for",
            "points_against",
            "is_playoffs",
            "is_consolation",
            "felo_tier",
            "felo_score",
            "league_felo_tier",
        ]
        # Keep only columns that are present
        cols_present = [c for c in col_order if c in season_df.columns]
        season_df = season_df[cols_present]

        # Write scores_<season>.csv
        scores_path = DATA_DIR / f"scores_{season}.csv"
        scores_path.parent.mkdir(parents=True, exist_ok=True)
        season_df.to_csv(scores_path, index=False)
        print(f"  ✅ Wrote {len(season_df)} rows → {scores_path}")

        all_rows.extend(season_rows)

    if not all_rows:
        print("⚠️ No rows parsed from any season; nothing to write.")
        return

    combined_df = pd.DataFrame(all_rows)
    combined_df.sort_values(["season", "week", "team"], inplace=True)

    combined_path = COMBINED_PATH
    combined_path.parent.mkdir(parents=True, exist_ok=True)
    combined_df.to_csv(combined_path, index=False)
    print(f"✅ Wrote combined scores: {len(combined_df)} rows → {combined_path}")


if __name__ == "__main__":
    build_all_scores_from_raw()
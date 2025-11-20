# scripts/validate_historical_data.py

import json
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path("data/raw/api")


def get_year_dirs():
    if not BASE_DIR.exists():
        print("No data/raw/api directory yet.")
        return []
    return sorted([p for p in BASE_DIR.iterdir() if p.is_dir() and p.name.isdigit()])


def validate_year(year_dir: Path):
    year = year_dir.name
    print(f"\n=== Validating {year} ===")

    issues = []

    standings = year_dir / "standings.json"
    teams = year_dir / "teams.json"
    rosters_dir = year_dir / "rosters"

    if not standings.exists():
        issues.append("missing standings.json")
    if not teams.exists():
        issues.append("missing teams.json")

    # Scoreboards
    scoreboard_files = sorted(year_dir.glob("scoreboard_week_*.json"))
    weeks_found = []
    for f in scoreboard_files:
        try:
            week_str = f.stem.split("_")[-1]
            weeks_found.append(int(week_str))
        except Exception:
            pass

    if scoreboard_files:
        print(f"  Scoreboards: {len(scoreboard_files)} file(s), weeks found: {sorted(weeks_found)}")
    else:
        issues.append("no scoreboard_week_*.json files found")

    # Rosters
    roster_counts_by_team = defaultdict(int)
    if rosters_dir.exists():
        for team_dir in rosters_dir.iterdir():
            if not team_dir.is_dir():
                continue
            week_files = list(team_dir.glob("week_*.json"))
            roster_counts_by_team[team_dir.name] = len(week_files)

        if roster_counts_by_team:
            print("  Rosters:")
            for team_name, count in sorted(roster_counts_by_team.items()):
                print(f"    {team_name}: {count} week file(s)")
        else:
            issues.append("rosters dir exists but no week_*.json files found")
    else:
        issues.append("missing rosters directory")

    if issues:
        print("  ⚠ Issues:")
        for msg in issues:
            print(f"    - {msg}")
    else:
        print("  ✅ Looks good.")


def main():
    year_dirs = get_year_dirs()
    if not year_dirs:
        return

    for year_dir in year_dirs:
        validate_year(year_dir)


if __name__ == "__main__":
    main()
from yahoo_oauth import OAuth2
import yahoo_fantasy_api as yfa
import pandas as pd
from datetime import datetime

# --- Authenticate ---
sc = OAuth2(None, None, from_file="oauth2.json")
print("[Auth] ✅ OAuth2 loaded")

# --- Connect to Yahoo NFL Game ---
gm = yfa.Game(sc, "nfl")
game_id = gm.game_id()
print(f"[Game] Active NFL game ID: {game_id}")

# --- Find the correct league ---
league_ids = gm.league_ids()
print(f"[Game] Leagues found: {league_ids}")

PREFERRED_LEAGUE_ID = "23054"
active_league = next(
    (lid for lid in league_ids if PREFERRED_LEAGUE_ID in lid), None)
if not active_league:
    active_league = next(
        (lid for lid in league_ids if str(game_id) in lid), league_ids[0])

print(f"[League] Using {active_league}")

# --- Connect to League ---
lg = gm.to_league(active_league)
settings = lg.settings()
num_weeks = int(settings.get("end_week", 17))
current_year = int(settings.get("season", datetime.now().year))

# --- Cache team metadata ---
team_metadata = {}
teams_data = lg.teams()
if isinstance(teams_data, dict):
    teams_data = teams_data.values()

for t in teams_data:
    team_key = t.get("team_key", "")
    manager_info = t.get("managers", [{}])[0].get("manager", {})
    team_metadata[team_key] = {
        "team_name": t.get("name", "Unknown"),
        "manager": manager_info.get("nickname", ""),
        "logo_url": (
            t.get("team_logos", [{}])[0].get("team_logo", {}).get("url", "")
        ),
        "felo_tier": manager_info.get("felo_tier", ""),
    }

# --- Fetch matchups ---
print(f"[Fetch] Pulling matchups for {num_weeks} weeks…")
matchup_rows = []
yhandler = lg.yhandler
league_id = active_league


def parse_team_block(team_data):
    """Extract team details including projected points."""
    team_key = None
    team_name = "Unknown"
    points_actual = 0.0
    points_proj = 0.0

    # Flatten inner structure
    for entry in team_data:
        if isinstance(entry, list):
            for item in entry:
                if isinstance(item, dict):
                    if "team_key" in item:
                        team_key = item["team_key"]
                    elif "team_id" in item and not team_key:
                        for meta_key in team_metadata.keys():
                            if meta_key.endswith(f".t.{item['team_id']}"):
                                team_key = meta_key
                                break
                    if "name" in item:
                        team_name = item["name"]
                    if "team_points" in item:
                        points_actual = float(
                            item["team_points"].get("total", 0))
                    if "team_projected_points" in item:
                        points_proj = float(
                            item["team_projected_points"].get("total", 0))

    # Merge metadata
    meta = team_metadata.get(team_key, {})
    manager = meta.get("manager", "")
    logo_url = meta.get("logo_url", "")
    felo_tier = meta.get("felo_tier", "")

    print(
        f"Parsed team: {team_name} | Actual: {points_actual:.2f} | Projected: {points_proj:.2f}")

    return {
        "team": team_name,
        "manager": manager,
        "logo_url": logo_url,
        "felo_tier": felo_tier,
        "points_actual": points_actual,
        "points_proj": points_proj,
    }


for week in range(1, num_weeks + 1):
    try:
        raw = yhandler.get(f"league/{league_id}/scoreboard;week={week}")
        scoreboard = raw.get("fantasy_content", {}).get(
            "league", [])[1].get("scoreboard", {})
        matchups = scoreboard.get("0", {}).get(
            "matchups", {}) or scoreboard.get("matchups", {})

        if not matchups:
            print(f"⚠️ Week {week}: no matchup data found.")
            continue

        for _, matchup_item in matchups.items():
            if not isinstance(matchup_item, dict) or "matchup" not in matchup_item:
                continue
            matchup = matchup_item["matchup"]
            teams_section = matchup.get("0", {}).get(
                "teams") or matchup.get("teams")
            if not isinstance(teams_section, dict):
                continue

            team_entries = [
                teams_section[k]["team"]
                for k in teams_section.keys()
                if isinstance(teams_section[k], dict) and "team" in teams_section[k]
            ]
            if len(team_entries) != 2:
                continue

            tA = parse_team_block(team_entries[0])
            tB = parse_team_block(team_entries[1])

            matchup_rows.extend([
                {
                    "season": current_year,
                    "week": week,
                    "team": tA["team"],
                    "manager": tA["manager"],
                    "felo_tier": tA["felo_tier"],
                    "logo_url": tA["logo_url"],
                    "opponent": tB["team"],
                    "points_for": tA["points_actual"],
                    "points_against": tB["points_actual"],
                    "projected_points": tA["points_proj"],
                },
                {
                    "season": current_year,
                    "week": week,
                    "team": tB["team"],
                    "manager": tB["manager"],
                    "felo_tier": tB["felo_tier"],
                    "logo_url": tB["logo_url"],
                    "opponent": tA["team"],
                    "points_for": tB["points_actual"],
                    "points_against": tA["points_actual"],
                    "projected_points": tB["points_proj"],
                },
            ])

        print(f"✅ Week {week}: {len(matchups)} matchups processed.")
    except Exception as e:
        print(f"⚠️ Error in week {week}: {e}")
        continue

# --- Export league matchups ---
scores_df = pd.DataFrame(matchup_rows, columns=[
    "season", "week", "team", "manager", "felo_tier", "logo_url",
    "opponent", "points_for", "points_against", "projected_points"
])

output_path = f"data/scores_{current_year}.csv"
scores_df.to_csv(output_path, index=False)
print(f"\n[Export] ✅ {len(scores_df)} rows written to {output_path}")
print(f"[Columns] {list(scores_df.columns)}")

# ===============================================================
# 🧩 NEW SECTION: Fetch Player-Level Stats (with actual + projected)
# ===============================================================
print(
    f"\n[Fetch] Pulling player-level stats for all teams (Week {num_weeks})…")

players = []
teams_data = lg.teams()
if isinstance(teams_data, dict):
    teams_data = teams_data.values()

for t in teams_data:
    try:
        team_key = t.get("team_key")
        team_name = t.get("name", "Unknown")
        manager_info = t.get("managers", [{}])[0].get("manager", {})
        manager = manager_info.get("nickname", "Unknown")
        logo_url = (
            t.get("team_logos", [{}])[0].get("team_logo", {}).get("url", "")
        )

        print(f"📊 Fetching roster for {team_name} ({manager})…")
        t_obj = lg.to_team(team_key)
        roster = t_obj.roster(week=num_weeks)

        if isinstance(roster, list):
            for p in roster:
                # Extract actual & projected fantasy points if available
                actual_points = 0.0
                projected_points = 0.0

                if "player_points" in p:
                    actual_points = float(p["player_points"].get("total", 0.0))
                elif "points" in p:
                    actual_points = float(p["points"].get("total", 0.0))

                if "player_projected_points" in p:
                    projected_points = float(
                        p["player_projected_points"].get("total", 0.0))

                players.append({
                    "season": current_year,
                    "team": team_name,
                    "manager": manager,
                    "player_name": p.get("name", "Unknown"),
                    "position": p.get("selected_position", "N/A"),
                    "eligible_positions": ", ".join(p.get("eligible_positions", [])),
                    "week": num_weeks,
                    "logo_url": logo_url,
                    "manager_image": manager_info.get("image_url", ""),
                    "manager_felo": manager_info.get("felo_tier", ""),
                    "actual_points": actual_points,
                    "projected_points": projected_points,
                })
        else:
            print(
                f"⚠️ Unexpected roster format for {team_name}: {type(roster)}")

    except Exception as e:
        print(f"⚠️ Error fetching roster for {t.get('name', 'Unknown')}: {e}")
        continue

# --- Export player stats ---
if players:
    players_df = pd.DataFrame(players)
    player_path = f"data/player_stats_{current_year}.csv"
    players_df.to_csv(player_path, index=False)
    print(f"[Export] ✅ {len(players_df)} player rows written to {player_path}")
    print(f"[Columns] {list(players_df.columns)}")
else:
    print("⚠️ No player stats found — skipping export.")

print("\n🎉 Done! Both team and player data ready for Streamlit.")

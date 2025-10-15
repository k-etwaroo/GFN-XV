from yahoo_oauth import OAuth2
import yahoo_fantasy_api as yfa
import pandas as pd
from datetime import datetime
import os

# ===============================================================
# CONFIGURATION
# ===============================================================
LEAGUE_KEY = "461.l.23054"
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

print("[Auth] 🔐 Loading OAuth2 credentials...")
sc = OAuth2(None, None, from_file="oauth2.json")
print("[Auth] ✅ OAuth2 loaded successfully")

gm = yfa.Game(sc, "nfl")
game_id = gm.game_id()
lg = gm.to_league(LEAGUE_KEY)
settings = lg.settings()
current_year = int(settings.get("season", datetime.now().year))
current_week = int(settings.get("current_week", 1))
num_weeks = int(settings.get("end_week", 17))

print(f"[League] Using league {LEAGUE_KEY}")
print(f"[League] Year: {current_year}, Current Week: {current_week}, Total Weeks: {num_weeks}")

# ===============================================================
# TEAM METADATA
# ===============================================================
teams_data = lg.teams()
if isinstance(teams_data, dict):
    teams_data = teams_data.values()

team_metadata = {}
for t in teams_data:
    manager_info = t.get("managers", [{}])[0].get("manager", {})
    team_metadata[t["team_key"]] = {
        "team_name": t.get("name", "Unknown"),
        "manager": manager_info.get("nickname", ""),
        "logo_url": t.get("team_logos", [{}])[0].get("team_logo", {}).get("url", ""),
        "felo_tier": manager_info.get("felo_tier", ""),
    }

print(f"[Teams] Loaded {len(team_metadata)} teams.")

# ===============================================================
# FETCH MATCHUPS
# ===============================================================
yhandler = lg.yhandler
matchup_rows = []

print(f"\n[Matchups] Fetching weekly scores through week {current_week}...")
for week in range(1, current_week + 1):
    try:
        raw = yhandler.get(f"league/{LEAGUE_KEY}/scoreboard;week={week}")
        league_data = raw.get("fantasy_content", {}).get("league", [])
        if len(league_data) < 2:
            print(f"⚠️ Week {week}: No league data.")
            continue

        scoreboard = league_data[1].get("scoreboard", {})
        matchups = (
            scoreboard.get("0", {}).get("matchups", {}) or  # ✅ FIXED PATH
            scoreboard.get("matchups", {})
        )

        if not matchups:
            print(f"⚠️ Week {week}: No matchups found.")
            continue

        # handle both dict-style and list-style matchups
        for mk, matchup_data in matchups.items():
            if not isinstance(matchup_data, dict) or "matchup" not in matchup_data:
                continue

            matchup = matchup_data["matchup"]
            teams_section = matchup.get("0", {}).get("teams") or matchup.get("teams", {})
            if not isinstance(teams_section, dict):
                continue

            team_entries = [
                v["team"]
                for v in teams_section.values()
                if isinstance(v, dict) and "team" in v
            ]
            if len(team_entries) != 2:
                continue

            def parse_team_block(block):
                team_key = None
                team_name = "Unknown"
                points_actual = 0.0
                points_proj = 0.0

                def deep_iter(d):
                    """Recursively yield all nested dicts from lists or dicts."""
                    if isinstance(d, dict):
                        yield d
                        for v in d.values():
                            yield from deep_iter(v)
                    elif isinstance(d, list):
                        for i in d:
                            yield from deep_iter(i)

                for item in deep_iter(block):
                    if "team_key" in item:
                        team_key = item["team_key"]
                    if "name" in item:
                        team_name = item["name"]
                    if "team_points" in item:
                        points_actual = float(item["team_points"].get("total", 0))
                    if "team_projected_points" in item:
                        points_proj = float(item["team_projected_points"].get("total", 0))

                meta = team_metadata.get(team_key, {})
                return {
                    "team": team_name or meta.get("team_name", "Unknown"),
                    "manager": meta.get("manager", ""),
                    "felo_tier": meta.get("felo_tier", ""),
                    "logo_url": meta.get("logo_url", ""),
                    "points_actual": points_actual,
                    "points_proj": points_proj,
                }
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
        print(f"⚠️ Error week {week}: {e}")

# Export team scores
scores_df = pd.DataFrame(matchup_rows)
scores_out = os.path.join(DATA_DIR, f"scores_{current_year}.csv")
scores_df.to_csv(scores_out, index=False)
print(f"\n[Export] ✅ Team scores written to {scores_out}")

# ===============================================================
# PLAYER STATS (limited for private leagues)
# ===============================================================
print(f"\n[Players] Fetching player rosters through week {current_week}...")
players = []

for t in teams_data:
    team_key = t.get("team_key")
    team_name = t.get("name", "Unknown")
    manager_info = t.get("managers", [{}])[0].get("manager", {})
    manager = manager_info.get("nickname", "")
    logo_url = t.get("team_logos", [{}])[0].get("team_logo", {}).get("url", "")

    try:
        t_obj = lg.to_team(team_key)
        roster = t_obj.roster(week=current_week)
        for p in roster:
            players.append({
                "season": current_year,
                "team": team_name,
                "manager": manager,
                "player_name": p.get("name", ""),
                "position": p.get("selected_position", ""),
                "eligible_positions": ", ".join(p.get("eligible_positions", [])),
                "week": current_week,
                "logo_url": logo_url,
                "manager_image": manager_info.get("image_url", ""),
                "manager_felo": manager_info.get("felo_tier", ""),
            })
    except Exception as e:
        if "denied" in str(e):
            print(f"🚫 Skipping private team: {team_name}")
        else:
            print(f"⚠️ Error fetching {team_name}: {e}")

if players:
    players_df = pd.DataFrame(players)
    players_out = os.path.join(DATA_DIR, f"player_stats_{current_year}.csv")
    players_df.to_csv(players_out, index=False)
    print(f"[Export] ✅ Player stats written to {players_out}")
else:
    print("⚠️ No player stats exported (private league)")

# ===============================================================
# 🏈 SCOREBOARD PREVIEW (colorized with actual + projected)
# ===============================================================
print("\n🏈 [Preview] Latest Matchups Summary:")

def color_text(text, color):
    """Return colored terminal text using ANSI escape codes."""
    colors = {
        "green": "\033[92m",  # bright green
        "red": "\033[91m",    # bright red
        "white": "\033[97m",  # white / neutral
        "reset": "\033[0m",
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"

if not matchup_rows:
    print("⚠️ No matchups parsed. Try again during an active week.")
else:
    df = pd.DataFrame(matchup_rows)
    df = df.groupby(
        ["week", "team", "opponent", "manager", "points_for", "points_against", "projected_points"],
        as_index=False
    ).first()

    summary_rows = []  # for CSV export
    for week in sorted(df["week"].unique()):
        print(f"\n--- Week {week} ---")
        week_df = df[df["week"] == week]
        seen = set()

        for _, row in week_df.iterrows():
            matchup_key = tuple(sorted([row["team"], row["opponent"]]))
            if matchup_key in seen:
                continue
            seen.add(matchup_key)

            opp_row = week_df[
                (week_df["team"] == row["opponent"]) & (week_df["opponent"] == row["team"])
            ]
            if not opp_row.empty:
                opp_points = opp_row.iloc[0]["points_for"]
                opp_proj = opp_row.iloc[0]["projected_points"]
            else:
                opp_points, opp_proj = 0.0, 0.0

            # Determine colors (based on actual > 0 or projected)
            if row["points_for"] > 0 or opp_points > 0:
                if abs(row["points_for"] - opp_points) < 0.5:
                    color_team = color_opp = "white"
                elif row["points_for"] > opp_points:
                    color_team, color_opp = "green", "red"
                else:
                    color_team, color_opp = "red", "green"
            else:
                if abs(row["projected_points"] - opp_proj) < 0.5:
                    color_team = color_opp = "white"
                elif row["projected_points"] > opp_proj:
                    color_team, color_opp = "green", "red"
                else:
                    color_team, color_opp = "red", "green"

            team_str = color_text(f"{row['team']} ({row['manager']})", color_team)
            opp_str = color_text(f"{row['opponent']}", color_opp)

            # Terminal display
            print(
                f"{team_str} vs {opp_str} → "
                f"Actual: {row['points_for']:.1f} / {opp_points:.1f} | "
                f"Proj: {row['projected_points']:.1f} / {opp_proj:.1f}"
            )

            # CSV-friendly row (no color codes)
            summary_rows.append({
                "season": current_year,
                "week": week,
                "team": row["team"],
                "manager": row["manager"],
                "opponent": row["opponent"],
                "points_for": round(row["points_for"], 2),
                "points_against": round(opp_points, 2),
                "projected_for": round(row["projected_points"], 2),
                "projected_against": round(opp_proj, 2),
            })

    # --- Export CSV Summary ---
    summary_df = pd.DataFrame(summary_rows)
    summary_path = f"data/matchup_summary_{current_year}.csv"
    summary_df.to_csv(summary_path, index=False)
    print(f"\n[Export] 🗂️ Matchup summary written to {summary_path}")

print("\n🎉 Done! Data ready for Streamlit.")
# --- Record last updated time ---
from datetime import datetime
with open("data/last_updated.txt", "w") as f:
    f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print("\n🕓 Timestamp written to data/last_updated.txt")
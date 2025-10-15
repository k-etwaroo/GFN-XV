import os
import pandas as pd

DATA_DIR = "data"
checks = {
    "scores_2025.csv": {"season", "week", "team", "manager", "felo_tier", "logo_url", "opponent", "points_for", "points_against", "projected_points"},
    "combined_seasons_scores.csv": {"season", "week", "team", "manager", "felo_tier", "logo_url", "opponent", "points_for", "points_against"},
    "player_stats_2025.csv": {"season", "team", "manager", "player_name", "position", "eligible_positions", "week", "logo_url", "manager_image", "manager_felo"},
}


def check_file(name, req):
    p = os.path.join(DATA_DIR, name)
    if not os.path.exists(p):
        print(f"❌ {name} missing")
        return
    try:
        df = pd.read_csv(p)
    except Exception as e:
        print(f"❌ {name} unreadable: {e}")
        return
    have = set(df.columns)
    missing = req - have
    extras = have - req
    print(f"\n📄 {name}: {len(df)} rows")
    if missing:
        print(f"   ➤ Missing columns: {missing}")
    else:
        print("   ✅ Required columns present")
    if extras:
        print(f"   ℹ️ Extra columns (ok): {extras}")
    print(df.head(3).to_string(index=False))


for fname, req in checks.items():
    check_file(fname, req)

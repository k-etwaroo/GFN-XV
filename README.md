
# Goodell For Nothing XV — Complete Fantasy Dashboard

Gridiron Gold themed Streamlit app for Yahoo Fantasy Football analytics.

## 1) Prereqs (Mac/Linux)
```bash
# Python 3.10+ recommended
xcode-select --install  # mac only, if needed
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## 2) Project Structure
```
app.py
components/
  header.py          # sticky gold header
  splash.py          # cinematic splash (5s, optional audio)
pages/
  01_League_Overview.py
  02_Team_Stats.py
  03_Player_Leaders.py
  04_Power_Rankings.py
  05_💸_Payout_Leaderboard.py
  06_Hall_of_Fame.py
  07_Luck_Index.py
  08_Historical_Records.py
  09_Top_Performers.py
  10_Money_Analytics.py
  11_📊_Advanced_Analytics.py
  12_🆚_Season_Comparison.py
data/                # empty (put your CSVs here)
  templates/GFN_Money_Template.csv
.streamlit/config.toml  # Gridiron Gold theme
```

## 3) Yahoo Fantasy: Export Local CSVs
1. Create a Yahoo Developer App (get Consumer Key/Secret).  
2. Use the `yahoo_oauth` flow or your own script to export:
   - `data/scores_<YEAR>.csv` (columns suggested: week, team, opponent, result, points, opp_points)
   - `data/player_stats_<YEAR>.csv` (player_name, position, team_abbr, week, actual_points)
   - optional `data/owner_map.json`
3. Add multiple seasons for historical views.

> Tip: Re-run your exporter weekly to keep charts current.

## 4) Google Sheets: Money Tracker
- Create a Google Cloud project + Service Account.
- Download the service account JSON.
- Share your **GFN Money** Google Sheet with the service account email.
- Add `.streamlit/secrets.toml`:
```toml
[gcp_service_account]
# Paste full JSON (as TOML): "type", "project_id", "private_key_id", "private_key", "client_email", ...

[money]
sheet_name = "GFN Money"
```
- Use the provided CSV template in `data/templates/GFN_Money_Template.csv` to build your sheet tabs per season (worksheet title = year).

## 5) Run Locally
```bash
streamlit run app.py
```
- Toggle the intro sound in the sidebar if you want the cinematic audio on load.
- Use the sidebar to navigate all pages.

## 6) Deploy to Streamlit Cloud
1. Push this folder to GitHub.
2. In Streamlit Cloud, create an app → point to your repo `app.py`.
3. Set Secrets in the web UI (same as `.streamlit/secrets.toml`).
4. Deploy. The Gridiron Gold theme is picked up automatically.

## 7) Customization
- Edit `components/header.py` to change the header text.
- Tweak colors in `.streamlit/config.toml`.
- Replace hosted audio URLs in `components/splash.py` anytime.
- Add pages by creating new files in `pages/` (they auto-appear).

## 8) Data Expectations
- Missing files are handled gracefully with friendly messages.
- To unlock full analytics:
  - At least one `scores_<YEAR>.csv` for most pages
  - `player_stats_<YEAR>.csv` for Player Leaders / Top Performers
  - Google Sheet for Money pages

Enjoy! 🏈

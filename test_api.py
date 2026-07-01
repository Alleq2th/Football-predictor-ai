# test_api.py
import requests
from datetime import datetime

FOOTBALL_DATA_TOKEN = "10c9430698288310ee1c87a5960299b7"
ODDS_API_KEY = "9e425175cd824c9d8eab7ae3a232250f"

print("=" * 50)
print("API DIAGNOSTIC TEST")
print("=" * 50)

# TEST 1: Football-Data.org - Fixtures
print("\n1️⃣ Testing Football-Data.org - Fixtures...")
url = "https://api.football-data.org/v4/matches"
headers = {"X-Auth-Token": FOOTBALL_DATA_TOKEN}
params = {"dateFrom": datetime.now().strftime("%Y-%m-%d"), "dateTo": datetime.now().strftime("%Y-%m-%d")}
try:
    resp = requests.get(url, headers=headers, params=params)
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        matches = resp.json().get("matches", [])
        print(f"   ✅ SUCCESS - {len(matches)} fixtures found today")
        if matches:
            print(f"   Sample: {matches[0]['homeTeam']['name']} vs {matches[0]['awayTeam']['name']}")
    else:
        print(f"   ❌ FAILED - Response: {resp.text[:200]}")
except Exception as e:
    print(f"   ❌ EXCEPTION: {e}")

# TEST 2: Football-Data.org - Standings (Premier League)
print("\n2️⃣ Testing Football-Data.org - Standings...")
url = "https://api.football-data.org/v4/competitions/PL/standings"
try:
    resp = requests.get(url, headers=headers)
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        table = data.get("standings", [{}])[0].get("table", [])
        print(f"   ✅ SUCCESS - {len(table)} teams in standings")
        if table:
            print(f"   Top: {table[0]['team']['name']} - {table[0]['position']}st")
    else:
        print(f"   ❌ FAILED - Response: {resp.text[:200]}")
except Exception as e:
    print(f"   ❌ EXCEPTION: {e}")

# TEST 3: Football-Data.org - Team Matches (Manchester United = ID 66)
print("\n3️⃣ Testing Football-Data.org - Team Matches...")
url = "https://api.football-data.org/v4/teams/66/matches"
try:
    resp = requests.get(url, headers=headers, params={"limit": 5, "status": "FINISHED"})
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        matches = resp.json().get("matches", [])
        print(f"   ✅ SUCCESS - {len(matches)} recent matches")
        if matches:
            print(f"   Latest: {matches[0]['homeTeam']['name']} vs {matches[0]['awayTeam']['name']}")
    else:
        print(f"   ❌ FAILED - Response: {resp.text[:200]}")
except Exception as e:
    print(f"   ❌ EXCEPTION: {e}")

# TEST 4: The Odds API
print("\n4️⃣ Testing The Odds API...")
url = "https://api.the-odds-api.com/v4/sports/soccer/odds"
params = {"apiKey": ODDS_API_KEY, "regions": "eu", "markets": "h2h", "oddsFormat": "decimal"}
try:
    resp = requests.get(url, params=params)
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"   ✅ SUCCESS - {len(data)} matches with odds")
        if data:
            print(f"   Sample: {data[0]['home_team']} vs {data[0]['away_team']}")
            # Show first bookmaker odds
            bk = data[0].get("bookmakers", [])
            if bk:
                outcomes = bk[0].get("markets", [{}])[0].get("outcomes", [])
                for o in outcomes:
                    print(f"      {o['name']}: {o['price']}")
    elif resp.status_code == 401:
        print(f"   ❌ UNAUTHORIZED - API key is invalid or expired")
    elif resp.status_code == 429:
        print(f"   ❌ RATE LIMITED - Too many requests. Wait and try again.")
    else:
        print(f"   ❌ FAILED - Response: {resp.text[:200]}")
except Exception as e:
    print(f"   ❌ EXCEPTION: {e}")

# TEST 5: The Odds API - Remaining requests
print("\n5️⃣ Checking Odds API quota...")
url = "https://api.the-odds-api.com/v4/sports/soccer/odds"
try:
    resp = requests.get(url, params=params)
    print(f"   X-Requests-Used: {resp.headers.get('X-Requests-Used', 'N/A')}")
    print(f"   X-Requests-Remaining: {resp.headers.get('X-Requests-Remaining', 'N/A')}")
except:
    print(f"   Could not get headers")

print("\n" + "=" * 50)
print("DIAGNOSTIC COMPLETE")
print("=" * 50)

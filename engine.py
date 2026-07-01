# engine.py
import requests, time, numpy as np
from datetime import datetime

FOOTBALL_DATA_TOKEN = "9e425175cd824c9d8eab7ae3a232250f"   # Football-Data.org
ODDS_API_KEY = "10c9430698288310ee1c87a5960299b7"           # The Odds API

class Predictor:
    def __init__(self):
        self.fd_headers = {"X-Auth-Token": FOOTBALL_DATA_TOKEN}
        self.last_req = 0
        self.delay = 6

    def _limit(self):
        elapsed = time.time() - self.last_req
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self.last_req = time.time()

    def get_fixtures(self, date_str):
        self._limit()
        url = "https://api.football-data.org/v4/matches"
        resp = requests.get(url, headers=self.fd_headers, params={"dateFrom": date_str, "dateTo": date_str})
        return resp.json().get("matches", []) if resp.status_code == 200 else []

    def get_standings(self, code):
        self._limit()
        url = f"https://api.football-data.org/v4/competitions/{code}/standings"
        resp = requests.get(url, headers=self.fd_headers)
        return resp.json() if resp.status_code == 200 else {}

    def get_team_matches(self, tid, limit=10):
        self._limit()
        url = f"https://api.football-data.org/v4/teams/{tid}/matches"
        resp = requests.get(url, headers=self.fd_headers, params={"limit": limit, "status": "FINISHED"})
        return resp.json().get("matches", []) if resp.status_code == 200 else []

    def get_odds(self):
        url = "https://api.the-odds-api.com/v4/sports/soccer/odds"
        resp = requests.get(url, params={"apiKey": ODDS_API_KEY, "regions": "eu", "markets": "h2h", "oddsFormat": "decimal"})
        return resp.json() if resp.status_code == 200 else []

    def calc_avg_goals(self, matches, team_id, is_home):
        scored, conceded = [], []
        for m in matches:
            if m.get("status") != "FINISHED": continue
            sg = m.get("score", {}).get("fullTime", {})
            hg, ag = sg.get("home") or 0, sg.get("away") or 0
            hid = m.get("homeTeam", {}).get("id")
            aid = m.get("awayTeam", {}).get("id")
            if is_home and hid == team_id:
                scored.append(hg); conceded.append(ag)
            elif not is_home and aid == team_id:
                scored.append(ag); conceded.append(hg)
        return {
            "scored": np.mean(scored) if scored else 1.0,
            "conceded": np.mean(conceded) if conceded else 1.0
        }

    def form_list(self, matches, team_id):
        form = []
        for m in matches[:5]:
            if m.get("status") != "FINISHED": continue
            sg = m.get("score", {}).get("fullTime", {})
            hg, ag = sg.get("home") or 0, sg.get("away") or 0
            hid = m.get("homeTeam", {}).get("id")
            if hid == team_id:
                form.append("W" if hg > ag else ("D" if hg == ag else "L"))
            else:
                form.append("W" if ag > hg else ("D" if ag == hg else "L"))
        return form

    def stakes(self, standings, hid, aid):
        if not standings: return 25
        try:
            table = standings.get("standings", [{}])[0].get("table", [])
            hp = ap = None
            size = len(table)
            for t in table:
                if t["team"]["id"] == hid: hp = t["position"]
                if t["team"]["id"] == aid: ap = t["position"]
            if not hp or not ap: return 25
            s = 25
            if hp <= 3: s += 35
            if ap <= 3: s += 30
            if 4 <= hp <= 6: s += 20
            if 4 <= ap <= 6: s += 15
            if hp >= size - 3: s += 30
            if ap >= size - 3: s += 25
            return max(25, min(100, s))
        except:
            return 25

    def lowest_odd(self, odds_data, home_name):
        best = None
        for m in odds_data:
            if home_name.lower() in m.get("home_team", "").lower():
                for bk in m.get("bookmakers", []):
                    for market in bk.get("markets", []):
                        if market.get("key") == "h2h":
                            for out in market.get("outcomes", []):
                                if out["name"] == home_name:
                                    p = out["price"]
                                    if best is None or p < best: best = p
        return best

    def predict_all(self):
        today = datetime.now().strftime("%Y-%m-%d")
        fixtures = self.get_fixtures(today)
        odds = self.get_odds()
        results = []

        for m in fixtures:
            try:
                home = m["homeTeam"]; away = m["awayTeam"]
                hid = home["id"]; aid = away["id"]
                hname = home["name"]; aname = away["name"]
                comp = m["competition"]["code"]

                st = self.stakes(self.get_standings(comp), hid, aid)
                if st < 25: continue

                odd = self.lowest_odd(odds, hname)
                if not odd or odd > 1.5: continue

                hm = self.get_team_matches(hid, 20)
                aw = self.get_team_matches(aid, 20)
                hh = self.calc_avg_goals(hm, hid, True)
                aa = self.calc_avg_goals(aw, aid, False)
                hform = self.form_list(hm, hid)
                aform = self.form_list(aw, aid)

                def form_score(lst):
                    if not lst: return 0.5
                    w = [1.0, 0.9, 0.8, 0.7, 0.6]
                    s = sum(w[i] if r=="W" else (w[i]*0.5 if r=="D" else 0) for i,r in enumerate(lst))
                    return s / sum(w[:len(lst)])

                home_form_val = form_score(hform[:5])
                away_form_val = form_score(aform[:5])

                factors = {
                    "home_scoring": min(1, hh["scored"] / 3),
                    "home_defense": min(1, (3 - hh["conceded"]) / 3),
                    "away_scoring": min(1, (3 - aa["scored"]) / 3),
                    "away_defense": min(1, aa["conceded"] / 3),
                    "form_home": home_form_val,
                    "form_away": 1 - away_form_val,
                    "stakes": st / 100,
                    "odds": 1 - (odd - 1) * 2,
                }
                weights = {
                    "home_scoring": 0.12, "home_defense": 0.10, "away_scoring": 0.10,
                    "away_defense": 0.10, "form_home": 0.14, "form_away": 0.12,
                    "stakes": 0.10, "odds": 0.22
                }
                total = sum(factors[k]*weights.get(k,0.05) for k in factors)
                total_w = sum(weights.get(k,0.05) for k in factors)
                conf = min(95, max(50, (total/total_w)*100))

                results.append({
                    "home": hname, "away": aname,
                    "league": m["competition"]["name"],
                    "kickoff": m["utcDate"],
                    "odd": round(odd, 3),
                    "confidence": round(conf, 1),
                    "prediction": "HOME WIN" if conf > 65 else "DRAW/HOME",
                    "stakes": st
                })
            except Exception as e:
                continue

        results.sort(key=lambda x: x["confidence"], reverse=True)
        return [r for r in results if r["confidence"] > 55][:5]

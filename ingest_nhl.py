"""Download point-in-time NHL completed game logs from official NHL score API.

No credentials, paid APIs or betting feeds. Fails closed if any date is unavailable.
"""
import argparse,csv,datetime as dt,json,time,urllib.request
from pathlib import Path

BASE="https://api-web.nhle.com/v1/score/"
FIELDS=["date","game_id","home","away","home_goals","away_goals","home_shots","away_shots"]
def fetch_day(day):
    req=urllib.request.Request(BASE+day,headers={"User-Agent":"SportsPicksResearch/0.1"})
    with urllib.request.urlopen(req,timeout=25) as response:
        return json.load(response)
def parse_day(day,payload):
    if not isinstance(payload.get("games"),list):raise ValueError("NHL score payload missing games")
    rows=[]
    for g in payload["games"]:
        if g.get("gameType")!=2:continue
        if g.get("gameState") not in ("OFF","FINAL"):continue
        home,away=g["homeTeam"],g["awayTeam"]
        if any(x not in home or x not in away for x in ("score","sog","abbrev")):
            raise ValueError("Completed game missing scores/shots: "+str(g.get("id")))
        rows.append(dict(date=g.get("gameDate",day),game_id=g["id"],
            home=home["abbrev"],away=away["abbrev"],
            home_goals=home["score"],away_goals=away["score"],
            home_shots=home["sog"],away_shots=away["sog"]))
    return rows
def collect(start,end):
    day=dt.date.fromisoformat(start);stop=dt.date.fromisoformat(end)
    if day>stop:raise ValueError("start after end")
    rows=[];seen=set()
    while day<=stop:
        payload=fetch_day(day.isoformat())
        for row in parse_day(day.isoformat(),payload):
            if row["game_id"] in seen:raise ValueError("Duplicate game "+str(row["game_id"]))
            seen.add(row["game_id"]);rows.append(row)
        day+=dt.timedelta(days=1)
        time.sleep(.1)
    return sorted(rows,key=lambda r:(r["date"],r["game_id"]))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--start",default="2026-10-06");p.add_argument("--end",required=True);p.add_argument("--output",default="data/nhl_games.csv");args=p.parse_args()
    rows=collect(args.start,args.end)
    if len(rows)<10:raise RuntimeError("Suspiciously small game history: "+str(len(rows)))
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
    print("Wrote",len(rows),"regular-season games to",path)

"""Bounded, unauthenticated source recovery on free standard GitHub runners."""
import concurrent.futures,csv,datetime as dt,hashlib,io,json,re,urllib.request,zipfile
from pathlib import Path
OUT=Path('recovery');OUT.mkdir(exist_ok=True)
manifest=[]
def get(url,name):
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'SportsPicksResearch/1.0 (noncommercial)'})
  with urllib.request.urlopen(req,timeout=45) as r: data=r.read()
  (OUT/name).write_bytes(data)
  result={'url':url,'file':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
 except Exception as e: result={'url':url,'file':name,'error':str(e)}
 manifest.append(result);print(json.dumps(result),flush=True)
 return result
urls=[('https://moneypuck.com/data.htm','moneypuck-data.html'),('https://www.playerwon.ca/data/nhl/games/?season=20262027','playerwon.html')]
urls += [(f'https://raw.githubusercontent.com/antonwilms/sleeper-dashboard-data/main/nflverse/teamcontext/{y}.json',f'nfl-{y}.json') for y in range(2021,2027)]
urls += [('https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv','nfl-schedule.csv')]
start=dt.date(2026,9,1)
urls += [(f'https://api-web.nhle.com/v1/score/{start+dt.timedelta(days=i)}',f'nhl-{start+dt.timedelta(days=i)}.json') for i in range(53)]
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:list(pool.map(lambda pair:get(*pair),urls))
page=OUT/'moneypuck-data.html'
if page.exists():
 links=re.findall(r'(?:href|src)=[\"\']([^\"\']+)',page.read_text())
 (OUT/'moneypuck-links.json').write_text(json.dumps(links,indent=2))
# Documented downloadable shot archive URL pattern from MoneyPuck data page.
for y in [2026]:
 result=get(f'https://peter-tanner.com/moneypuck/downloads/shots_{y}.zip',f'shots_{y}.zip')
 if 'error' not in result:
  with zipfile.ZipFile(OUT/result['file']) as z:
   with z.open(f'shots_{y}.csv') as f:
    rows=csv.DictReader(io.TextIOWrapper(f));agg={};fields=rows.fieldnames
    (OUT/'shot-fields.json').write_text(json.dumps(fields))
    for r in rows:
     if r['isPlayoffGame']!='0' or r['homeSkatersOnIce']!='5' or r['awaySkatersOnIce']!='5':continue
     key=(r['game_id'],r['isHomeTeam']);agg[key]=agg.get(key,0)+float(r['xGoal'])
    (OUT/f'xg-{y}.json').write_text(json.dumps([{'game_id':k[0],'is_home':k[1],'xg':v} for k,v in agg.items()]))
  (OUT/result['file']).unlink()
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))

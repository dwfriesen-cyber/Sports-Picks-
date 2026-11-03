"""Complete season NHL scores + original raw MoneyPuck 5-on-5 shot xG."""
import argparse,concurrent.futures,csv,datetime as dt,io,json,math,zipfile
from pathlib import Path
from sources import download,SourceError
BASE='https://api-web.nhle.com/v1/score/'
TEAM_NAMES=dict(zip('ANA BOS BUF CAR CBJ CGY CHI COL DAL DET EDM FLA LAK MIN MTL NJD NSH NYI NYR OTT PHI PIT SEA SJS STL TBL TOR UTA VAN VGK WPG WSH ARI'.split(),['Anaheim Ducks','Boston Bruins','Buffalo Sabres','Carolina Hurricanes','Columbus Blue Jackets','Calgary Flames','Chicago Blackhawks','Colorado Avalanche','Dallas Stars','Detroit Red Wings','Edmonton Oilers','Florida Panthers','Los Angeles Kings','Minnesota Wild','Montreal Canadiens','New Jersey Devils','Nashville Predators','New York Islanders','New York Rangers','Ottawa Senators','Philadelphia Flyers','Pittsburgh Penguins','Seattle Kraken','San Jose Sharks','St. Louis Blues','Tampa Bay Lightning','Toronto Maple Leafs','Utah Mammoth','Vancouver Canucks','Vegas Golden Knights','Winnipeg Jets','Washington Capitals','Arizona Coyotes']))
FIELDS=['date','game_id','home','away','home_goals','away_goals','home_shots','away_shots']

def parse_day(day,payload,include_future=False,strict=False):
    if not isinstance(payload.get('games'),list):raise ValueError('NHL score payload missing games')
    if strict and payload.get('currentDate')!=day:raise ValueError('Wrong score date')
    if strict:
        expected=[d['numberOfGames'] for d in payload.get('gameWeek',[]) if d.get('date')==day]
        if len(expected)!=1 or expected[0]!=len(payload['games']):raise ValueError('NHL daily game-count mismatch')
    rows=[]
    for g in payload['games']:
        if g.get('gameType')!=2:continue
        done=g.get('gameState') in ('OFF','FINAL')
        if not done and not include_future:continue
        home,away=g['homeTeam'],g['awayTeam']
        if done and any(x not in home or x not in away for x in ('score','sog','abbrev')):raise ValueError('Completed game missing scores/shots')
        if g.get('gameDate',day)!=day:raise ValueError('Game date mismatch')
        if home['abbrev'] not in TEAM_NAMES or away['abbrev'] not in TEAM_NAMES or home['abbrev']==away['abbrev']:raise ValueError('Unknown/identical NHL teams')
        row=dict(date=day,game_id=str(g['id']),home=home['abbrev'],away=away['abbrev'])
        if strict:
            if str(g['id'])[:6] != str(g['season'])[:4]+'02':raise ValueError('Wrong NHL ID/season/type')
            start=dt.datetime.fromisoformat(g['startTimeUTC'].replace('Z','+00:00'))
            if not start.tzinfo:raise ValueError('Naive puck-drop time')
            row.update(season=str(g['season']),start_time=g['startTimeUTC'],state=g['gameState'],schedule_state=g.get('gameScheduleState'))
        if done:
            for label,team in [('home',home),('away',away)]:
                for field,src in [('goals','score'),('shots','sog')]:
                    value=team[src]
                    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0 or int(value)!=value:raise ValueError('Invalid NHL statistic')
                    row[label+'_'+field]=int(value)
            if row['home_goals']==row['away_goals']:raise ValueError('Tied NHL final')
        if strict:row.update(home_name=TEAM_NAMES[row['home']],away_name=TEAM_NAMES[row['away']])
        rows.append(row)
    return rows

def parse_shots(data,year):
    agg={};teams={}
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        with z.open(f'shots_{year}.csv') as f:
            rows=csv.DictReader(io.TextIOWrapper(f))
            required={'game_id','isPlayoffGame','homeSkatersOnIce','awaySkatersOnIce','isHomeTeam','xGoal','homeTeamCode','awayTeamCode'}
            if not required.issubset(rows.fieldnames):raise SourceError('Shot schema drift')
            for r in rows:
                if float(r['isPlayoffGame'])!=0 or float(r['homeSkatersOnIce'])!=5 or float(r['awaySkatersOnIce'])!=5:continue
                gid=int(r['game_id'])
                if gid//10000!=2:continue
                full=str(year*1000000+gid); side=float(r['isHomeTeam'])
                if side not in (0,1):raise SourceError('Unknown shot side')
                x=float(r['xGoal'])
                if not math.isfinite(x) or not 0<=x<=1:raise SourceError('Invalid raw xGoal')
                pair=(r['homeTeamCode'],r['awayTeamCode'])
                if full in teams and teams[full]!=pair:raise SourceError('Conflicting xG team IDs')
                teams[full]=pair
                item=agg.setdefault(full,{'home_xg5v5':0.,'away_xg5v5':0.,'home':pair[0],'away':pair[1]})
                item['home_xg5v5' if side else 'away_xg5v5']+=x
    return agg

def collect_full(end,source_dir,year=None):
    end=dt.date.fromisoformat(end);year=year or (end.year if end.month>=9 else end.year-1)
    root=Path(source_dir);start=dt.date(year,9,1)
    days=[(start+dt.timedelta(days=i)).isoformat() for i in range((end-start).days+1)]
    def one(day):return parse_day(day,json.loads(download(BASE+day,root/f'nhl-{day}.json')),True,True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        rows=[r for chunk in pool.map(one,days) for r in chunk]
    ids=[r['game_id'] for r in rows]
    if len(ids)!=len(set(ids)):raise SourceError('Duplicate NHL game')
    if any(r['season']!=f'{year}{year+1}' for r in rows):raise SourceError('Wrong NHL season')
    xg=parse_shots(download(f'https://peter-tanner.com/moneypuck/downloads/shots_{year}.zip',root/f'shots_{year}.zip'),year)
    missing=[]
    for r in rows:
        if 'home_goals' not in r:continue
        x=xg.get(r['game_id'])
        if x is None:missing.append(r['game_id']);continue
        if (x['home'],x['away'])!=(r['home'],r['away']):raise SourceError('NHL/MoneyPuck team mismatch')
        r.update({k:v for k,v in x.items() if k.endswith('xg5v5')})
    return sorted(rows,key=lambda r:(r['date'],r['game_id'])),{'season':year,'completed_games':sum('home_goals' in r for r in rows),'missing_xg_games':missing}

def fetch_day(day):
    return json.loads(download(BASE+day,Path('data/sources')/f'nhl-{day}.json'))
def collect(start,end):
    rows=[];day=dt.date.fromisoformat(start);stop=dt.date.fromisoformat(end)
    if day>stop:raise ValueError('start after end')
    while day<=stop:
        rows.extend(parse_day(day.isoformat(),fetch_day(day.isoformat())));day+=dt.timedelta(days=1)
    ids=[r['game_id'] for r in rows]
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate game')
    return rows
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--start',default='2026-09-01');p.add_argument('--end',required=True);p.add_argument('--output',default='data/nhl_games.csv');a=p.parse_args()
    rows=collect(a.start,a.end);path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
    print('Wrote',len(rows),'regular-season games')

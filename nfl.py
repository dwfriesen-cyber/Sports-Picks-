"""Original NFL V1. V3 blocked until original fitted V1/V2 probabilities recover."""
import csv,datetime as dt,gzip,io,json,math
from collections import defaultdict
from zoneinfo import ZoneInfo
from pathlib import Path
from sources import download,SourceError
NFL_TEAMS=set('ARI ATL BAL BUF CAR CHI CIN CLE DAL DEN DET GB HOU IND JAX KC LA LAC LV MIA MIN NE NO NYG NYJ PHI PIT SEA SF TB TEN WAS'.split())
NFL_V3_BLOCKER='Original fitted V1/V2 probability transforms, coefficients and V3 audit were not recoverable; no replacement confidence model is used.'

def expected(team,opp,h):
    a,b=h[team],h[opp]
    if min(len(a),len(b))<3:return None
    pf=sum(x['pf'] for x in a);op=sum(x['op'] for x in a);pa=sum(x['pa'] for x in b);dp=sum(x['dp'] for x in b)
    if min(op,dp)<=0:raise SourceError('Invalid NFL play denominator')
    return .5*(pa/dp*op/len(a)+pf/op*dp/len(b))

def replay(games):
    hist=defaultdict(list);out=[]
    # Original historical evaluation updates only after the full NFL week.
    for week in sorted({g['week'] for g in games}):
        batch=[g for g in games if g['week']==week]
        for g in batch:
            home,away=g['home'],g['away'];hp,ap=expected(home,away,hist),expected(away,home,hist)
            p={k:v for k,v in g.items() if k not in ('home_stats','away_stats')}
            p.update(model_version='nfl-v1-original-20261016',v3_status='blocked',v3_reason=NFL_V3_BLOCKER)
            if hp is None or ap is None:p.update(eligible=False,reason='Insufficient prior data')
            else:
                margin=hp-ap;p.update(eligible=True,winner=home if margin>0 else away,margin=margin)
                if g.get('home_stats'):
                    hs,ass=g['home_stats']['pf'],g['away_stats']['pf']
                    p['actual_winner']=None if hs==ass else home if hs>ass else away
                    p['correct']=None if hs==ass else p['winner']==p['actual_winner']
            out.append(p)
        for g in batch:
            if g.get('home_stats'):
                hist[g['home']].append(g['home_stats']);hist[g['away']].append(g['away_stats'])
    return out

def context_games(data):
    games=defaultdict(dict)
    for team,entry in data['teams'].items():
        for g in entry['games']:
            if g['seasonType']=='REG':
                if team in games[g['gameId']]:raise SourceError('Duplicate NFL context row')
                games[g['gameId']][team]=g
    out=[]
    for gid,teams in games.items():
        season,week,away,home=gid.split('_')
        if set(teams)!={home,away}:raise SourceError('Unpaired NFL game')
        row={'game_id':gid,'week':int(week),'home':home,'away':away}
        for label,t in [('home',home),('away',away)]:
            g=teams[t];row[label+'_stats']={'pf':g['off']['pointsScored'],'pa':g['def']['pointsAllowed'],'op':g['off']['plays'],'dp':g['def']['plays']}
        validate_stats(row);out.append(row)
    return out

def validate_stats(g):
    h,a=g['home_stats'],g['away_stats']
    for t in [h,a]:
        if any(v is None or isinstance(v,bool) or not math.isfinite(v) or v<0 for v in t.values()):raise SourceError('Invalid NFL stats')
        if min(t['op'],t['dp'])<=0:raise SourceError('Missing NFL play counts')
    if (h['pf'],h['pa'],h['op'],h['dp'])!=(a['pa'],a['pf'],a['dp'],a['op']):raise SourceError('NFL opponent totals disagree')

def parse_schedule(data,year):
    rows=[];seen=set()
    for r in csv.DictReader(io.StringIO(data.decode())):
        if r['season']!=str(year) or r['game_type']!='REG':continue
        gid=r['game_id']
        if gid in seen:raise SourceError('Duplicate NFL game ID')
        seen.add(gid)
        if r['home_team'] not in NFL_TEAMS or r['away_team'] not in NFL_TEAMS:raise SourceError('Unknown NFL team')
        if not r['gametime']:raise SourceError('Unscheduled NFL kickoff')
        start=dt.datetime.fromisoformat(r['gameday']+'T'+r['gametime']).replace(tzinfo=ZoneInfo('America/New_York')).astimezone(dt.timezone.utc)
        rows.append({'game_id':gid,'season':year,'week':int(r['week']),'date':r['gameday'],'start_time':start.isoformat(),'home':r['home_team'],'away':r['away_team'],'home_score':int(r['home_score']) if r['home_score'] else None,'away_score':int(r['away_score']) if r['away_score'] else None})
    if len(rows)!=272:raise SourceError(f'Incomplete NFL season schedule: {len(rows)}')
    return rows

def parse_pbp(data,year,schedule):
    """Match original upstream countable plays: pass/rush, no no_play or 2pt."""
    counts=defaultdict(lambda:defaultdict(lambda:{'op':0,'dp':0}));scores={}
    with gzip.GzipFile(fileobj=io.BytesIO(data)) as z:
        rows=csv.DictReader(io.TextIOWrapper(z))
        required={'season','season_type','game_id','posteam','defteam','pass','rush','play_type','two_point_attempt','total_home_score','total_away_score'}
        if not required.issubset(rows.fieldnames):raise SourceError('NFL pbp schema drift')
        for r in rows:
            if r['season_type']!='REG':continue
            if int(r['season'])!=year:raise SourceError('Wrong NFL pbp season')
            gid=r['game_id']
            if r['total_home_score'] and r['total_away_score']:scores[gid]=(int(float(r['total_home_score'])),int(float(r['total_away_score'])))
            t,o=r['posteam'],r['defteam']
            if t and (float(r['pass'] or 0)==1 or float(r['rush'] or 0)==1) and r['play_type']!='no_play' and float(r['two_point_attempt'] or 0)!=1:
                if t not in NFL_TEAMS or o not in NFL_TEAMS:raise SourceError('Unknown NFL pbp team')
                counts[gid][t]['op']+=1;counts[gid][o]['dp']+=1
    out=[]
    for g in schedule:
        if g['home_score'] is None:out.append(g);continue
        gid=g['game_id']
        if scores.get(gid)!=(g['home_score'],g['away_score']):raise SourceError(f'Stale/incomplete NFL pbp scores: {gid}')
        h=counts[gid][g['home']];a=counts[gid][g['away']]
        row=dict(g,home_stats=dict(h,pf=g['home_score'],pa=g['away_score']),away_stats=dict(a,pf=g['away_score'],pa=g['home_score']))
        validate_stats(row);out.append(row)
    return out

def collect(year,root):
    root=Path(root)
    schedule=parse_schedule(download('https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv',root/'nfl-schedule.csv'),year)
    pbp=download(f'https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{year}.csv.gz',root/f'nfl-pbp-{year}.csv.gz')
    return parse_pbp(pbp,year,schedule)

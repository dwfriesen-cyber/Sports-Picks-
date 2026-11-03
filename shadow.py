"""Frozen V8-lite. Keep IceScope's last-five per-60 metric; never substitute 5v5 sums."""
import datetime as dt,json,math,re
from collections import defaultdict
from pathlib import Path
from sources import download,SourceError
from ledger import freeze,digest,append

def parse_icescope(html,day):
    # Read serialized public page data as JSON; never evaluate returned JavaScript.
    records={}
    for match in re.finditer(r'self\.__next_f\.push\((\[.*?\])\)</script>',html,re.S):
        block=json.loads(match.group(1))
        if len(block)<2 or not isinstance(block[1],str):continue
        for line in block[1].splitlines():
            ident,sep,body=line.partition(':')
            if sep and re.fullmatch(r'[0-9a-f]+',ident) and body.startswith(('[','{')):
                try:records[ident]=json.loads(body)
                except json.JSONDecodeError:continue
    def deref(value):
        for _ in range(30):
            if not isinstance(value,str) or not re.fullmatch(r'\$[0-9a-f]+(?::[^\s]+)*',value):return value
            parts=value[1:].split(':');value=records[parts[0]]
            for part in parts[1:]:
                value=deref(value)
                if isinstance(value,list):value=value[3] if part=='props' else value[int(part)]
                else:value=value[part]
        raise SourceError('Circular IceScope reference')
    matches=[]
    def walk(v):
        if isinstance(v,dict):
            if 'matchupAnalytics' in v:matches.append(deref(v['matchupAnalytics']))
            for x in v.values():walk(x)
        elif isinstance(v,list):
            for x in v:walk(x)
    for value in records.values():walk(value)
    if len(matches)!=1:raise SourceError('IceScope page schema changed')
    payload=matches[0];cutoff=dt.date.fromisoformat(payload['dataThroughGameDay']);target=dt.date.fromisoformat(day)
    if cutoff>=target or (target-cutoff).days>1:raise SourceError('Stale or future IceScope snapshot')
    teams=deref(payload['teams']);values={}
    for team,windows in teams.items():
        point=deref(deref(windows)['5']);record=deref(point.get('record'))
        value=point.get('value')
        if value is None or not record or record.get('games')!=5:continue
        if not isinstance(value,(int,float)) or not math.isfinite(value):raise SourceError('Invalid IceScope value')
        values[team]=value
    return {'source':'IceScope xgBalance60 window=5','data_through':cutoff.isoformat(),'values':values}

def strength(hist,xg60,day):
    if len(hist)<5:raise SourceError('V8 requires complete five-game history')
    n=len(hist);gd=sum(g[0]-g[1] for g in hist)/n;sd=sum(g[2]-g[3] for g in hist)/n
    b2b=(dt.date.fromisoformat(day)-dt.date.fromisoformat(hist[-1][4])).days==1
    return .5*gd+.05*sd+.25*xg60-(.15 if b2b else 0)

def predict(games,day,ice):
    hist=defaultdict(list)
    for g in sorted(games,key=lambda r:(r['date'],r['game_id'])):
        if g['date']>=day or 'home_goals' not in g:continue
        hist[g['home']].append((g['home_goals'],g['away_goals'],g['home_shots'],g['away_shots'],g['date']))
        hist[g['away']].append((g['away_goals'],g['home_goals'],g['away_shots'],g['home_shots'],g['date']))
    picks=[]
    for g in games:
        if g['date']!=day:continue
        h,a=g['home'],g['away']
        if h not in ice['values'] or a not in ice['values']:raise SourceError('V8 complete xG inputs unavailable')
        margin=strength(hist[h],ice['values'][h],day)-strength(hist[a],ice['values'][a],day)
        if margin==0:raise SourceError('V8 exact tie: historical tie-selection rule unavailable')
        picks.append({k:g[k] for k in ['date','game_id','home','away','start_time']})
        picks[-1].update(eligible=True,winner=h if margin>0 else a,margin=margin,confidence=abs(margin),model_version='v8-lite-frozen-20261018',xg_source=ice['source'],xg_data_through=ice['data_through'])
    # Exact tied scores have no recovered tie-ranking rule: fail instead of inventing one.
    if len(set(p['confidence'] for p in picks))!=len(picks):raise SourceError('V8 confidence tie rule unavailable')
    for i,p in enumerate(sorted(picks,key=lambda p:-p['confidence']),1):p.update(rank=i,top25=i<=math.ceil(len(picks)/4))
    return picks

def collect(day,source_dir):
    return parse_icescope(download('https://icescope.app/',Path(source_dir)/'icescope.html').decode(),day)

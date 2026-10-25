"""Append-only forecast and grading records; derived reports may be replaced."""
import datetime as dt,hashlib,json
from pathlib import Path

def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def digest(value):return hashlib.sha256(canonical(value)).hexdigest()
def timestamp(value):
    d=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
    if d.tzinfo is None:raise ValueError('Timezone required')
    return d

def append(path,record):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);data=canonical(record)+b'\n'
    try:
        with path.open('xb') as f:f.write(data)
    except FileExistsError:
        if path.read_bytes()!=data:raise ValueError(f'Immutable record conflict: {path}')
    return digest(record)

def freeze(path,picks,now,input_hash,code_sha,kind):
    path=Path(path)
    if path.exists():
        existing=json.loads(path.read_text())
        if existing['kind']!=kind:raise ValueError('Frozen slate kind mismatch')
        return existing
    if not picks:raise ValueError('Cannot freeze empty slate')
    if any(not p.get('eligible') for p in picks):raise ValueError('Incomplete eligible slate')
    if now>=min(timestamp(p['start_time']) for p in picks):raise ValueError('Late run: earliest game has started; slate not frozen')
    record={'schema_version':1,'kind':kind,'frozen_at':now.isoformat(),'input_sha256':input_hash,'code_sha':code_sha,'picks':json.loads(canonical(picks))}
    append(path,record);return record

def grade(root,games,now):
    root=Path(root);lookup={str(g['game_id']):g for g in games};graded=[]
    for path in sorted((root/'frozen').glob('**/*.json')):
        slate=json.loads(path.read_text());kind=slate['kind']
        for p in slate['picks']:
            g=lookup.get(str(p['game_id']))
            if not g:continue
            if kind=='nfl_v1_only':
                if g.get('home_score') is None:continue
                hs,ass=g['home_score'],g['away_score']
            else:
                if 'home_goals' not in g:continue
                hs,ass=g['home_goals'],g['away_goals']
            actual=None if hs==ass else g['home'] if hs>ass else g['away']
            record={'game_id':str(g['game_id']),'date':p.get('date',g.get('date','unknown')),'forecast_sha256':digest(slate),'model':kind,'winner':p['winner'],'actual_winner':actual,'home_score':hs,'away_score':ass,'correct':None if actual is None else p['winner']==actual,'rank':p.get('rank'),'top25':p.get('top25')}
            version=digest(record)
            sport='nfl' if kind=='nfl_v1_only' else 'nhl' if kind=='nhl_v6_v7a' else 'v8'
            target=root/'grading'/sport/str(g['game_id'])/(version+'.json')
            if target.exists():saved=json.loads(target.read_text())
            else:
                saved=dict(record,graded_at=now.isoformat());append(target,saved)
            graded.append(saved)
    return graded

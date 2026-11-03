"""Research-only weekly freezes, wholly separate from production state."""
import datetime as dt
import json
from pathlib import Path
from ledger import append,canonical,digest
from nfl import context_games
from research_v3.model import VERSION,feature_rows,attach,weekly_slate


def generate(data,schedule,week,models,now,root,pool_scale=None):
    root=Path(root)
    year=int(data['season']);target=root/'frozen'/f'{year}-W{week:02}.json'
    # An immutable existing weekly pool is always returned unchanged, including after kickoff.
    if target.exists():
        old=json.loads(target.read_text())
        if old['model_version']!=VERSION:raise ValueError('Research model version mismatch')
        return old
    fixtures=[g for g in schedule if g['week']==week and g['season']==year]
    if not fixtures:raise ValueError('No target week')
    if now>=min(dt.datetime.fromisoformat(g['start_time'].replace('Z','+00:00')) for g in fixtures):
        raise ValueError('Weekly freeze missed earliest kickoff')
    if any(g['home_score'] is not None or g['away_score'] is not None for g in fixtures):
        raise ValueError('Target week already contains results')
    previous=[g for g in schedule if g['season']==year and g['week']<week]
    if any(g['home_score'] is None or g['away_score'] is None for g in previous):
        raise ValueError('Prior week not complete')
    games=context_games(data);past={g['game_id']:g for g in games if g['week']<week}
    if set(past)!={g['game_id'] for g in previous}:raise ValueError('Incomplete prior-week team context')
    for g in previous:
        c=past[g['game_id']]
        if (c['home_stats']['pf'],c['away_stats']['pf'])!=(g['home_score'],g['away_score']):
            raise ValueError('Stale team-context scores')
    selected=[r for r in feature_rows(data,fixtures) if r['week']==week]
    scored=attach(selected,models['p1'],models['p2'])
    # Freeze clock is checked by the caller after downloads and again here.
    slate=weekly_slate(scored,fixtures,now,pool_scale)
    inputs=dict(data=data,schedule=schedule,models=models)
    slate.update(input_sha256=digest(inputs),model_coefficients_sha256=digest(models))
    append(root/'inputs'/(digest(inputs)+'.json'),inputs)
    append(target,slate)
    return slate

"""Frozen NHL V1/V6 winners and V7-A confidence. No odds or fitted replacements.

Research protocol: predict every game on a date before updating that date.
V7-A uses xG for ranking at ALL season stages; V6 always selects winners.
"""
import argparse
import csv
import json
import math
from collections import defaultdict

MODEL_VERSION = 'nhl-v6-v7a-original-20261016'

def clip(x):
    return max(-1.5, min(1.5, x))

def weight(n):
    return .8 if n <= 10 else max(0, .8 * (40 - n) / 30)

def expected(team, opp, history):
    a, b = history[team], history[opp]
    if min(len(a), len(b)) < 3:
        return None
    gf, sf = sum(x[0] for x in a), sum(x[2] for x in a)
    oga, osa = sum(x[1] for x in b), sum(x[3] for x in b)
    if sf <= 0 or osa <= 0:
        return None
    return .5 * ((oga / osa) * (sf / len(a)) + (gf / sf) * (osa / len(b)))

def predict(game, h, r, xr=None):
    home, away = game['home'], game['away']
    eh, ea = expected(home, away, h), expected(away, home, h)
    if eh is None or ea is None:
        return dict(eligible=False, reason='Insufficient prior data')
    n = min(len(h[home]), len(h[away]))
    v1 = eh - ea
    margin = (1 - weight(n)) * v1 + weight(n) * 1.5 * (r[home] - r[away])
    xweight = .4 if n >= 40 else weight(n)
    confidence_margin = None if xr is None else ((1 - xweight) * v1 + xweight * 1.5 * (xr[home] - xr[away]))
    return dict(eligible=True, winner=home if margin > 0 else away,
                margin=margin, v1_margin=v1, shot_rating_margin=1.5*(r[home]-r[away]),
                confidence=None if confidence_margin is None else abs(confidence_margin),
                confidence_margin=confidence_margin,
                confidence_status='V7-A xG ranking' if xr is not None else '5v5 xG unavailable',
                v6_confidence=abs(margin), prior_games=n, model_version=MODEL_VERSION)

def present(v):
    return v is not None and v != ''

def assign_ranks(picks):
    # Exact original V7-A tie rule: score descending, home name, away name.
    eligible = [p for p in picks if p.get('eligible')]
    for key, prefix in [('confidence', ''), ('v6_confidence', 'v6_')]:
        if not eligible or any(p.get(key) is None for p in eligible):
            continue  # No partial slate top-quarter selection.
        order = sorted(eligible, key=lambda p: (-p[key], p.get('home_name',p['home']), p.get('away_name',p['away'])))
        for i,p in enumerate(order):
            p[prefix+'rank'] = i+1
            p[prefix+'top25'] = i < math.ceil(len(order)/4)
    return picks

def replay(rows, target, through=None, xg_rating_audit=None):
    """xg_rating_audit is historical parity evidence only, NEVER live inputs."""
    hist=defaultdict(list); r=defaultdict(float); xr=defaultdict(float)
    out=[]; missing_xg=False; season=None
    groups=defaultdict(list)
    for row in rows:
        groups[row['date']].append(row)
    for day, games in sorted(groups.items()):
        current=games[0].get('season', day[:4])
        if season != current:
            hist=defaultdict(list);r=defaultdict(float);xr=defaultdict(float);missing_xg=False;season=current
        games=sorted(games,key=lambda g:str(g['game_id']))
        if day >= target and (through is None or day <= through):
            picks=[]
            for g in games:
                ratings=None if missing_xg else xr
                if xg_rating_audit is not None:
                    a=xg_rating_audit.get(str(g['game_id']))
                    ratings=None if a is None else defaultdict(float,{g['home']:float(a['xg_rating_margin'])/1.5})
                pick=dict(g, **predict(g,hist,r,ratings))
                pick['prediction_kind']='retrospective_reconstruction'
                if all(present(g.get(k)) for k in ('home_goals','away_goals')):
                    pick['actual_winner']=g['home'] if float(g['home_goals'])>float(g['away_goals']) else g['away']
                    if pick['eligible']:pick['correct']=pick['winner']==pick['actual_winner']
                picks.append(pick)
            out.extend(assign_ranks(picks))
        old=r.copy();oldx=xr.copy()
        for g in games:
            if not all(present(g.get(k)) for k in ('home_goals','away_goals','home_shots','away_shots')):
                continue
            home,away=g['home'],g['away']
            hg,ag,hs,ass=(float(g[k]) for k in ('home_goals','away_goals','home_shots','away_shots'))
            if not all(math.isfinite(v) and v>=0 for v in (hg,ag,hs,ass)):
                raise ValueError('Invalid goals or shots')
            sig=clip((hs-ass)/30)
            r[home]=.8*old[home]+.2*(sig+old[away]);r[away]=.8*old[away]+.2*(-sig+old[home])
            if all(present(g.get(k)) for k in ('home_xg5v5','away_xg5v5')):
                xh,xa=(float(g[k]) for k in ('home_xg5v5','away_xg5v5'))
                if not all(math.isfinite(v) and v>=0 for v in (xh,xa)):raise ValueError('Invalid xG')
                xs=clip((xh-xa)/2)
                xr[home]=.8*oldx[home]+.2*(xs+oldx[away]);xr[away]=.8*oldx[away]+.2*(-xs+oldx[home])
            else:missing_xg=True
            hist[home].append((hg,ag,hs,ass));hist[away].append((ag,hg,ass,hs))
    return out

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--games',required=True);ap.add_argument('--from-date',required=True);ap.add_argument('--output',default='predictions.json');args=ap.parse_args()
    with open(args.games,newline='') as f:rows=list(csv.DictReader(f))
    result=replay(rows,args.from_date)
    with open(args.output,'w') as f:json.dump(result,f,indent=2,allow_nan=False)
    print(json.dumps(dict(games=len(result),eligible=sum(p['eligible'] for p in result))))

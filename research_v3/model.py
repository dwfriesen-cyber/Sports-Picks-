"""Isolated NFL V3 Reconstruction. Never imported by the production pipeline."""
import datetime as dt
import math
from collections import defaultdict

from nfl import NFL_TEAMS, context_games, expected

VERSION = 'nfl-v3-reconstruction-20261023-r1'
FEATURES = ['v1_margin', 'scoring_net', 'epa_net', 'recent_epa_net',
            'epa_trend', 'success_net', 'redzone_net']


def number(x):
    if isinstance(x, bool) or not isinstance(x, (float, int)) or not math.isfinite(x):
        raise ValueError('Missing/nonfinite NFL research input')
    return x


def rate(rows, side, numerator, denominator, weights=None, zero_prior=False):
    weights = weights if weights is not None else [1.] * len(rows)
    ns = [number(r[side][numerator]) for r in rows]
    ds = [number(r[side][denominator]) for r in rows]
    if any(d < 0 for d in ds):
        raise ValueError('Negative denominator')
    n = sum(w * x for w, x in zip(weights, ns))
    d = sum(w * x for w, x in zip(weights, ds))
    if d == 0 and zero_prior:
        if n != 0: raise ValueError('Nonzero touchdowns with no trips')
        return .5
    if d <= 0: raise ValueError('Zero research denominator')
    if numerator != 'epaSum' and (n < 0 or n > d):
        raise ValueError('Invalid rate numerator')
    return n / d


def team_features(rows):
    def net_epa(rs, ws=None):
        return 60 * (rate(rs, 'off', 'epaSum', 'epaPlays', ws)
                     - rate(rs, 'def', 'epaSum', 'epaPlays', ws))
    recent = rows[-4:]
    weights = [2 ** (-(len(recent)-1-i)/2) for i in range(len(recent))]
    season_epa, recent_epa = net_epa(rows), net_epa(recent, weights)
    return [sum(number(r['off']['pointsScored'])-number(r['def']['pointsAllowed'])
                for r in rows)/len(rows), season_epa, recent_epa,
            recent_epa-season_epa,
            rate(rows, 'off', 'successes', 'successPlays')
            - rate(rows, 'def', 'successes', 'successPlays'),
            rate(rows, 'off', 'rzTdTrips', 'rzTrips', zero_prior=True)
            - rate(rows, 'def', 'rzTdTripsAllowed', 'rzTripsAllowed', zero_prior=True)]


def feature_rows(data, fixtures=None):
    """Validate paired totals via original V1 and emit prior-week-only features.

    fixtures may include future games with no outcome. Completed ties update history
    but receive y=None and are excluded from training/evaluation.
    """
    season = int(data['season'])
    completed = context_games(data)
    detailed = {}
    for team, entry in data['teams'].items():
        if team not in NFL_TEAMS: raise ValueError('Unknown research team')
        for g in entry['games']:
            if g['seasonType'] == 'REG':
                if int(g['gameId'].split('_')[0]) != season: raise ValueError('Wrong season')
                detailed[(g['gameId'], team)] = g
    games = {g['game_id']:g for g in completed}
    for f in fixtures or []:
        if int(f['season']) != season: raise ValueError('Wrong fixture season')
        if f['game_id'] not in games: games[f['game_id']] = f
    hist, basic, result = defaultdict(list), defaultdict(list), []
    for week in sorted({g['week'] for g in games.values()}):
        batch = sorted((g for g in games.values() if g['week']==week), key=lambda g:g['game_id'])
        teams = [g[k] for g in batch for k in ('home','away')]
        if len(set(teams)) != len(teams): raise ValueError('Duplicate team within week')
        for g in batch:
            h,a = g['home'],g['away']
            hp,ap = expected(h,a,basic),expected(a,h,basic)
            if hp is None or ap is None: continue
            margin = hp-ap
            hf,af = team_features(hist[h]),team_features(hist[a])
            hs,aws = g.get('home_stats'),g.get('away_stats')
            y = None if hs is None or hs['pf']==aws['pf'] else int(hs['pf']>aws['pf'])
            result.append(dict(season=season, week=week, game_id=g['game_id'],home=h,away=a,
                prior_home=len(hist[h]),prior_away=len(hist[a]),
                latest_input_week=max(r['week'] for r in hist[h]+hist[a]),
                x=[margin]+[x-y for x,y in zip(hf,af)], y=y,
                winner=h if margin>0 else a, margin=margin,
                zero_rz_denominators=sum(sum(r[side][den] for r in hist[t])==0
                    for t in (h,a) for side,den in [('off','rzTrips'),('def','rzTripsAllowed')])) )
        for g in batch:
            if g.get('home_stats'):
                for side in ('home','away'):
                    t=g[side];hist[t].append(detailed[(g['game_id'],t)])
                    basic[t].append(g[side+'_stats'])
    return result


def fit(rows, features):
    import numpy as np
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression
    rows = [r for r in rows if r['y'] is not None]
    indices = [FEATURES.index(f) for f in features]
    X=np.array([[r['x'][i] for i in indices] for r in rows]);y=np.array([r['y'] for r in rows])
    scaler=StandardScaler().fit(X)
    clf=LogisticRegression(C=1.,solver='lbfgs',fit_intercept=True,
                           class_weight=None,tol=1e-10,max_iter=10000).fit(scaler.transform(X),y)
    if max(clf.n_iter_) >= 10000: raise ValueError('Logistic fit did not converge')
    coef=clf.coef_[0];raw=coef/scaler.scale_
    return dict(features=features,means=scaler.mean_.tolist(),scales=scaler.scale_.tolist(),
        intercept=float(clf.intercept_[0]),coefficients=coef.tolist(),
        raw_intercept=float(clf.intercept_[0]-np.dot(raw,scaler.mean_)),
        raw_coefficients=raw.tolist(),training_seasons=sorted({r['season'] for r in rows}),
        training_games=len(rows),iterations=int(clf.n_iter_[0]),regularization='L2',C=1.,
        solver='lbfgs',tol=1e-10,max_iter=10000,scaling='training-only population standard deviation')


def probability(model, row):
    z=model['intercept']+sum(c*(number(row['x'][FEATURES.index(f)])-m)/s
        for f,c,m,s in zip(model['features'],model['coefficients'],model['means'],model['scales']))
    return 1/(1+math.exp(-z)) if z>=0 else math.exp(z)/(1+math.exp(z))


def attach(rows,p1_model,p2_model):
    out=[]
    for r in rows:
        if max(p1_model['training_seasons']+p2_model['training_seasons'])>=r['season']:
            raise ValueError('Training/evaluation season leakage')
        p1,p2=probability(p1_model,r),probability(p2_model,r)
        p3=(p1+p2)/2;home=r['winner']==r['home']
        y=r['y'];q=dict(r,model_version=VERSION,p1=p1,p2=p2,p3=p3,
            v1_confidence=p1 if home else 1-p1,v2_confidence=max(p2,1-p2),
            v3_confidence=p3 if home else 1-p3,raw_confidence=abs(r['margin']),
            v2_winner=r['home'] if p2>=.5 else r['away'],
            v3_disagreement=(p3>=.5)!=home,
            v1_correct=None if y is None else home==bool(y),
            v2_correct=None if y is None else (p2>=.5)==bool(y))
        out.append(q)
    return out


def ranked(rows,score):
    return sorted(rows,key=lambda r:(-r[score],r['game_id']))


def weekly_top(rows,score,correct):
    groups=defaultdict(list)
    for r in rows:
        if r['y'] is not None: groups[(r['season'],r['week'])].append(r)
    result=[]
    for (season,week),batch in sorted(groups.items()):
        top=ranked(batch,score)[:math.ceil(len(batch)/4)]
        result.append(dict(season=season,week=week,eligible=len(batch),games=len(top),
                           wins=sum(r[correct] for r in top),ids=[r['game_id'] for r in top]))
    return result


def probability_metrics(rows,key):
    rs=[r for r in rows if r['y'] is not None];n=len(rs)
    bins=[]
    for i in range(10):
        b=[r for r in rs if min(int(r[key]*10),9)==i]
        bins.append(dict(lower=i/10,upper=(i+1)/10,n=len(b),
            predicted=sum(r[key] for r in b)/len(b) if b else None,
            observed=sum(r['y'] for r in b)/len(b) if b else None))
    return dict(n=n,brier=sum((r[key]-r['y'])**2 for r in rs)/n,
        log_loss=-sum(r['y']*math.log(max(r[key],1e-15))+(1-r['y'])*math.log(max(1-r[key],1e-15)) for r in rs)/n,
        ece=sum(b['n']*abs(b['predicted']-b['observed']) for b in bins if b['n'])/n,
        calibration_bins=bins)


def summarize(rows):
    rows=[r for r in rows if r['y'] is not None]
    tops={name:weekly_top(rows,score,correct) for name,score,correct in [
        ('raw_v1','raw_confidence','v1_correct'),('fitted_v1','v1_confidence','v1_correct'),
        ('v2','v2_confidence','v2_correct'),('v3','v3_confidence','v1_correct')]}
    paired=[]
    for baseline in ('raw_v1','fitted_v1'):
        for v1,v3 in zip(tops[baseline],tops['v3']):
            paired.append(dict(baseline=baseline,season=v1['season'],week=v1['week'],v1_wins=v1['wins'],v3_wins=v3['wins'],
                delta=v3['wins']-v1['wins'],removed=sorted(set(v1['ids'])-set(v3['ids'])),
                added=sorted(set(v3['ids'])-set(v1['ids']))))
    return dict(n=len(rows),v1_wins=sum(r['v1_correct'] for r in rows),
        p1_threshold_wins=sum((r['p1']>=.5)==bool(r['y']) for r in rows),
        v2_wins=sum(r['v2_correct'] for r in rows),v3_preserved_winner_wins=sum(r['v1_correct'] for r in rows),
        disagreement_games=sum(r['v3_disagreement'] for r in rows),
        top_quarter={k:dict(wins=sum(w['wins'] for w in v),games=sum(w['games'] for w in v),weeks=v) for k,v in tops.items()},
        probability_metrics={k:probability_metrics(rows,k) for k in ('p1','p2','p3')},
        paired_weeks=paired,paired_summary={b:dict(improved=sum(w['delta']>0 for w in paired if w['baseline']==b),
            worsened=sum(w['delta']<0 for w in paired if w['baseline']==b),unchanged=sum(w['delta']==0 for w in paired if w['baseline']==b),
            net_wins=sum(w['delta'] for w in paired if w['baseline']==b)) for b in ('raw_v1','fitted_v1')})


def weekly_slate(rows, fixtures, now, pool_scale=None):
    """Complete weekly pool only. Callers validate all prior-week source coverage."""
    if now.tzinfo is None: raise ValueError('Timezone-aware freeze time required')
    if not fixtures: raise ValueError('Empty weekly schedule')
    if len({(f['season'],f['week']) for f in fixtures})!=1: raise ValueError('Mixed weeks')
    if len({f['game_id'] for f in fixtures})!=len(fixtures): raise ValueError('Duplicate fixture')
    if now>=min(dt.datetime.fromisoformat(f['start_time'].replace('Z','+00:00')) for f in fixtures):
        raise ValueError('Weekly freeze missed earliest kickoff')
    if {r['game_id'] for r in rows}!={f['game_id'] for f in fixtures} or len(rows)!=len(fixtures):
        raise ValueError('Incomplete eligible weekly confidence pool')
    if any((r['season'],r['week'])!=(fixtures[0]['season'],fixtures[0]['week']) for r in rows):
        raise ValueError('Wrong forecast week')
    if any(r['latest_input_week']>=r['week'] or r['y'] is not None for r in rows):
        raise ValueError('Non-pregame weekly inputs')
    n=len(rows);scale=list(range(1,n+1)) if pool_scale is None else list(pool_scale)
    if len(scale)!=n or len(set(scale))!=n or any(number(p)<=0 for p in scale) or scale!=sorted(scale):
        raise ValueError('Pool scale must contain N distinct positive ascending values')
    starts={f['game_id']:f['start_time'] for f in fixtures}
    return dict(model_version=VERSION,label='V3 Reconstruction — research only',
        frozen_at=now.isoformat(),season=fixtures[0]['season'],week=fixtures[0]['week'],
        picks=[dict(r,rank=i+1,pool_points=scale[-1-i],top25=i<math.ceil(n/4),
                    start_time=starts[r['game_id']]) for i,r in enumerate(ranked(rows,'v3_confidence'))])

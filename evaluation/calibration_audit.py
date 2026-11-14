"""Research-only walk-forward calibration of immutable NHL V6 picks.

No network, quote fabrication, model/pick edits, ledger writes, or live promotion.
Input is a pinned GitHub bundle: {ref, files:[{path,blob_sha,content}]}.
This is retrospective evaluation of a NEW calibration layer, not a claim that
these probability estimates existed when original picks were published.
"""
import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path

VERSION = 'nhl-v6-margin-calibration-research-20261114'
MIN_TRAIN = 50
RIDGE = 1.0

def instant(value):
    x = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if x.tzinfo is None:
        raise ValueError('Timezone required')
    return x

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()

def records(bundle):
    """Strict ID/hash join. Conflicting grade revisions must be reconciled, not guessed."""
    picks, grades = {}, {}
    for f in bundle['files']:
        x = f['content']
        if f['path'].startswith('frozen/nhl/'):
            if x['kind'] != 'nhl_v6_v7a':
                raise ValueError('Wrong model kind')
            for p in x['picks']:
                if p['game_id'] in picks:
                    raise ValueError('Duplicate frozen game')
                if not p['eligible'] or p['winner'] not in (p['home'], p['away']):
                    raise ValueError('Invalid frozen pick')
                if p['model_version'] != 'nhl-v6-v7a-original-20261016':
                    raise ValueError('Mixed model version')
                if instant(x['frozen_at']) >= instant(p['start_time']):
                    raise ValueError('Late freeze')
                margin = float(p['margin'])
                if not math.isfinite(margin):
                    raise ValueError('Nonfinite margin')
                if p['winner'] != (p['home'] if margin > 0 else p['away']):
                    raise ValueError('V6 winner/margin mismatch')
                picks[p['game_id']] = dict(p, feature=abs(margin), frozen_at=x['frozen_at'], forecast_sha256=digest(x))
        elif f['path'].startswith('grading/nhl/'):
            if x['game_id'] in grades:
                raise ValueError('Multiple grade versions; reconcile first')
            grades[x['game_id']] = x
    result = []
    for gid, p in picks.items():
        g = grades.get(gid)
        if g:
            if g['forecast_sha256'] != p['forecast_sha256'] or g['winner'] != p['winner'] or g['model'] != 'nhl_v6_v7a':
                raise ValueError('Grade does not match frozen source')
            if g['actual_winner'] not in (p['home'], p['away']):
                raise ValueError('Invalid actual winner')
            if g['correct'] != (g['actual_winner'] == p['winner']):
                raise ValueError('Grade inconsistency')
            if instant(g['graded_at']) < instant(p['start_time']):
                raise ValueError('Grade predates start')
            p.update(correct=int(g['correct']), graded_at=g['graded_at'])
        result.append(p)
    return sorted(result, key=lambda x:(x['frozen_at'], x['game_id']))

def logistic(z):
    z = max(-35.0, min(35.0, z))
    return 1.0 / (1.0 + math.exp(-z))

def fit(train):
    """Fixed two-parameter ridge logistic fit; no search or held-out tuning."""
    if len(train) < MIN_TRAIN or {r['correct'] for r in train} != {0, 1}:
        raise ValueError('Insufficient training outcomes')
    mean = sum(r['feature'] for r in train) / len(train)
    scale = math.sqrt(sum((r['feature']-mean)**2 for r in train)/len(train)) or 1.0
    a, b = 0.0, 0.0
    for _ in range(80):
        ga, gb, haa, hab, hbb = 0.0, RIDGE*b, 0.0, 0.0, RIDGE
        for r in train:
            z = (r['feature']-mean)/scale
            p = logistic(a+b*z)
            w = p*(1-p)
            ga += p-r['correct']; gb += (p-r['correct'])*z
            haa += w; hab += w*z; hbb += w*z*z
        determinant = haa*hbb-hab*hab
        if determinant <= 1e-12:
            raise ValueError('Singular fit')
        da, db = (hbb*ga-hab*gb)/determinant, (haa*gb-hab*ga)/determinant
        # Bounded Newton step prevents numerical divergence, not data tuning.
        factor = max(1.0, abs(da)/2.0, abs(db)/2.0)
        a -= da/factor; b -= db/factor
        if max(abs(da),abs(db)) < 1e-8:
            return dict(intercept=a, slope=b, mean=mean, scale=scale, train_n=len(train))
    raise ValueError('Fit did not converge')

def predict(model, feature):
    return logistic(model['intercept'] + model['slope']*(feature-model['mean'])/model['scale'])

def metrics(rows):
    if not rows:
        return dict(n=0, brier=None, log_loss=None, baseline_brier=None)
    return dict(n=len(rows), brier=sum((r['probability']-r['correct'])**2 for r in rows)/len(rows),
                log_loss=-sum(r['correct']*math.log(r['probability'])+(1-r['correct'])*math.log(1-r['probability']) for r in rows)/len(rows),
                baseline_brier=sum((r['baseline_probability']-r['correct'])**2 for r in rows)/len(rows))

def audit(bundle):
    data = records(bundle)
    scored, untrained = [], []
    for r in data:
        train = [x for x in data if 'correct' in x and instant(x['graded_at']) < instant(r['frozen_at']) and instant(x['start_time']) < instant(r['frozen_at'])]
        if len(train) < MIN_TRAIN:
            untrained.append(r['game_id']); continue
        model = fit(train)
        probability = predict(model, r['feature'])
        row = dict(game_id=r['game_id'], date=r['date'], winner=r['winner'], start_time=r['start_time'],
                   original_frozen_at=r['frozen_at'], probability=probability,
                   baseline_probability=sum(x['correct'] for x in train)/len(train),
                   train_n=len(train), latest_training_grade=max((x['graded_at'] for x in train), key=instant),
                   coefficients=model, research_only=True)
        if 'correct' in r: row['correct'] = r['correct']
        scored.append(row)
    evaluated = [r for r in scored if 'correct' in r]
    return dict(schema_version=1, research_model=VERSION, source_ref=bundle['ref'],
                status='research_only_not_promoted', feature='absolute original V6 margin; not V7-A confidence',
                original_frozen_picks=len(data), joined_outcomes=sum('correct' in r for r in data),
                min_train=MIN_TRAIN, ridge=RIDGE, insufficient_training_ids=untrained,
                walk_forward_metrics=metrics(evaluated), predictions=scored,
                value_evaluation='BLOCKED', blockers=['No approved calibration promotion/adequacy decision',
                  'No integrated observed pregame same-book price feed', 'No preregistered validated price-margin policy'],
                limitations=['New retrospective calibration, not probabilities published with original picks',
                  'Small single-season sample and shared-day dependence',
                  'No profitability, return, or positive-EV claim; no ticket created'])

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--bundle')
    source.add_argument('--state-root', help='Read-only checkout of the picks-data branch')
    parser.add_argument('--source-ref', help='Exact checked-out state commit, required with --state-root')
    args = parser.parse_args()
    if args.bundle:
        bundle = json.loads(Path(args.bundle).read_text())
    else:
        if not args.source_ref:
            parser.error('--source-ref required with --state-root')
        root = Path(args.state_root)
        paths = sorted((root/'frozen'/'nhl').glob('*.json')) + sorted((root/'grading'/'nhl').glob('*/*.json'))
        if not paths:
            parser.error('No NHL state files')
        bundle = dict(ref=args.source_ref, files=[dict(path=p.relative_to(root).as_posix(), content=json.loads(p.read_text())) for p in paths])
    print(json.dumps(audit(bundle), indent=2, allow_nan=False))

"""Daily deterministic pipeline. Unavailable original models remain explicitly blocked."""
import argparse,datetime as dt,json,os,sys
from collections import defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo
from engine import replay
from ingest_nhl import collect_full
import nfl,shadow
from ledger import append,digest,freeze,grade,timestamp
from scripts.reconstruct import stats
TZ=ZoneInfo('America/Regina')

def prospective(p):
    allowed=['date','game_id','home','away','home_name','away_name','start_time','winner','margin','v1_margin','confidence','confidence_margin','confidence_status','prior_games','model_version','rank','top25','eligible']
    return {k:p[k] for k in allowed if k in p}

def historical_report(games):
    rows=json.loads(Path('ledgers/historical/v6-reconstructed-oct18-23.json').read_text())
    actual={g['game_id']:g for g in games if 'home_goals' in g}
    for r in rows:
        g=actual.get(r['game_id'])
        if g:
            r['actual_winner']=g['home'] if g['home_goals']>g['away_goals'] else g['away']
            for key in ['v6','published','v8_lite']:r[key+'_correct']=r[key+'_winner']==r['actual_winner']
    summary={k:stats(rows,w,r) for k,w,r in [('v6_v7a_reconstructed','v6_winner','v7a_rank'),('published','published_winner','published_rank'),('v8_lite','v8_lite_winner','v8_lite_rank')]}
    ds=[r for r in rows if r['v6_v8_disagree'] and r['actual_winner']]
    return {'rows':rows,'summary':summary,'disagreements':{'graded':len(ds),'v6_wins':sum(r['v6_correct'] for r in ds),'v8_wins':sum(r['v8_lite_correct'] for r in ds)},'coverage':'Recovered October 18–23 only; reconstructed V6 is separate from prospective forecasts.'}

def freeze_nfl(games,root,now,code,freeze_clock):
    future=[g for g in games if timestamp(g['start_time'])>now]
    if not future:return {'v1_status':'no_games','v3_status':'blocked','reason':nfl.NFL_V3_BLOCKER}
    week=min(future,key=lambda g:timestamp(g['start_time']))['week'];year=future[0]['season']
    if any(g.get('home_stats') is None for g in games if g['week']<week):raise ValueError('NFL previous-week play data incomplete')
    # Predict the full week with previous weeks only; freeze each date before its first kickoff.
    # Thursday, Sunday (including international), Monday and unusual game days are independent slots.
    predictions=[p for p in nfl.replay(games) if p['week']==week]
    ih=digest(games);append(root/'inputs'/('nfl-'+ih+'.json'),games)
    groups=defaultdict(list)
    for p in predictions:groups[p['date']].append(p)
    slates=[];missed=[]
    for date,items in sorted(groups.items()):
        path=root/'frozen'/'nfl'/(date+'.json')
        if min(timestamp(p['start_time']) for p in items)<=now and not path.exists():
            missed.append(date);continue
        picks=[{k:p[k] for k in ['game_id','date','week','home','away','start_time','winner','margin','eligible','model_version'] if k in p} for p in items]
        slates.append(freeze(path,picks,freeze_clock(),ih,code,'nfl_v1_only'))
    return {'v1_status':'frozen' if slates else 'missed','week':week,'slates':slates,'missed_dates':missed,'v3_status':'blocked','reason':nfl.NFL_V3_BLOCKER,'weekly_confidence_rankings':None}

def run(root,source_dir,now=None,nhl_games=None,nfl_games=None,ice=None):
    fixed_clock=now is not None
    now=now or dt.datetime.now(dt.timezone.utc)
    clock=(lambda:now) if fixed_clock else (lambda:dt.datetime.now(dt.timezone.utc))
    today=now.astimezone(TZ).date();date=today.isoformat()
    root=Path(root);root.mkdir(parents=True,exist_ok=True);Path('reports').mkdir(exist_ok=True)
    code=os.environ.get('SPORTS_SOURCE_SHA',os.environ.get('GITHUB_SHA','local-unpublished'))
    report={'schema_version':1,'generated_at':now.isoformat(),'report_date':date,'timezone':'America/Regina','valid_until':dt.datetime.combine(today+dt.timedelta(days=1),dt.time(6),TZ).isoformat(),'code_sha':code,'status':'partial','nhl':{},'nfl':{},'v8':{}}
    safe_nhl=False
    try:
        if nhl_games is None:nhl_games,quality=collect_full(date,source_dir)
        else:quality={'completed_games':sum('home_goals' in g for g in nhl_games),'source':'injected-test-or-recovery'}
        prior=[g for g in nhl_games if g['date']<date]
        unresolved=[g['game_id'] for g in prior if 'home_goals' not in g and g.get('schedule_state') not in ('PPD','CNCL')]
        if unresolved:raise ValueError('Prior-date games not final: '+','.join(unresolved))
        missing=[g['game_id'] for g in prior if 'home_goals' in g and ('home_xg5v5' not in g or 'away_xg5v5' not in g)]
        if missing:raise ValueError('Missing prior-game raw 5v5 xG: '+','.join(missing))
        safe_nhl=True
        inputs={'sport':'NHL','cutoff_exclusive_date':date,'games':nhl_games}
        ih=digest(inputs);append(root/'inputs'/('nhl-'+ih+'.json'),inputs)
        picks=[p for p in replay(nhl_games,date,date) if p['date']==date]
        if picks:
            if any(not p.get('eligible') or p.get('rank') is None for p in picks):raise ValueError('NHL slate incomplete or confidence unavailable')
            slate=freeze(root/'frozen'/'nhl'/(date+'.json'),[prospective(p) for p in picks],clock(),ih,code,'nhl_v6_v7a')
            report['nhl']={'status':'frozen','quality':quality,'slate':slate}
        else:report['nhl']={'status':'no_games','quality':quality,'picks':[]}
    except Exception as exc:report['nhl']={'status':'blocked','reason':str(exc)}
    if safe_nhl:
        report['historical']=historical_report(nhl_games)
        append(root/'grading'/'historical'/(digest(report['historical'])+'.json'),report['historical'])
        Path('reports/nhl-current-inputs.json').write_text(json.dumps(nhl_games,indent=2))
    try:
        if not safe_nhl:raise ValueError('NHL source coverage unavailable')
        original=json.loads(Path('ledgers/historical/imported-chat-picks.json').read_text())['days'].get(date)
        if not any(g['date']==date for g in nhl_games):
            report['v8']={'status':'no_games'}
        elif original:
            report['v8']={'status':'preserved_historical','original_source_time':original['shadow_source_message_time'],'winner_order':original['shadow'],'note':'Original published V8-lite picks remain fixed. Newly downloaded inputs do not replace them.'}
        else:
            if ice is None:ice=shadow.collect(date,source_dir)
            candidates=shadow.predict(nhl_games,date,ice)
            inputs={'games':nhl_games,'ice':ice};ih=digest(inputs);append(root/'inputs'/('v8-'+ih+'.json'),inputs)
            if candidates:report['v8']={'status':'frozen','slate':freeze(root/'frozen'/'v8'/(date+'.json'),candidates,clock(),ih,code,'nhl_v8_lite')}
            else:report['v8']={'status':'no_games'}
    except Exception as exc:report['v8']={'status':'blocked','reason':str(exc)}
    try:
        year=today.year if today.month>=8 else today.year-1
        if nfl_games is None:nfl_games=nfl.collect(year,source_dir)
        report['nfl']=freeze_nfl(nfl_games,root,now,code,clock)
        Path('reports/nfl-current-inputs.json').write_text(json.dumps(nfl_games,indent=2))
    except Exception as exc:report['nfl']={'v1_status':'blocked','v3_status':'blocked','reason':str(exc),'v3_reason':nfl.NFL_V3_BLOCKER}
    # Grade independently of today's freeze success, preserving every prior forecast.
    report['grading']=grade(root,(nhl_games or [])+(nfl_games or []),clock())
    report['prospective_summary']=grade_summary(report['grading'])
    if safe_nhl:report['v8_tracking']=shadow_tracking(root,report['historical']['rows'],nhl_games)
    report['source_receipts']=[json.loads(p.read_text()) for p in sorted(Path(source_dir).glob('*.receipt.json'))]
    for receipt in report['source_receipts']:append(root/'source-receipts'/(digest(receipt)+'.json'),receipt)
    attempt=clock().strftime('%Y%m%dT%H%M%S%fZ')
    append(root/'runs'/(attempt+'.json'),report)
    (root/'latest.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    return report

def shadow_tracking(root,historical,games):
    # Imported historical selections stay intact; append future shadow records by game ID.
    rows={r['game_id']:dict(r,comparison_basis='retrospective V6 reconstruction') for r in historical}
    finals={str(g['game_id']):g for g in games if 'home_goals' in g}
    official={}
    for path in sorted((root/'frozen'/'nhl').glob('*.json')):
        for p in json.loads(path.read_text())['picks']:official[str(p['game_id'])]=p
    for path in sorted((root/'frozen'/'v8').glob('*.json')):
        for p in json.loads(path.read_text())['picks']:
            gid=str(p['game_id'])
            if gid in rows:raise ValueError('Prospective shadow overlaps preserved historical ledger')
            g=finals.get(gid);v6=official.get(gid)
            actual=None if not g else g['home'] if g['home_goals']>g['away_goals'] else g['away']
            rows[gid]={'game_id':gid,'date':p['date'],'v8_lite_winner':p['winner'],'v8_lite_rank':p['rank'],'actual_winner':actual,'v6_winner':None if not v6 else v6['winner'],'comparison_basis':'prospective frozen V6' if v6 else 'V6 unavailable'}
    batch=list(rows.values())
    disagreements=[r for r in batch if r['actual_winner'] and r.get('v6_winner') and r['v6_winner']!=r['v8_lite_winner']]
    return {'coverage_start':'2026-10-18','coverage_note':'Season totals cover the recovered ledger from October 18 onward; earlier picks were not recovered.','metrics':stats(batch,'v8_lite_winner','v8_lite_rank'),'same_game_disagreements':{'graded':len(disagreements),'v6_correct':sum(r['v6_winner']==r['actual_winner'] for r in disagreements),'v8_correct':sum(r['v8_lite_winner']==r['actual_winner'] for r in disagreements),'rows':disagreements}}

def grade_summary(grades):
    result={}
    for model in sorted({g['model'] for g in grades}):
        rows=[dict(date=g['date'],actual_winner=g['actual_winner'],winner=g['winner'],rank=g.get('rank')) for g in grades if g['model']==model and g['actual_winner']]
        result[model]=stats(rows,'winner','rank') if rows else {}
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',default='state');p.add_argument('--sources',default='data/sources');a=p.parse_args()
    r=run(a.state,a.sources)
    print(json.dumps({k:r[k] for k in ['report_date','status']}));print('NHL:',r['nhl']['status'],'NFL V1:',r['nfl']['v1_status'],'NFL V3:',r['nfl']['v3_status'],'V8:',r['v8']['status'])
    if r['nhl']['status']=='blocked' or r['v8']['status']=='blocked' or r['nfl']['v1_status']=='blocked':sys.exit(1)

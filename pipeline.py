"""Daily deterministic pipeline. Partial components are explicit; no substitutions."""
import argparse,datetime as dt,json,os,sys
from pathlib import Path
from zoneinfo import ZoneInfo
from engine import replay
from ingest_nhl import collect_full
import nfl
from ledger import append,digest,freeze,grade,timestamp
from scripts.reconstruct import reconstruct
TZ=ZoneInfo('America/Regina')

def prospective(p):
    allowed=['date','game_id','home','away','home_name','away_name','start_time','winner','margin','v1_margin','confidence','confidence_margin','confidence_status','prior_games','model_version','rank','top25','eligible']
    return {k:p[k] for k in allowed if k in p}

def run(root,source_dir,now=None,nhl_games=None,nfl_games=None):
    fixed_clock=now is not None
    now=now or dt.datetime.now(dt.timezone.utc);today=now.astimezone(TZ).date();date=today.isoformat()
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    code=os.environ.get('GITHUB_SHA','local-unpublished')
    report={'schema_version':1,'generated_at':now.isoformat(),'report_date':date,'timezone':'America/Regina','valid_until':dt.datetime.combine(today+dt.timedelta(days=1),dt.time(6),TZ).isoformat(),'code_sha':code,'status':'partial','nhl':{},'nfl':{},'v8':{'status':'blocked','reason':'IceScope last-five xgBalance60 source adapter pending validation; historical shadow ledger preserved.'}}
    try:
        if nhl_games is None:nhl_games,quality=collect_full(date,source_dir)
        else:quality={'completed_games':sum('home_goals' in g for g in nhl_games),'source':'injected-test-or-recovery'}
        prior=[g for g in nhl_games if g['date']<date]
        unresolved=[g['game_id'] for g in prior if 'home_goals' not in g and g.get('schedule_state') not in ('PPD','CNCL')]
        if unresolved:raise ValueError('Prior-date games not final: '+','.join(unresolved))
        missing=[g['game_id'] for g in prior if 'home_goals' in g and ('home_xg5v5' not in g or 'away_xg5v5' not in g)]
        if missing:raise ValueError('Missing prior-game raw 5v5 xG: '+','.join(missing))
        inputs={'sport':'NHL','cutoff_exclusive_date':date,'games':nhl_games}
        ih=digest(inputs);append(root/'inputs'/('nhl-'+ih+'.json'),inputs)
        picks=[p for p in replay(nhl_games,date,date) if p['date']==date]
        if picks:
            if any(not p.get('eligible') or p.get('rank') is None for p in picks):raise ValueError('NHL slate incomplete or confidence unavailable')
            slate=freeze(root/'frozen'/'nhl'/(date+'.json'),[prospective(p) for p in picks],now if fixed_clock else dt.datetime.now(dt.timezone.utc),ih,code,'nhl_v6_v7a')
            report['nhl']={'status':'frozen','quality':quality,'slate':slate}
        else:report['nhl']={'status':'no_games','quality':quality,'picks':[]}
        report['nhl']['grading']=grade(root,nhl_games,now)
        (Path('reports')/'nhl-current-inputs.json').write_text(json.dumps(nhl_games,indent=2))
    except Exception as exc:report['nhl']={'status':'blocked','reason':str(exc)}
    try:
        year=today.year if today.month>=8 else today.year-1
        if nfl_games is None:nfl_games=nfl.collect(year,source_dir)
        # Freeze every remaining game of a week together, before its earliest kickoff.
        active=sorted({g['week'] for g in nfl_games if timestamp(g['start_time'])>now and (timestamp(g['start_time']).astimezone(TZ).date()-today).days<=7})
        if active:
            week=active[0];batch=[p for p in nfl.replay(nfl_games) if p['week']==week]
            if any(p.get('home_score') is not None for p in batch) and not (root/'frozen'/'nfl'/f'{year}-{week:02d}.json').exists():
                raise ValueError('NFL weekly freeze missed earliest kickoff; no late weekly confidence slate issued')
            ih=digest(nfl_games);append(root/'inputs'/('nfl-'+ih+'.json'),nfl_games)
            picks=[{k:p[k] for k in ['game_id','date','week','home','away','start_time','winner','margin','eligible','model_version'] if k in p} for p in batch]
            slate=freeze(root/'frozen'/'nfl'/f'{year}-{week:02d}.json',picks,now if fixed_clock else dt.datetime.now(dt.timezone.utc),ih,code,'nfl_v1_only')
            report['nfl']={'v1_status':'frozen','slate':slate,'v3_status':'blocked','reason':nfl.NFL_V3_BLOCKER}
        else:report['nfl']={'v1_status':'no_games','v3_status':'blocked','reason':nfl.NFL_V3_BLOCKER}
        (Path('reports')/'nfl-current-inputs.json').write_text(json.dumps(nfl_games,indent=2))
    except Exception as exc:report['nfl']={'v1_status':'blocked','v3_status':'blocked','reason':str(exc),'v3_reason':nfl.NFL_V3_BLOCKER}
    # Keep an auditable status for every attempt; latest always advertises partial/blocked.
    attempt=now.strftime('%Y%m%dT%H%M%S%fZ')
    append(root/'runs'/(attempt+'.json'),report)
    (root/'latest.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',default='state');p.add_argument('--sources',default='data/sources');a=p.parse_args()
    Path('reports').mkdir(exist_ok=True)
    r=run(a.state,a.sources)
    print(json.dumps({k:r[k] for k in ['report_date','status']}));print('NHL:',r['nhl']['status'],'NFL V1:',r['nfl']['v1_status'],'NFL V3:',r['nfl']['v3_status'])
    if r['nhl']['status']=='blocked':sys.exit(1)

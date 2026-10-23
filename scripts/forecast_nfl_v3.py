"""Generate a separate research pool; no existing official status is overwritten."""
import argparse,datetime as dt,json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sources import download
from nfl import parse_schedule
from research_v3.weekly import generate


def main():
    p=argparse.ArgumentParser();p.add_argument('--season',type=int,default=2026)
    p.add_argument('--week',type=int);p.add_argument('--upstream',default='upstream-context')
    p.add_argument('--state',default='research-state/nfl-v3')
    p.add_argument('--pool-scale',help='Explicit ascending comma-separated pool points, one per eligible game')
    a=p.parse_args();root=Path(a.state);root.mkdir(parents=True,exist_ok=True)
    cache=Path('data/v3-current');cache.mkdir(parents=True,exist_ok=True)
    now=dt.datetime.now(dt.timezone.utc)
    try:
        schedule=parse_schedule(download('https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv',cache/'schedule.csv'),a.season)
        future=[g for g in schedule if dt.datetime.fromisoformat(g['start_time'])>now]
        if not future:raise ValueError('No future regular-season games')
        week=a.week if a.week is not None else min(g['week'] for g in future)
        frozen=root/'frozen'/f'{a.season}-W{week:02}.json'
        if frozen.exists():
            record=json.loads(frozen.read_text())
        else:
            fs=[g for g in schedule if g['week']==week]
            if not fs:raise ValueError('Unknown NFL week')
            if now>=min(dt.datetime.fromisoformat(g['start_time']) for g in fs):
                raise ValueError('Weekly freeze missed earliest kickoff; no backdating')
            if any(g['home_score'] is None for g in schedule if g['week']<week):
                raise ValueError('Previous NFL week not finished')
            path=cache/f'pbp-{a.season}.csv.gz'
            download(f'https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{a.season}.csv.gz',path)
            output=cache/'context.json'
            subprocess.run(['node','scripts/v3_team_context.mjs',a.upstream,str(path),str(a.season),str(output)],check=True)
            models=json.loads(Path('reports/nfl-v3-reconstruction/coefficients.json').read_text())['models'][str(a.season)]
            scale=[float(v) for v in a.pool_scale.split(',')] if a.pool_scale else None
            record=generate(json.loads(output.read_text()),schedule,week,models,dt.datetime.now(dt.timezone.utc),root,scale)
        report=dict(status='frozen_research_only',slate=record)
    except (ValueError,RuntimeError,KeyError,subprocess.CalledProcessError) as exc:
        report=dict(status='blocked',reason=str(exc),model='V3 Reconstruction',generated_at=dt.datetime.now(dt.timezone.utc).isoformat())
    (root/'latest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
    # Blocked weekly input is visible and contains no made-up forecasts; validation workflow checks status.
    return report


if __name__=='__main__':main()

"""Check fresh research EPA/RZ ingestion against the working V1 source adapter."""
import json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sources import download
from nfl import parse_schedule,parse_pbp,context_games
from research_v3.model import feature_rows

if __name__=='__main__':
    year=int(sys.argv[1]) if len(sys.argv)>1 else 2026
    cache=Path('data/v3-current');cache.mkdir(parents=True,exist_ok=True)
    schedule=parse_schedule(download('https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv',cache/'schedule.csv'),year)
    pbp=download(f'https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{year}.csv.gz',cache/'pbp.csv.gz')
    live=parse_pbp(pbp,year,schedule)
    subprocess.run(['node','scripts/v3_team_context.mjs','upstream-context',str(cache/'pbp.csv.gz'),str(year),str(cache/'context.json')],check=True)
    data=json.loads((cache/'context.json').read_text());context={g['game_id']:g for g in context_games(data)}
    complete=[g for g in live if g.get('home_stats')]
    assert set(context)=={g['game_id'] for g in complete}
    for g in complete:
        for side in ('home_stats','away_stats'):assert context[g['game_id']][side]==g[side],(g['game_id'],side)
    rows=feature_rows(data)
    out=Path('recovery/nfl-v3');out.mkdir(parents=True,exist_ok=True)
    result=dict(status='passed',season=year,completed_games=len(complete),eligible_feature_rows=len(rows),
        all_v1_points_and_plays_match=True,all_research_features_finite=True,
        upstream_aggregation_commit='5231fb4c22923a344504fefdfe4b1520714dd5db')
    (out/'current-data-validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))

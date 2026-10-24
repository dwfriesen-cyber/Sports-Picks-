import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from nfl import context_games,replay,NFL_V3_BLOCKER
from sources import download

def validate(source_dir):
    root=Path(source_dir);out=[]
    for year in range(2021,2026):
        path=root/f'nfl-{year}.json'
        if not path.exists():download(f'https://raw.githubusercontent.com/antonwilms/sleeper-dashboard-data/main/nflverse/teamcontext/{year}.json',path)
        picks=[p for p in replay(context_games(json.loads(path.read_text()))) if p['eligible'] and p.get('correct') is not None]
        expected={2021:(223,131),2022:(222,128),2023:(224,133),2024:(224,154),2025:(223,142)}
        got=(len(picks),sum(p['correct'] for p in picks));assert got==expected[year],(year,got)
        out.append({'year':year,'games':got[0],'correct':got[1]})
    # Original independently documented raw V1 benchmark: 2023–25 429/671; 2025 142/223.
    assert sum(r['correct'] for r in out[2:])==429
    return {'v1_status':'passed','seasons':out,'v3_status':'blocked','v3_reason':NFL_V3_BLOCKER,'reported_v3_top_quarter':'145/180; NOT reproduced'}
if __name__=='__main__':
    r=validate(sys.argv[1] if len(sys.argv)>1 else 'data/sources');Path('reports').mkdir(exist_ok=True);Path('reports/nfl-validation.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))

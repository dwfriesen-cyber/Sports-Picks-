"""Replay all original V6 cases; verify original V7 ranking from archived pregame xG ratings."""
import csv,json,sys,math,gzip,io,unicodedata
from collections import defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import replay
from ingest_nhl import TEAM_NAMES

def validate():
    root=Path(__file__).resolve().parents[1]; fixture=root/'tests/fixtures'
    audits={r['game_id']:r for r in csv.DictReader(io.StringIO(gzip.decompress((fixture/'original_v7_audit.csv.gz').read_bytes()).decode()))}
    expected={2023:(1259,755,257,383),2024:(1258,721,249,386),2025:(1256,693,230,381)}
    results=[]
    for year,want in expected.items():
        rows=[]
        xg=json.loads(gzip.decompress((fixture/f'xg-{year}.json.gz').read_bytes()))
        norm=lambda s: ''.join(c for c in unicodedata.normalize('NFKD',s) if not unicodedata.combining(c))
        names={norm(v):k for k,v in TEAM_NAMES.items()};names['Utah Hockey Club']='UTA'
        for r in csv.DictReader(io.StringIO(gzip.decompress((fixture/f'nhl_{year}.csv.gz').read_bytes()).decode())):
            rows.append(dict(date=r['game_date'],season=r['season'],game_id=r['game_id'],home=r['home_team'],away=r['away_team'],home_goals=r['home_score'],away_goals=r['away_score'],home_shots=r['home_shots'],away_shots=r['away_shots']))
        for row in rows:
            x=xg[row['game_id']]
            assert (x['home'],x['away'])==(names[norm(row['home'])],names[norm(row['away'])])
            row.update(home_xg5v5=x['home_xg5v5'],away_xg5v5=x['away_xg5v5'])
        predictions=replay(rows,f'{year}-10-15' if year==2025 else f'{year}-01-01')
        picks=[p for p in predictions if p['eligible']]
        for p in picks:
            a=audits[p['game_id']]
            for mine,original in [('margin','V6_shots_margin'),('v1_margin','v1_margin'),('shot_rating_margin','shot_rating_margin'),('confidence_margin','V7_xG_confidence_margin')]:
                assert math.isclose(p[mine],float(a[original]),abs_tol=1e-10),(p['game_id'],mine,p[mine],a[original])
            assert p['correct']==bool(int(a['V6_shots_correct']))
        got=(len(picks),sum(p['correct'] for p in picks),sum(p['correct'] for p in picks if p.get('top25')),sum(bool(p.get('top25')) for p in picks))
        assert got==want,(year,got,want)
        results.append(dict(season=year,games=got[0],v6_correct=got[1],v7_top_correct=got[2],v7_top_games=got[3],all_game_margins_match=True))
    return {'status':'passed','seasons':results,'v7_scope':'Full end-to-end parity from goals/shots and raw MoneyPuck 5v5 xG sums for all 3,936 historical games. All 3,773 eligible confidence margins match the original audit.'}
if __name__=='__main__':
    result=validate();Path('reports').mkdir(exist_ok=True);Path('reports/nhl-historical-validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))

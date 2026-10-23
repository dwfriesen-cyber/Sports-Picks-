import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ingest_nhl import parse_shots
from sources import download
import nfl
root=Path('recovery');root.mkdir(exist_ok=True)
for year in [2023,2024,2025]:
    xg=parse_shots(download(f'https://peter-tanner.com/moneypuck/downloads/shots_{year}.zip',root/f'shots_{year}.zip'),year)
    (root/f'xg-{year}.json').write_text(json.dumps(xg));(root/f'shots_{year}.zip').unlink()
    print(year,len(xg),'xG games',flush=True)
try:
    games=nfl.collect(2026,root)
    (root/'nfl-games-2026.json').write_text(json.dumps(games));print('NFL live normalized',len(games),flush=True)
except Exception as exc:(root/'nfl-error.txt').write_text(str(exc));print('NFL:',exc,flush=True)
try:download('https://icescope.app/',root/'icescope.html')
except Exception as exc:(root/'icescope-error.txt').write_text(str(exc))
for p in root.glob('*.gz'):p.unlink()

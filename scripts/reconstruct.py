"""Historical comparison without editing the imported published/shadow selections."""
import csv,datetime as dt,json,math,sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import replay

def stats(rows,key,rank_key):
    out={}
    for period,groups in [('daily',lambda p:p['date']),('weekly',lambda p:dt.date.fromisoformat(p['date']).strftime('%G-W%V')),('season_to_date_available_ledger',lambda p:'2026-27')]:
        grouped=defaultdict(list)
        for r in rows:grouped[groups(r)].append(r)
        out[period]={}
        for label,batch in grouped.items():
            graded=[r for r in batch if r.get('actual_winner') and r.get(key)]
            selected=[r for r in graded if r.get(rank_key) and r[rank_key]<=math.ceil(sum(p['date']==r['date'] and p.get(key) is not None for p in rows)/4)]
            wins=sum(r[key]==r['actual_winner'] for r in graded);tw=sum(r[key]==r['actual_winner'] for r in selected)
            out[period][label]={'wins':wins,'losses':len(graded)-wins,'games':len(graded),'accuracy':wins/len(graded) if graded else None,'top25_wins':tw,'top25_games':len(selected),'top25_accuracy':tw/len(selected) if selected else None}
    return out

def reconstruct(games,root='.'):
    root=Path(root);ledger=json.loads((root/'ledgers/historical/imported-chat-picks.json').read_text())
    picks=replay(games,'2026-10-18','2026-10-23');rows=[]
    for p in picks:
        d=ledger['days'][p['date']];r={k:p.get(k) for k in ['date','game_id','home','away','actual_winner']}
        r.update(v6_winner=p.get('winner'),v7a_rank=p.get('rank'),v7a_confidence=p.get('confidence'),v6_correct=p.get('correct'),prediction_kind='retrospective_reconstruction',published_winner=None,published_rank=None,v8_lite_winner=None,v8_lite_rank=None)
        for field,lkey in [('published','published'),('v8_lite','shadow')]:
            matches=[(i,t) for i,t in enumerate(d[lkey],1) if t in (p['home'],p['away'])]
            if len(matches)!=1:raise ValueError(f'Ledger matchup mismatch {p["game_id"]} {field}: {matches}')
            i,t=matches[0];r[field+'_winner']=t;r[field+'_rank']=i
            r[field+'_correct']=None if not p.get('actual_winner') else t==p['actual_winner']
        r['v6_v8_disagree']=r['v6_winner']!=r['v8_lite_winner'];rows.append(r)
    if len(rows)!=sum(len(d['published']) for d in ledger['days'].values()):raise ValueError('Comparison game coverage mismatch')
    summary={k:stats(rows,w,r) for k,w,r in [('v6_v7a','v6_winner','v7a_rank'),('published','published_winner','published_rank'),('v8_lite','v8_lite_winner','v8_lite_rank')]}
    disagreed=[r for r in rows if r['v6_v8_disagree'] and r['actual_winner']]
    summary['disagreements']={'graded':len(disagreed),'v6_wins':sum(r['v6_correct'] for r in disagreed),'v8_wins':sum(r['v8_lite_correct'] for r in disagreed)}
    summary['limitations']=['Reconstructed NHL inputs exclude the entire target date, matching original audit rules.','Historical source estimates downloaded now may contain revisions; point-in-time source availability is not provable.','Published and shadow lists are recovered transcripts with original message times; the import timestamp is separate.','October 23 games are pending until final; never graded as losses.','Season-to-date totals cover only recovered October 18–23 ledgers, not the entire season.']
    out=root/'reports';out.mkdir(exist_ok=True)
    (out/'oct18-23-comparison.json').write_text(json.dumps({'rows':rows,'summary':summary},indent=2))
    with (out/'oct18-23-comparison.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    lines=['# October 18–23 retrospective reconstruction','','V6 winners and V7-A ranks calculated now from prior-date games. Published and shadow choices remain unchanged. October 23 results pending.','','| Date | Away @ home | V6 | V7-A rank | Published | V8-lite | Result | V6 / Published / V8 |','|---|---|---|---:|---|---|---|---|']
    for r in rows:
        result=r['actual_winner'] or 'Pending'
        marks=' / '.join('—' if r[k] is None else '✓' if r[k] else '✗' for k in ['v6_correct','published_correct','v8_lite_correct'])
        lines.append(f"| {r['date']} | {r['away']} @ {r['home']} | {r['v6_winner']} | {r['v7a_rank']} | {r['published_winner']} | {r['v8_lite_winner']} | {result} | {marks} |")
    lines+=['','## Accuracy (completed games)','','| Model | Wins / games | Accuracy | Daily top quarter | Accuracy |','|---|---:|---:|---:|---:|']
    for k in ['v6_v7a','published','v8_lite']:
        s=summary[k]['season_to_date_available_ledger']['2026-27'];lines.append(f"| {k} | {s['wins']}/{s['games']} | {s['accuracy']:.1%} | {s['top25_wins']}/{s['top25_games']} | {s['top25_accuracy']:.1%} |")
    lines+=['','## Limits','']+['- '+v for v in summary['limitations']]
    (out/'oct18-23-comparison.md').write_text('\n'.join(lines)+'\n')
    return summary
if __name__=='__main__':print(json.dumps(reconstruct(json.loads(Path(sys.argv[1]).read_text())),indent=2))

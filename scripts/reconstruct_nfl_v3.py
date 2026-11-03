"""One predeclared reconstruction; no parameter search or production writes."""
import argparse,csv,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from research_v3.model import FEATURES,VERSION,feature_rows,fit,attach,summarize
from sources import download

UPSTREAM='5231fb4c22923a344504fefdfe4b1520714dd5db'


def execute(source_dir,output_dir):
    source_dir=Path(source_dir);out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    rows=[];sources=[]
    for year in range(2021,2026):
        path=source_dir/f'nfl-{year}.json'
        url=f'https://raw.githubusercontent.com/antonwilms/sleeper-dashboard-data/{UPSTREAM}/nflverse/teamcontext/{year}.json'
        if not path.exists(): download(url,path)
        raw=path.read_bytes();data=json.loads(raw)
        if data['season']!=year: raise ValueError('Wrong source year')
        rs=feature_rows(data)
        eligible=[r for r in rs if r['y'] is not None]
        expected={2021:(223,131),2022:(222,128),2023:(224,133),2024:(224,154),2025:(223,142)}
        actual=(len(eligible),sum((r['winner']==r['home'])==bool(r['y']) for r in eligible))
        assert actual==expected[year],(year,actual)
        sources.append(dict(year=year,url=url,sha256=hashlib.sha256(raw).hexdigest(),
            eligible=len(eligible),ties_excluded=len(rs)-len(eligible)))
        rows+=rs
    models={};audits=[];summaries={}
    for year in (2023,2024,2025,2026):
        train=[r for r in rows if r['season']<year and r['y'] is not None]
        m1,m2=fit(train,['v1_margin']),fit(train,FEATURES)
        models[str(year)]={'p1':m1,'p2':m2}
        if year==2026: continue
        audit=attach([r for r in rows if r['season']==year and r['y'] is not None],m1,m2)
        summary=summarize(audit);summaries[str(year)]=summary;audits+=audit
        for model,top in summary['top_quarter'].items():
            for week in top['weeks']:
                for r in audit:
                    if r['week']==week['week']:r[model+'_top25']=r['game_id'] in week['ids']
    summary=summarize(audits)
    assert summary['v1_wins']==429 and summary['n']==671
    fixed=attach([r for r in rows if r['season']==2025 and r['y'] is not None],models['2024']['p1'],models['2024']['p2'])
    import numpy,scipy,sklearn
    result=dict(model_version=VERSION,status='validated_reconstruction_not_original',
        protocol_sha256=hashlib.sha256(Path('research/NFL_V3_RECONSTRUCTION_PROTOCOL.md').read_bytes()).hexdigest(),
        runtime=dict(numpy=numpy.__version__,scipy=scipy.__version__,sklearn=sklearn.__version__),
        sources=sources,seasons=summaries,combined=summary,
        separate_fixed_2021_2023_parameters_on_2025=summarize(fixed),
        original_targets=dict(v3_top_wins=145,v1_top_wins=136,top_games=180,v2_wins=427,v2_top_wins=140),
        exact_original_reproduced=False,zero_rz_denominator_uses=sum(r['zero_rz_denominators'] for r in rows),
        recommendation='Keep research-only; do not replace original-V3 unavailable status. Require prospective shadow evidence before promotion.')
    (out/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
    (out/'coefficients.json').write_text(json.dumps(dict(model_version=VERSION,models=models),indent=2)+'\n')
    with (out/'game-audit.csv').open('w') as f:
        fields=['season','week','game_id','home','away','prior_home','prior_away','latest_input_week',
            *FEATURES,'y','winner','v2_winner','p1','p2','p3','v1_confidence','v2_confidence','v3_confidence',
            'v1_correct','v2_correct','v3_disagreement','raw_v1_top25','fitted_v1_top25','v2_top25','v3_top25']
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in audits:
            record=dict(r,**dict(zip(FEATURES,r['x'])))
            w.writerow({k:record[k] for k in fields})
    with (out/'paired-weeks.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(summary['paired_weeks'][0]));w.writeheader();w.writerows(summary['paired_weeks'])
    with (out/'calibration.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=['sample','model','lower','upper','n','predicted','observed']);w.writeheader()
        for label,s in [*summaries.items(),('combined',summary)]:
            for model,m in s['probability_metrics'].items():
                for b in m['calibration_bins']:w.writerow(dict(sample=label,model=model,**b))
    lines=['# NFL V3 Reconstruction — measured results','',
        '**Not verified original V3. Production NFL V1 and NHL are unchanged.**','',
        'One fixed, predeclared reconstruction; no evaluation-driven tuning. Details: [protocol](../../research/NFL_V3_RECONSTRUCTION_PROTOCOL.md).',
        'Coefficients/scaling: [coefficients.json](coefficients.json). Full [671-game audit](game-audit.csv), [paired weeks](paired-weeks.csv), [calibration bins](calibration.csv) and [validation JSON](validation.json).','',
        '| Season | V1 winners | V2 winners | Raw V1 top quarter | Fitted V1 top quarter | V2 top quarter | V3 top quarter |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for label,s in [*summaries.items(),('Combined',summary)]:
        values=[f"{s['v1_wins']}/{s['n']}",f"{s['v2_wins']}/{s['n']}"]
        values += [f"{s['top_quarter'][k]['wins']}/{s['top_quarter'][k]['games']}" for k in ('raw_v1','fitted_v1','v2','v3')]
        lines.append('| '+label+' | '+' | '.join(values)+' |')
    lines+=['','V3 preserves every V1 winner. Its overall winner accuracy is therefore identical to V1; confidence changes which games enter the top quarter. Fitted V1 uses probability assigned to the original V1 selection, not absolute distance from 0.5.','',
        '| Sample | Probability | Brier | Log loss | ECE (10 fixed bins) |','|---|---|---:|---:|---:|']
    for label,s in [*summaries.items(),('Combined',summary)]:
        for model,m in s['probability_metrics'].items():
            lines.append(f"| {label} | {model} | {m['brier']:.6f} | {m['log_loss']:.6f} | {m['ece']:.6f} |")
    top=summary['top_quarter']['v3'];paired=summary['paired_summary']['fitted_v1'];rawpaired=summary['paired_summary']['raw_v1']
    lines+=['','## Original result comparison','',
        f"Original reported V3: 145/180 (80.6%). Reconstruction: {top['wins']}/{top['games']} ({100*top['wins']/top['games']:.2f}%). Difference: {top['wins']-145:+d} wins.",
        f"Paired weekly comparison against fitted V1: {paired['improved']} improved, {paired['worsened']} worsened, {paired['unchanged']} unchanged; net {paired['net_wins']:+d} wins. Full membership changes are in paired-weeks.csv.",
        f"Against raw V1 (the original 136/180 baseline): {rawpaired['improved']} improved, {rawpaired['worsened']} worsened, {rawpaired['unchanged']} unchanged; net {rawpaired['net_wins']:+d} wins.",
        f"V2 does not reproduce exactly: {summary['v2_wins']}/671 versus original reported 427/671; reconstructed V2 top quarter {summary['top_quarter']['v2']['wins']}/180 versus reported 140/180. Thus the matching V3 aggregate is insufficient to claim the original implementation was recovered.",
        'The exact original feature algebra, scaling, regularization and recent decay are missing. These can change fitted probabilities and weekly ordering. Different historical source revisions may also matter. No saved original game-level probability audit exists to attribute the gap uniquely. Matching an aggregate would not establish restoration.',
        'The original 145/180 was chosen after examining several blend ratios. The reconstructed 50/50 ratio is fixed from that evidence, not reselected. The adopted expanding/refit protocol is distinct from the fixed 2021–23 parameters-on-2025 comparison recorded separately in validation.json.',
        '', '## Recommendation','',result['recommendation'],
        'The historical checks validate arithmetic, chronology and reproducibility; they do not establish a dependable future improvement. Keep the candidate explicitly labelled V3 Reconstruction. The prospective 2026 coefficients use 2021–25 only.',
        'Weekly pool generation is implemented separately and refuses late or incomplete slates. Rank 1 maps to N points by default; a supplied N-value pool scale is supported. No existing freeze or grading record is altered.',
        '', '## Limits','',
        '2023 coefficients use only 2021–22, but model structure was informed by original 2024 research. 2025 is excluded from its own fitting and no new tuning used it, but original 2025 research results were already examined. Future independent shadow weeks are needed. Historical data may include source revisions. Neutral-site games retain nominal home labels, as in the recovered data; no invented home-field overrides are applied.']
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({k:dict(n=v['n'],v1=v['v1_wins'],v2=v['v2_wins'],top={m:(t['wins'],t['games']) for m,t in v['top_quarter'].items()}) for k,v in [*summaries.items(),('combined',summary)]}))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--sources',default='data/v3-sources');p.add_argument('--output',default='reports/nfl-v3-reconstruction');a=p.parse_args()
    execute(a.sources,a.output)

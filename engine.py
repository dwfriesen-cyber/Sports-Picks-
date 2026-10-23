"""NHL V1/V6 research reconstruction; no market-derived selections."""
import csv,math,argparse,json
from collections import defaultdict

def clip(x): return max(-1.5,min(1.5,x))
def weight(n): return .8 if n<=10 else max(0,.8*(40-n)/30)
def expected(team,opp,h):
    a,b=h[team],h[opp]
    if min(len(a),len(b))<3:return None
    gf=sum(x[0] for x in a);sf=sum(x[2] for x in a)
    oga=sum(x[1] for x in b);osa=sum(x[3] for x in b)
    if sf<=0 or osa<=0:return None
    return .5*((oga/osa)*(sf/len(a))+(gf/sf)*(osa/len(b)))
def predict(game,h,r,xr=None):
    home,away=game['home'],game['away']
    eh,ea=expected(home,away,h),expected(away,home,h)
    if eh is None or ea is None:return dict(eligible=False,reason="Insufficient prior data")
    n=min(len(h[home]),len(h[away]));v1=eh-ea
    margin=(1-weight(n))*v1+weight(n)*1.5*(r[home]-r[away])
    if n<40:conf=abs(margin);status="early V6 ranking"
    elif xr is not None:conf=abs(.6*v1+.4*1.5*(xr[home]-xr[away]));status="V7-A xG ranking"
    else:conf=None;status="5v5 xG unavailable"
    return dict(eligible=True,winner=home if margin>0 else away,margin=round(margin,6),confidence=None if conf is None else round(conf,6),confidence_status=status,prior_games=n)
def replay(rows,target):
    hist=defaultdict(list);r=defaultdict(float);xr=defaultdict(float);out=[]
    for day in sorted({x['date'] for x in rows}):
        games=[x for x in rows if x['date']==day]
        if day>=target:
            picks=[dict(date=day,home=g['home'],away=g['away'],**predict(g,hist,r,xr if all(z.get('home_xg5v5') and z.get('away_xg5v5') for z in rows if z['date']<day) else None)) for g in games]
            eligible=sorted((p for p in picks if p['eligible'] and p['confidence'] is not None),key=lambda p:-p['confidence'])
            for i,p in enumerate(eligible):p.update(rank=i+1,top25=i<math.ceil(len(eligible)/4))
            out+=picks
        old=r.copy();oldx=xr.copy()
        for g in games:
            if any(not g.get(k) for k in ('home_goals','away_goals','home_shots','away_shots')):continue
            home,away=g['home'],g['away'];hs=float(g['home_shots']);ass=float(g['away_shots'])
            sig=clip((hs-ass)/30)
            r[home]=.8*old[home]+.2*(sig+old[away]);r[away]=.8*old[away]+.2*(-sig+old[home])
            if g.get('home_xg5v5') and g.get('away_xg5v5'):
                xs=clip((float(g['home_xg5v5'])-float(g['away_xg5v5']))/2)
                xr[home]=.8*oldx[home]+.2*(xs+oldx[away]);xr[away]=.8*oldx[away]+.2*(-xs+oldx[home])
            hg,ag=map(float,(g['home_goals'],g['away_goals']))
            hist[home].append((hg,ag,hs,ass));hist[away].append((ag,hg,ass,hs))
    return out
if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--games",required=True);ap.add_argument("--from-date",required=True);ap.add_argument("--output",default="predictions.json");args=ap.parse_args()
    with open(args.games,newline="") as f:rows=list(csv.DictReader(f))
    result=replay(rows,args.from_date)
    with open(args.output,"w") as f:json.dump(result,f,indent=2)
    print(json.dumps(dict(games=len(result),eligible=sum(p['eligible'] for p in result))))

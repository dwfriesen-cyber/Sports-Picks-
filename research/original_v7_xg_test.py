from pathlib import Path
import zipfile, pandas as pd, numpy as np
from collections import defaultdict
P=Path('/mnt/data/nhl_engine')
TEAM={'ANA':'Anaheim Ducks','BOS':'Boston Bruins','BUF':'Buffalo Sabres','CAR':'Carolina Hurricanes','CBJ':'Columbus Blue Jackets','CGY':'Calgary Flames','CHI':'Chicago Blackhawks','COL':'Colorado Avalanche','DAL':'Dallas Stars','DET':'Detroit Red Wings','EDM':'Edmonton Oilers','FLA':'Florida Panthers','LAK':'Los Angeles Kings','MIN':'Minnesota Wild','MTL':'Montreal Canadiens','NJD':'New Jersey Devils','NSH':'Nashville Predators','NYI':'New York Islanders','NYR':'New York Rangers','OTT':'Ottawa Senators','PHI':'Philadelphia Flyers','PIT':'Pittsburgh Penguins','SEA':'Seattle Kraken','SJS':'San Jose Sharks','STL':'St. Louis Blues','TBL':'Tampa Bay Lightning','TOR':'Toronto Maple Leafs','UTA':'Utah Mammoth','VAN':'Vancouver Canucks','VGK':'Vegas Golden Knights','WPG':'Winnipeg Jets','WSH':'Washington Capitals','ARI':'Arizona Coyotes'}
results=[];daily=[]; audit=[]; quality=[]
for y in [2023,2024,2025]:
 print('READ',y,flush=True)
 raw=pd.read_csv('/mnt/data/nhl_game_data_2023'+str(2024)+'.csv') if False else pd.read_csv(['/mnt/data/nhl_game_data_20232024.csv','/mnt/data/nhl_game_data_20242025.csv',str(P/'nhl_2025_26_games.csv')][y-2023]);raw['date']=pd.to_datetime(raw.game_date);raw=raw.sort_values(['date','game_id']);raw['short_id']=(raw.game_id.astype(int)%100000)
 with zipfile.ZipFile(f'/mnt/data/shots_{y}.zip') as z:
  chunks=[]
  with z.open(f'shots_{y}.csv') as f:
   for c in pd.read_csv(f,usecols=['game_id','isPlayoffGame','homeSkatersOnIce','awaySkatersOnIce','isHomeTeam','xGoal','teamCode','homeTeamCode','awayTeamCode'],chunksize=150000):
    c=c[(c.isPlayoffGame==0)&(c.homeSkatersOnIce==5)&(c.awaySkatersOnIce==5)&(c.game_id>=20001)&(c.game_id<=21312)]
    c=c.dropna(subset=['xGoal','isHomeTeam'])
    if len(c):chunks.append(c.groupby(['game_id','isHomeTeam']).agg(xg=('xGoal','sum'),n=('xGoal','size')))
  agg=pd.concat(chunks).groupby(level=[0,1]).sum().unstack(fill_value=0)
 xg={}
 for game in agg.index:
  try:xg[int(game)]=(float(agg.loc[game,('xg',1)]),float(agg.loc[game,('xg',0)]),int(agg.loc[game,('n',1)]+agg.loc[game,('n',0)]))
  except KeyError:pass
 print('xg games',len(xg),'matches',raw.short_id.isin(xg).sum(),flush=True)
 hist={};shotratings={};xgratings={};rows=[];missing=0
 for date,day in raw.groupby('date',sort=True):
  for g in day.itertuples():
   a,h=g.away_team,g.home_team
   if a not in hist or h not in hist:continue
   sa=np.asarray(hist[a]);sh=np.asarray(hist[h]);n=min(len(sa),len(sh))
   def predict(xs,ys):
    gf,ga,sf,saa=xs.sum(axis=0);ogf,oga,osf,osa=ys.sum(axis=0)
    return ((oga/osa)*(sf/len(xs))+(gf/sf)*(osa/len(ys)))/2 if sf>0 and osa>0 else np.nan
   ap=predict(sa,sh);hp=predict(sh,sa)
   if not np.isfinite(ap+hp):continue
   v1=hp-ap; sr=1.5*(shotratings.get(h,0)-shotratings.get(a,0));xr=1.5*(xgratings.get(h,0)-xgratings.get(a,0))
   early=.8 if n<=10 else 0 if n>=40 else .8*(40-n)/30
   vs={'V1':v1,'V6_shots':(1-early)*v1+early*sr,'V7_xG':(1-early)*v1+early*xr,'V7_xGshot_blend':(1-early)*v1+early*(.5*xr+.5*sr),'V7_xG20_post40':(1-(.2 if n>=40 else early))*v1+(.2 if n>=40 else early)*xr}
   item={'season':str(g.season),'date':date,'game_id':g.game_id,'home':h,'away':a,'n_prior':n,'v1_margin':v1,'shot_rating_margin':sr,'xg_rating_margin':xr,'actual_home_win':int(g.home_score>g.away_score)}
   for k,m in vs.items():item[k+'_margin']=m;item[k+'_correct']=int((m>0)==item['actual_home_win'])
   # V1/V6 winner, xg absolute margin solely used for rank after 40
   item['V7_xG_confidence_margin']= (1-(.4 if n>=40 else early))*v1+(.4 if n>=40 else early)*xr
   item['V7_xG_confidence_correct']=item['V1_correct'] if n>=40 else item['V6_shots_correct']
   rows.append(item)
  oldshot=shotratings.copy();oldxg=xgratings.copy();news={};newx={}
  for g in day.itertuples():
   a,h=g.away_team,g.home_team;rh=oldshot.get(h,0.);ra=oldshot.get(a,0.)
   signal=float(np.clip((g.home_shots-g.away_shots)/30,-1.5,1.5));news[h]=.8*rh+.2*(signal+ra);news[a]=.8*ra+.2*(-signal+rh)
   x=xg.get(int(g.short_id))
   if x:
    shx,sax,_=x;rxh=oldxg.get(h,0.);rxa=oldxg.get(a,0.)
    sig=float(np.clip((shx-sax)/2,-1.5,1.5));newx[h]=.8*rxh+.2*(sig+rxa);newx[a]=.8*rxa+.2*(-sig+rxh)
   else:missing+=1
   hist.setdefault(h,[]).append((g.home_score,g.away_score,g.home_shots,g.away_shots));hist.setdefault(a,[]).append((g.away_score,g.home_score,g.away_shots,g.home_shots))
  shotratings.update(news);xgratings.update(newx)
 d=pd.DataFrame(rows);d=d[d.n_prior>=3].copy()
 if y==2025:d=d[d.date>=pd.Timestamp('2025-10-15')].copy()
 audit.append(d)
 print('unmatched',missing,'prediction games',len(d),flush=True)
 for seg,sub in [('all',d),('under40',d[d.n_prior<40]),('40plus',d[d.n_prior>=40])]:
  for key in ['V1','V6_shots','V7_xG','V7_xGshot_blend','V7_xG20_post40']:
   results.append(dict(season=y,segment=seg,model=key,games=len(sub),correct=int(sub[key+'_correct'].sum()),accuracy=round(sub[key+'_correct'].mean()*100,3)))
 for date,group in d.groupby('date'):
  n=int(np.ceil(len(group)*.25))
  for k in ['V1','V6_shots','V7_xG','V7_xGshot_blend','V7_xG20_post40','V7_xG_confidence']:
   scorecol=k+'_margin' if k!='V7_xG_confidence' else 'V7_xG_confidence_margin'
   sel=group.assign(score=group[scorecol].abs()).sort_values(['score','home','away'],ascending=[False,True,True]).head(n)
   daily.append(dict(season=y,date=date,model=k,selected=n,correct=int(sel[k+'_correct'].sum())))
A=pd.concat(audit,ignore_index=True);R=pd.DataFrame(results);D=pd.DataFrame(daily)
A.to_csv(P/'v7_xg_game_audit.csv',index=False);R.to_csv(P/'v7_xg_comparison.csv',index=False);D.to_csv(P/'v7_xg_daily_top25.csv',index=False)
print(R.to_string(index=False));print(D.groupby(['season','model']).agg(picks=('selected','sum'),correct=('correct','sum')).assign(pct=lambda x=(None):0) if False else D.groupby(['season','model']).agg(picks=('selected','sum'),correct=('correct','sum')).to_string())

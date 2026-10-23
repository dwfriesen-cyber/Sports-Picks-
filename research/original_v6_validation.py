from pathlib import Path
import numpy as np,pandas as pd
P=Path(__file__).parent
files=[Path('/mnt/data/nhl_game_data_20232024.csv'),Path('/mnt/data/nhl_game_data_20242025.csv'),P/'nhl_2025_26_games.csv']
allrows=[];summary=[]; daily=[]
for path in files:
 raw=pd.read_csv(path);raw['date']=pd.to_datetime(raw.game_date);raw=raw.sort_values(['date','game_id']); season=str(raw.season.iloc[0]); hist={};rating={};rows=[]
 for date, day in raw.groupby('date',sort=True):
  for g in day.itertuples():
   a,h=g.away_team,g.home_team
   if a not in hist or h not in hist:continue
   sa=np.asarray(hist[a]);sh=np.asarray(hist[h]);n=min(len(sa),len(sh))
   def one(xs,ys):
    gf,ga,sf,saa=xs.sum(axis=0);ogf,oga,osf,osa=ys.sum(axis=0)
    return ((oga/osa)*(sf/len(xs))+(gf/sf)*(osa/len(ys)))/2 if sf>0 and osa>0 else np.nan
   ap=one(sa,sh);hp=one(sh,sa)
   if not np.isfinite(ap+hp):continue
   v1=hp-ap;rd=rating.get(h,0)-rating.get(a,0);rolling=1.5*rd
   early=.8 if n<=10 else 0 if n>=40 else .8*(40-n)/30
   variants={'V1':0,'V6_stop40':early,'V6_continue20':.2 if n>=40 else early,'V6_continue40':.4 if n>=40 else early,'V6_continue80':.8 if n>=40 else early,'V6_conf40_V1winner':.4 if n>=40 else early}
   item=dict(season=season,date=date,game_id=g.game_id,home=h,away=a,n_prior=n,home_score=g.home_score,away_score=g.away_score,v1_margin=v1,rolling=rolling)
   for key,w in variants.items():
    margin=v1 if key=='V6_conf40_V1winner' else (1-w)*v1+w*rolling
    item[key+'_margin']=margin
    item[key+'_correct']=int((margin>0)==(g.home_score>g.away_score))
   # confidence only uses margin hybrid ranking; retains V1 pick for 40+; for under 40 uses V6
   item['V6_conf40_V1winner_rank_margin']=(1-variants['V6_continue40'])*v1+variants['V6_continue40']*rolling
   item['V6_conf40_V1winner_correct']=item['V1_correct'] if n>=40 else item['V6_stop40_correct']
   rows.append(item)
  # update AFTER entire date
  prior=rating.copy(); updates={}
  for g in day.itertuples():
   a,h=g.away_team,g.home_team
   rh=prior.get(h,0.);ra=prior.get(a,0.)
   signal=float(np.clip((g.home_shots-g.away_shots)/30,-1.5,1.5))
   updates[h]=.8*rh+.2*(signal+ra);updates[a]=.8*ra+.2*(-signal+rh)
   hist.setdefault(h,[]).append((g.home_score,g.away_score,g.home_shots,g.away_shots))
   hist.setdefault(a,[]).append((g.away_score,g.home_score,g.away_shots,g.home_shots))
  rating.update(updates)
 d=pd.DataFrame(rows);d['season_day']=(d.date-d.date.min()).dt.days
 allrows.append(d)
 # exact 2025 published dataset evaluates October 15 onward: filter >= date 15 for consistent recheck
 if season=='20252026':
  d=d[d.date>=pd.Timestamp('2025-10-15')]
 for eligible,sub in [('all_predictable',d),('min3',d[d.n_prior>=3]),('under40',d[(d.n_prior<40)&(d.n_prior>=3)]),('40plus',d[d.n_prior>=40])]:
  for key in variants:
   summary.append(dict(season=season,segment=eligible,model=key,games=len(sub),correct=int(sub[key+'_correct'].sum()),accuracy_pct=round(100*sub[key+'_correct'].mean(),2) if len(sub) else None))
 for segment,sub in [('all_predictable',d),('min3',d[d.n_prior>=3]),('40plus_only',d[d.n_prior>=40])]:
  for day,g in sub.groupby('date'):
   k=int(np.ceil(len(g)*.25))
   for key in variants:
    rank_col= key+'_rank_margin' if key=='V6_conf40_V1winner' else key+'_margin'
    picks=g.assign(rankscore=g[rank_col].abs()).sort_values(['rankscore','away','home'],ascending=[False,True,True]).head(k)
    daily.append(dict(season=season,segment=segment,date=day,model=key,selected=k,correct=int(picks[key+'_correct'].sum())))
D=pd.concat(allrows); S=pd.DataFrame(summary);T=pd.DataFrame(daily)
D.to_csv(P/'hybrid_multiseason_game_audit.csv',index=False); S.to_csv(P/'hybrid_multiseason_results.csv',index=False);T.to_csv(P/'hybrid_multiseason_daily_top25.csv',index=False)
print('RESULTS min3 and 40plus');print(S[S.segment.isin(['min3','under40','40plus'])].to_string(index=False))
print('\nDAILY TOP25'); print(T[T.segment=='min3'].groupby(['season','model']).agg(picks=('selected','sum'),correct=('correct','sum')).assign(pct=lambda x:(100*x.correct/x.picks).round(2)).to_string())

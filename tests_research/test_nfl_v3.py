import copy,datetime as dt,json,math,tempfile,unittest
from pathlib import Path
from research_v3.model import FEATURES,attach,feature_rows,fit,probability,weekly_slate
from research_v3.weekly import generate


def source():
    teams={t:{'games':[]} for t in ('BUF','NYJ','KC','DEN')};schedule=[]
    for week in range(1,6):
        for home,away in [('BUF','NYJ'),('KC','DEN')]:
            gid=f'2026_{week:02}_{away}_{home}'
            h=20+week;a=17+week%2
            for team,opp,pf,pa in [(home,away,h,a),(away,home,a,h)]:
                teams[team]['games'].append(dict(week=week,seasonType='REG',gameId=gid,opponent=opp,
                    off=dict(pointsScored=pf,plays=60,epaSum=pf-20,epaPlays=60,successes=30,
                        successPlays=60,rzTrips=3,rzTdTrips=2),
                    **{'def':dict(pointsAllowed=pa,plays=60,epaSum=pa-20,epaPlays=60,
                        successes=28,successPlays=60,rzTripsAllowed=3,rzTdTripsAllowed=1)}))
            schedule.append(dict(game_id=gid,season=2026,week=week,home=home,away=away,
                home_score=h,away_score=a,start_time=f'2026-10-{week+1:02}T13:30:00+00:00'))
    return dict(season=2026,teams=teams),schedule


def models():
    return {key:dict(features=['v1_margin'],means=[0.],scales=[1.],coefficients=[coef],
         intercept=0.,training_seasons=[2021,2022,2023,2024,2025]) for key,coef in [('p1',.1),('p2',-.3)]}


class V3Tests(unittest.TestCase):
    def test_future_and_same_week_leakage(self):
        data,_=source();before=feature_rows(data);changed=copy.deepcopy(data)
        for team,entry in changed['teams'].items():
            for g in entry['games']:
                if g['week']>=4:
                    g['off']['epaSum']=9999
        after=feature_rows(changed)
        self.assertEqual([r['x'] for r in before if r['week']==4],[r['x'] for r in after if r['week']==4])
        self.assertTrue(all(r['latest_input_week']<r['week'] for r in after))

    def test_missing_feature_fails(self):
        d,_=source();d['teams']['BUF']['games'][0]['off']['epaSum']=None
        with self.assertRaises(ValueError):feature_rows(d)

    def test_ties_excluded_but_used_as_prior_games(self):
        d,_=source()
        for t in ['BUF','NYJ']:
            d['teams'][t]['games'][3]['off']['pointsScored']=20
            d['teams'][t]['games'][3]['def']['pointsAllowed']=20
        r=feature_rows(d)
        self.assertIsNone(next(x for x in r if x['week']==4 and x['home']=='BUF')['y'])
        self.assertEqual(next(x for x in r if x['week']==5 and x['home']=='BUF')['prior_home'],4)

    def test_disagreement_never_flips_winner(self):
        d,_=source();rows=feature_rows(d);m=models();r=attach(rows,m['p1'],m['p2'])
        self.assertEqual([x['winner'] for x in r],[x['winner'] for x in rows])
        for x in r:
            self.assertAlmostEqual(x['p3'],(x['p1']+x['p2'])/2)
            self.assertEqual(x['v3_disagreement'],x['v3_confidence']<.5)
        self.assertTrue(any(x['v3_disagreement'] for x in r))
        away=copy.deepcopy(rows[0]);away['winner']=away['away'];away['x'][0]=-3
        z=attach([away],m['p1'],m['p2'])[0]
        self.assertAlmostEqual(z['v3_confidence'],1-z['p3'])

    def test_fit_standardizes_training_only_and_serializes(self):
        rows=[dict(x=[float(i)]+[0.]*6,y=int(i%3==0),season=2021+i%2) for i in range(20)]
        m=fit(rows,['v1_margin']);self.assertAlmostEqual(m['means'][0],9.5)
        for row in rows:
            z=m['raw_intercept']+m['raw_coefficients'][0]*row['x'][0]
            self.assertAlmostEqual(probability(m,row),1/(1+math.exp(-z)))
        self.assertEqual(probability(m,rows[0]),probability(json.loads(json.dumps(m)),rows[0]))

    def test_training_season_leakage_rejected(self):
        d,_=source();m=models();m['p1']['training_seasons']=[2026]
        with self.assertRaises(ValueError):attach(feature_rows(d),m['p1'],m['p2'])

    def prepared(self):
        d,s=source()
        for entry in d['teams'].values():entry['games']=[g for g in entry['games'] if g['week']<4]
        s=[g for g in s if g['week']<=4]
        for g in s:
            if g['week']==4:g.update(home_score=None,away_score=None,start_time='2026-10-25T13:30:00+00:00')
        return d,s

    def test_weekly_pool_freeze_scale_and_immutable_retry(self):
        d,s=self.prepared();now=dt.datetime(2026,10,25,12,tzinfo=dt.timezone.utc)
        with tempfile.TemporaryDirectory() as temp:
            r=generate(d,s,4,models(),now,temp,[10,20]);path=Path(temp)/'frozen/2026-W04.json';saved=path.read_bytes()
            self.assertEqual([p['pool_points'] for p in r['picks']],[20,10])
            self.assertEqual(sum(p['top25'] for p in r['picks']),1)
            d['teams']['BUF']['games'][0]['off']['epaSum']=999
            later=generate(d,s,4,models(),now+dt.timedelta(days=2),temp)
            self.assertEqual(later,r);self.assertEqual(path.read_bytes(),saved)

    def test_international_kickoff_blocks_late_weekly_freeze(self):
        d,s=self.prepared()
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError,'earliest kickoff'):
                generate(d,s,4,models(),dt.datetime(2026,10,25,14,tzinfo=dt.timezone.utc),temp)
            self.assertFalse((Path(temp)/'frozen').exists())

    def test_partial_or_stale_prior_week_rejected(self):
        d,s=self.prepared();now=dt.datetime(2026,10,25,12,tzinfo=dt.timezone.utc)
        for mutation in ['missing','incomplete','score']:
            dd,ss=copy.deepcopy(d),copy.deepcopy(s)
            if mutation=='missing':
                for t in ['BUF','NYJ']:dd['teams'][t]['games']=dd['teams'][t]['games'][1:]
            elif mutation=='incomplete':ss[0]['home_score']=None
            else:ss[0]['home_score']+=1
            with tempfile.TemporaryDirectory() as temp:
                with self.assertRaises(ValueError):generate(dd,ss,4,models(),now,temp)

    def test_rank_ties_and_pool_scale_validation(self):
        d,s=self.prepared();fs=[g for g in s if g['week']==4]
        rs=attach([r for r in feature_rows(d,fs) if r['week']==4],models()['p1'],models()['p2'])
        for r in rs:r['v3_confidence']=.6
        now=dt.datetime(2026,10,25,12,tzinfo=dt.timezone.utc)
        result=weekly_slate(list(reversed(rs)),fs,now)
        self.assertEqual([r['game_id'] for r in result['picks']],sorted(r['game_id'] for r in rs))
        for scale in ([1,1],[1],[2,1],[1,float('nan')]):
            with self.assertRaises(ValueError):weekly_slate(rs,fs,now,scale)
        with self.assertRaises(ValueError):weekly_slate(rs[:1],fs,now)


if __name__=='__main__':unittest.main()

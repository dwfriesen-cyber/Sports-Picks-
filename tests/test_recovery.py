import copy,datetime as dt,json,tempfile,unittest
from collections import defaultdict
from pathlib import Path
from engine import predict,replay
from ingest_nhl import parse_day
from ledger import freeze,grade,append,digest
from nfl import expected as nfl_expected,parse_schedule,NFL_V3_BLOCKER
from scripts.validate_history import validate

class RecoveryTests(unittest.TestCase):
    def test_all_original_nhl_game_margins_and_rankings(self):
        self.assertEqual(validate()['status'],'passed')
    def test_v7_early_confidence_uses_xg_but_winner_stays_v6(self):
        h=defaultdict(list,{'A':[(3,2,30,20)]*3,'B':[(2,3,20,30)]*3})
        p=predict({'home':'A','away':'B'},h,defaultdict(float,{'A':1}),defaultdict(float,{'B':2}))
        self.assertEqual(p['winner'],'A');self.assertLess(p['confidence_margin'],0)
    def test_missing_xg_has_no_invented_confidence(self):
        h=defaultdict(list,{'A':[(0,2,30,20)]*3,'B':[(2,0,20,30)]*3})
        p=predict({'home':'A','away':'B'},h,defaultdict(float))
        self.assertTrue(p['eligible']);self.assertIsNone(p['confidence'])
    def test_same_date_and_future_outcomes_cannot_change_predictions(self):
        rows=json.loads(Path('research/nhl-2026-recovered-games.json').read_text())
        before=replay(rows,'2026-10-18','2026-10-18')
        changed=copy.deepcopy(rows)
        for r in changed:
            if r['date']>='2026-10-18':r.update(home_goals=99,away_goals=0,home_shots=99,away_shots=1,home_xg5v5=30,away_xg5v5=0)
        after=replay(changed,'2026-10-18','2026-10-18')
        self.assertEqual([(p['winner'],p['confidence'],p['rank']) for p in before],[(p['winner'],p['confidence'],p['rank']) for p in after])
    def test_zero_goal_final_is_not_skipped(self):
        rows=[dict(date=f'2026-10-0{i}',game_id=i,home='A',away='B',home_goals=0,away_goals=1,home_shots=20,away_shots=20,home_xg5v5=0,away_xg5v5=1) for i in range(1,5)]
        p=replay(rows,'2026-10-04')[0]
        self.assertEqual(p['prior_games'],3);self.assertIsNotNone(p['confidence'])
    def test_freeze_is_immutable_and_retries_reuse_original(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'f.json';now=dt.datetime(2026,10,23,12,tzinfo=dt.timezone.utc)
            picks=[{'game_id':'1','eligible':True,'start_time':'2026-10-24T00:00:00Z','winner':'A'}]
            first=freeze(p,picks,now,'inputs','code','nhl_v6_v7a')
            picks[0]['winner']='B'
            self.assertEqual(freeze(p,picks,now+dt.timedelta(hours=1),'new','new','nhl_v6_v7a'),first)
            with self.assertRaises(ValueError):append(p,{'altered':True})
    def test_late_freeze_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            now=dt.datetime(2026,10,23,12,tzinfo=dt.timezone.utc)
            with self.assertRaises(ValueError):freeze(Path(d)/'f.json',[{'eligible':True,'start_time':now.isoformat()}],now,'i','c','n')
    def test_partial_slate_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):freeze(Path(d)/'f.json',[{'eligible':False}],dt.datetime.now(dt.timezone.utc),'i','c','n')
    def test_grade_does_not_change_pick_and_corrections_are_append_only(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);now=dt.datetime(2026,10,23,12,tzinfo=dt.timezone.utc)
            p=root/'frozen/nhl/2026-10-23.json'
            freeze(p,[{'game_id':'1','winner':'A','eligible':True,'start_time':'2026-10-24T00:00:00Z','rank':1,'top25':True}],now,'i','c','nhl_v6_v7a')
            original=p.read_bytes();g={'game_id':'1','home':'A','away':'B','home_goals':1,'away_goals':2}
            self.assertFalse(grade(root,[g],now)[0]['correct'])
            grade(root,[g],now);self.assertEqual(len(list((root/'grading/nhl/1').glob('*.json'))),1)
            g.update(home_goals=3);grade(root,[g],now);self.assertEqual(len(list((root/'grading/nhl/1').glob('*.json'))),2)
            self.assertEqual(original,p.read_bytes())
    def test_nfl_v1_separate_points_plays_equation(self):
        h=defaultdict(list,{'A':[{'pf':30,'pa':20,'op':60,'dp':50}]*3,'B':[{'pf':20,'pa':30,'op':50,'dp':60}]*3})
        self.assertEqual(nfl_expected('A','B',h),30)
    def test_regina_no_dst_schedule(self):
        from zoneinfo import ZoneInfo
        for month in [1,7,10]:
            t=dt.datetime(2026,month,23,6,tzinfo=ZoneInfo('America/Regina'))
            self.assertEqual(t.astimezone(dt.timezone.utc).hour,12)
    def test_wrong_source_date_rejected(self):
        with self.assertRaises(ValueError):parse_day('2026-10-23',{'currentDate':'2026-10-22','games':[]},strict=True)
if __name__=='__main__':unittest.main()

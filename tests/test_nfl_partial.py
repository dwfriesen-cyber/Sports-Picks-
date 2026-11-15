import copy,csv,datetime as dt,gzip,io,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch

import nfl
from ledger import freeze,grade
from pipeline import run,preserved_nfl
from sources import SourceError

NOW=dt.datetime(2026,11,15,19,30,tzinfo=dt.timezone.utc)
FIELDS=['season','season_type','game_id','posteam','defteam','pass','rush','play_type',
        'two_point_attempt','total_home_score','total_away_score','desc']

def game(gid,date,week,home='DET',away='NE',home_score=35,away_score=10):
    return dict(game_id=gid,season=2026,week=week,date=date,start_time=date+'T14:30:00+00:00',
                home=home,away=away,home_score=home_score,away_score=away_score)

def plays(g,terminal=True):
    base=dict(season='2026',season_type='REG',game_id=g['game_id'],two_point_attempt='0',
              total_home_score=str(g['home_score']),total_away_score=str(g['away_score']))
    rows=[dict(base,posteam=g['home'],defteam=g['away'],**{'pass':'1','rush':'0'},play_type='pass',desc='Pass'),
          dict(base,posteam=g['away'],defteam=g['home'],**{'pass':'0','rush':'1'},play_type='run',desc='Run')]
    if terminal:rows.append(dict(base,posteam='',defteam='',**{'pass':'0','rush':'0'},play_type='',desc='END GAME'))
    return rows

def encoded(rows,fields=FIELDS):
    s=io.StringIO();w=csv.DictWriter(s,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
    return gzip.compress(s.getvalue().encode())

def saved(root,g,winner=None):
    return freeze(root/'frozen'/'nfl'/(g['date']+'.json'),
                  [dict(game_id=g['game_id'],date=g['date'],week=g['week'],home=g['home'],away=g['away'],
                        start_time=g['start_time'],winner=winner or g['home'],margin=2.5,eligible=True,
                        model_version='nfl-v1-original-20261016')],
                  dt.datetime(2026,11,1,tzinfo=dt.timezone.utc),'original-input','original-code','nfl_v1_only')

class PartialPlayDataTests(unittest.TestCase):
    def setUp(self):
        self.old=game('2026_09_NYJ_KC','2026-11-08',9,'KC','NYJ',35,12)
        self.missing=game('2026_10_NE_DET','2026-11-15',10)
        self.future=game('2026_10_LAC_BAL','2026-11-16',10,'BAL','LAC',None,None)
        self.schedule=[self.old,self.missing,self.future]

    def partial(self,rows,schedule=None):
        with self.assertRaises(nfl.IncompletePlayData) as caught:
            nfl.parse_pbp(encoded(rows),2026,schedule or self.schedule)
        return caught.exception

    def test_missing_game_keeps_other_validated_games_but_raises(self):
        before=copy.deepcopy(self.schedule);exc=self.partial(plays(self.old))
        self.assertEqual([g['game_id'] for g in exc.validated_games],[self.old['game_id'],self.future['game_id']])
        self.assertEqual(exc.blocked_games,[{'game_id':self.missing['game_id'],'reason':'Stale/incomplete NFL pbp scores'}])
        self.assertEqual(exc.schedule,before);self.assertEqual(self.schedule,before)

    def test_all_mismatched_or_missing_games_are_reported(self):
        bad=copy.deepcopy(self.old);bad['home_score']=1
        exc=self.partial(plays(bad))
        self.assertEqual([g['game_id'] for g in exc.blocked_games],[self.old['game_id'],self.missing['game_id']])
        self.assertEqual(exc.validated_games,[self.future])

    def test_matching_live_or_truncated_scores_are_not_final(self):
        exc=self.partial(plays(self.old)+plays(self.missing,terminal=False))
        self.assertIn('terminal END GAME row missing',exc.blocked_games[0]['reason'])
        self.assertNotIn(self.missing['game_id'],[g['game_id'] for g in exc.validated_games])

    def test_incomplete_schedule_score_is_quarantined(self):
        incomplete=dict(self.missing,away_score=None)
        exc=self.partial(plays(self.old),[self.old,incomplete,self.future])
        self.assertEqual(exc.blocked_games[0]['reason'],'Incomplete schedule score')

    def test_missing_countable_plays_are_quarantined(self):
        exc=self.partial(plays(self.old)+[plays(self.missing)[-1]])
        self.assertEqual(exc.blocked_games[0]['reason'],'Missing NFL play counts')

    def test_complete_zero_score_and_tie_finals_are_valid(self):
        for hs,aws in [(0,10),(27,27),(35,10)]:
            g=dict(self.missing,home_score=hs,away_score=aws)
            rows=nfl.parse_pbp(encoded(plays(g)),2026,[g,self.future])
            self.assertEqual(rows[0]['home_stats'],dict(pf=hs,pa=aws,op=1,dp=1))
            self.assertEqual(rows[1],self.future)

    def test_global_schema_season_and_team_errors_do_not_return_partial_data(self):
        rows=plays(self.old)
        cases=[encoded(rows,[f for f in FIELDS if f!='desc'])]
        wrong=copy.deepcopy(rows);wrong[0]['season']='2025';cases.append(encoded(wrong))
        wrong=copy.deepcopy(rows);wrong[0]['posteam']='UNKNOWN';cases.append(encoded(wrong))
        for data in cases:
            with self.assertRaises(SourceError) as caught:nfl.parse_pbp(data,2026,self.schedule)
            self.assertNotIsInstance(caught.exception,nfl.IncompletePlayData)

    def test_pipeline_keeps_original_freezes_and_grades_only_validated_games(self):
        exc=self.partial(plays(self.old))
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for g in self.schedule:saved(root,g)
            original={p:p.read_bytes() for p in (root/'frozen').rglob('*.json')}
            grade(root,exc.validated_games,NOW-dt.timedelta(hours=1))
            grade_before={p:p.read_bytes() for p in (root/'grading'/'nfl').rglob('*.json')}
            with patch('pipeline.nfl.collect',side_effect=exc),patch('pipeline.freeze_nfl',side_effect=AssertionError('New freeze attempted')) as make:
                report=run(root,root,now=NOW,nhl_games=[])
            make.assert_not_called()
            self.assertEqual(report['nfl']['v1_status'],'blocked')
            self.assertEqual(report['nfl']['source_status'],'blocked')
            self.assertEqual(report['nfl']['grading_status'],'partial')
            grading_inputs=json.loads((root/'inputs'/('nfl-grading-'+report['nfl']['grading_input_sha256']+'.json')).read_text())
            self.assertEqual(grading_inputs['purpose'],'grading_only')
            self.assertEqual(grading_inputs['validated_games'],exc.validated_games)
            self.assertEqual(report['nfl']['frozen_status'],'preserved')
            self.assertEqual(report['nfl']['v3_status'],'blocked')
            self.assertEqual(report['nfl']['v3_reason'],nfl.NFL_V3_BLOCKER)
            self.assertIsNone(report['nfl']['weekly_confidence_rankings'])
            self.assertEqual([s['picks'][0]['game_id'] for s in report['nfl']['slates']],
                             [self.missing['game_id'],self.future['game_id']])
            self.assertEqual([g['game_id'] for g in report['grading']],[self.old['game_id']])
            self.assertIn('nfl_v1_only',report['prospective_summary'])
            self.assertFalse((root/'grading'/'nfl'/self.missing['game_id']).exists())
            self.assertEqual(original,{p:p.read_bytes() for p in (root/'frozen').rglob('*.json')})
            self.assertEqual(grade_before,{p:p.read_bytes() for p in (root/'grading'/'nfl').rglob('*.json')})

            # Once upstream catches up, normal collection and grading resume. No
            # change to the original picks, forecast hashes, or old grade records.
            complete=nfl.parse_pbp(encoded(plays(self.old)+plays(self.missing)),2026,self.schedule)
            with patch('pipeline.nfl.collect',return_value=complete):
                recovered=run(root,root,now=NOW+dt.timedelta(minutes=1),nhl_games=[])
            self.assertEqual(recovered['nfl']['v1_status'],'frozen')
            self.assertEqual({g['game_id'] for g in recovered['grading']},{self.old['game_id'],self.missing['game_id']})
            self.assertEqual(original,{p:p.read_bytes() for p in (root/'frozen').rglob('*.json')})
            for p,b in grade_before.items():self.assertEqual(p.read_bytes(),b)

    def test_no_saved_slate_is_not_backfilled_on_partial_data(self):
        exc=self.partial(plays(self.old))
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with patch('pipeline.nfl.collect',side_effect=exc):report=run(root,root,now=NOW,nhl_games=[])
            self.assertEqual(report['nfl']['frozen_status'],'unavailable')
            self.assertEqual(report['nfl']['slates'],[])
            self.assertFalse((root/'frozen').exists())

    def test_saved_late_freeze_is_not_presented_as_valid(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);saved(root,self.missing)
            p=root/'frozen'/'nfl'/(self.missing['date']+'.json');s=json.loads(p.read_text())
            s['frozen_at']=NOW.isoformat();p.write_text(json.dumps(s))
            with self.assertRaisesRegex(ValueError,'before kickoff'):preserved_nfl(root,self.schedule,NOW)

    def test_january_slate_uses_season_game_identity_not_calendar_year(self):
        g=game('2026_18_NE_DET','2027-01-03',18,home_score=None,away_score=None)
        now=dt.datetime(2027,1,3,12,tzinfo=dt.timezone.utc)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);saved(root,g)
            r=preserved_nfl(root,[g],now)
            self.assertEqual(r['frozen_status'],'preserved')
            self.assertEqual(r['slates'][0]['picks'][0]['game_id'],g['game_id'])
            unrelated=dict(g,game_id='2026_18_DET_NE')
            self.assertEqual(preserved_nfl(root,[unrelated],now)['slates'],[])

if __name__=='__main__':unittest.main()

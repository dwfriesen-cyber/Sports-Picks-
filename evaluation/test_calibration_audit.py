import copy
import unittest
from calibration_audit import audit, records, digest, fit, predict

def fixture():
    files=[]
    for i in range(80):
        day=1+i//4
        date=f'2026-10-{day:02}'
        p=dict(game_id=str(i),date=date,home='H',away='A',winner='H',eligible=True,
               margin=(i%5+1)/10,model_version='nhl-v6-v7a-original-20261016',start_time=date+'T18:00:00Z')
        f=dict(kind='nhl_v6_v7a',frozen_at=date+'T12:00:00Z',picks=[p])
        g=dict(game_id=str(i),winner='H',actual_winner='H' if i%3 else 'A',correct=bool(i%3),
               model='nhl_v6_v7a',forecast_sha256=digest(f),graded_at=date+'T22:00:00Z')
        files.extend([dict(path=f'frozen/nhl/{i}.json',content=f),dict(path=f'grading/nhl/{i}.json',content=g)])
    return dict(ref='fixture-ref',files=files)

class CalibrationTests(unittest.TestCase):
    def test_grade_hash_rejected(self):
        b=fixture(); b['files'][1]['content']['forecast_sha256']='wrong'
        with self.assertRaises(ValueError):records(b)
    def test_late_freeze_rejected(self):
        b=fixture(); b['files'][0]['content']['frozen_at']='2026-10-01T19:00:00Z'
        with self.assertRaises(ValueError):records(b)
    def test_duplicate_grade_rejected(self):
        b=fixture(); b['files'].append(copy.deepcopy(b['files'][1]))
        with self.assertRaises(ValueError):records(b)
    def test_grade_before_game_rejected(self):
        b=fixture(); b['files'][1]['content']['graded_at']='2026-10-01T11:00:00Z'
        with self.assertRaises(ValueError):records(b)
    def test_future_labels_do_not_change_prior_predictions(self):
        b=fixture(); first=audit(b)
        changed=copy.deepcopy(b)
        for f in changed['files']:
            if f['path'].startswith('grading') and int(f['content']['game_id'])>=60:
                g=f['content'];g['correct']=not g['correct'];g['actual_winner']='H' if g['correct'] else 'A'
        second=audit(changed)
        a=[r['probability'] for r in first['predictions'] if int(r['game_id'])<60]
        z=[r['probability'] for r in second['predictions'] if int(r['game_id'])<60]
        self.assertEqual(a,z)
    def test_same_day_results_excluded(self):
        result=audit(fixture())
        for r in result['predictions']:
            self.assertLess(r['latest_training_grade'],r['original_frozen_at'])
        self.assertEqual(result['predictions'][0]['train_n'],52)
    def test_no_fake_value_or_ticket(self):
        result=audit(fixture())
        self.assertEqual(result['value_evaluation'],'BLOCKED')
        self.assertTrue(all(r['research_only'] for r in result['predictions']))
        self.assertNotIn('ticket',result)
    def test_probabilities_bounded_deterministic(self):
        rows=[dict(feature=i/100,correct=i%2) for i in range(70)]
        m=fit(rows);self.assertEqual(m,fit(rows))
        self.assertTrue(all(0<predict(m,x)<1 for x in [-100,0,100]))
    def test_no_source_mutation(self):
        b=fixture();before=copy.deepcopy(b);audit(b);self.assertEqual(before,b)

if __name__=='__main__':unittest.main()

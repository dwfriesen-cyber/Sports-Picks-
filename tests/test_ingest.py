import unittest
from ingest_nhl import parse_day
class IngestTests(unittest.TestCase):
 def test_regular_final_only(self):
  g={"id":2026020001,"gameType":2,"gameState":"OFF","gameDate":"2026-10-08","homeTeam":{"abbrev":"MTL","score":3,"sog":31},"awayTeam":{"abbrev":"TOR","score":2,"sog":25}}
  self.assertEqual(parse_day("2026-10-08",{"games":[g]})[0]["home_shots"],31)
 def test_preseason_excluded(self):
  g={"id":1,"gameType":1,"gameState":"OFF","homeTeam":{},"awayTeam":{}}
  self.assertEqual(parse_day("2026-10-08",{"games":[g]}),[])
 def test_missing_shots_fail_closed(self):
  g={"id":1,"gameType":2,"gameState":"OFF","homeTeam":{"abbrev":"MTL","score":3},"awayTeam":{"abbrev":"TOR","score":2,"sog":20}}
  with self.assertRaises(ValueError):parse_day("2026-10-08",{"games":[g]})

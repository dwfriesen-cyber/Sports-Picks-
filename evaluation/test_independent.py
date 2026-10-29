"""Unittest coverage for isolated evaluator. Run: python -m unittest discover -s evaluation -v"""
import json
import tempfile
import unittest
from pathlib import Path
from independent import freeze_rows, compare, assess_singles, grade_tickets


class IndependentEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.pick = {"game_id": "G1", "date": "2026-10-28", "home": "WSH", "away": "PHI",
                     "winner": "WSH", "eligible": True, "start_time": "2026-10-28T23:30:00Z",
                     "rank": 1, "confidence": 0.66}
        self.freeze = {"kind": "nhl_v6_v7a", "frozen_at": "2026-10-28T17:21:48Z",
                       "picks": [self.pick]}
        self.path = self.root / "frozen.json"
        self.path.write_text(json.dumps(self.freeze))
        self.quote = {"quote_id": "q1", "game_id": "G1", "book": "ExampleBook",
                      "market": "full_game_moneyline", "selection": "WSH",
                      "decimal_odds": 1.5, "observed_at": "2026-10-28T18:00:00Z",
                      "source_url": "https://example.com/receipt", "status": "observed",
                      "executable": True}

    def test_freeze_and_matched_comparison(self):
        self.assertEqual(freeze_rows(self.path)[0]["winner"], "WSH")
        other = dict(self.freeze, kind="nhl_v8_lite",
                     picks=[dict(self.pick, winner="PHI")])
        path2 = self.root / "shadow.json"
        path2.write_text(json.dumps(other))
        out = compare([self.path, path2], [{"game_id": "G1", "winner": "WSH"}])
        self.assertEqual(out["models"]["nhl_v6_v7a"]["matched_correct"], 1)
        self.assertEqual(out["models"]["nhl_v8_lite"]["matched_correct"], 0)
        self.assertEqual(len(out["disagreements"]), 1)

    def test_post_start_freeze_rejected(self):
        self.freeze["frozen_at"] = "2026-10-29T00:00:00Z"
        self.path.write_text(json.dumps(self.freeze))
        with self.assertRaises(ValueError):
            freeze_rows(self.path)

    def test_single_profit_and_missing_quote(self):
        out = assess_singles(freeze_rows(self.path), [self.quote], [{"game_id": "G1", "winner": "WSH"}])
        self.assertEqual((out["wins"], out["net"]), (1, 1.0))
        no = assess_singles(freeze_rows(self.path), [], [{"game_id": "G1", "winner": "WSH"}])
        self.assertEqual(no["eligible"], 0)
        self.assertIsNone(no["roi"])

    def test_stale_and_nonexecutable_quotes_excluded(self):
        stale = dict(self.quote, observed_at="2026-10-28T16:00:00Z")
        fake = dict(self.quote, executable=False)
        self.assertEqual(assess_singles(freeze_rows(self.path), [stale, fake],
                         [{"game_id": "G1", "winner": "WSH"}])["eligible"], 0)

    def test_ticket_versions_and_pending_exclusion(self):
        q2 = dict(self.quote, quote_id="q2", game_id="G2", selection="TOR")
        legs = [
            {"game_id": "G1", "home": "WSH", "away": "PHI", "selection": "WSH",
             "quote_id": "q1", "start_time": self.pick["start_time"]},
            {"game_id": "G2", "home": "TOR", "away": "SEA", "selection": "TOR",
             "quote_id": "q2", "start_time": self.pick["start_time"]}
        ]
        t = {"date": "2026-10-28", "version": 2, "status": "active", "stake": 2,
             "published_at": "2026-10-28T18:30:00Z", "legs": legs}
        old = dict(t, version=1, status="superseded")
        results = grade_tickets([old, t], [self.quote, q2],
                                [{"game_id": "G1", "winner": "WSH"}, {"game_id": "G2", "winner": "SEA"}])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["net"], -2)
        with self.assertRaises(ValueError):
            grade_tickets([t], [self.quote, q2], [], ["G2"])


if __name__ == "__main__":
    unittest.main()

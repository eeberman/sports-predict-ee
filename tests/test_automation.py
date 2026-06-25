from __future__ import annotations

import unittest

from automation.odds import market_book_from_events
from automation.resolver import resolve_questions


def question(number, text, family, subtype, target=None, threshold=None, time_scope="regulation"):
    return {
        "number": number,
        "question": text,
        "normalized": {
            "question_family": family,
            "question_subtype": subtype,
            "target_team_or_side": target,
            "threshold_value": threshold,
            "time_scope": time_scope,
            "home_team": "Czechia",
            "away_team": "Mexico",
            "raw_question": text,
        },
    }


class AutomationResolverTests(unittest.TestCase):
    def book(self):
        event = {
            "home_team": "Czechia",
            "away_team": "Mexico",
            "bookmakers": [
                {
                    "key": "fanduel",
                    "markets": [
                        {
                            "key": "h2h",
                            "outcomes": [
                                {"name": "Czechia", "price": 4.59},
                                {"name": "Draw", "price": 4.19},
                                {"name": "Mexico", "price": 1.763},
                            ],
                        },
                        {
                            "key": "btts",
                            "outcomes": [
                                {"name": "Yes", "price": 1.91},
                                {"name": "No", "price": 1.86},
                            ],
                        },
                        {
                            "key": "team_totals",
                            "outcomes": [
                                {"name": "Over", "description": "Czechia", "point": 0.5, "price": 1.65},
                                {"name": "Under", "description": "Czechia", "point": 0.5, "price": 2.25},
                            ],
                        },
                        {
                            "key": "player_shots_on_target",
                            "outcomes": [
                                {"name": "Over", "description": "Adam Hlozek", "point": 0.5, "price": 2.85}
                            ],
                        },
                    ],
                },
                {
                    "key": "draftkings",
                    "markets": [
                        {
                            "key": "h2h",
                            "outcomes": [
                                {"name": "Czechia", "price": 4.6},
                                {"name": "Draw", "price": 4.2},
                                {"name": "Mexico", "price": 1.76},
                            ],
                        }
                    ],
                },
            ],
        }
        return market_book_from_events([event], "Czechia", "Mexico")

    def test_h2h_uses_direct_de_vig(self):
        decisions = resolve_questions(
            [question(1, "Will Czechia win the match?", "match_result", "team_win", "home")],
            self.book(),
        )
        self.assertEqual(decisions[0].source_tier, "Direct")
        self.assertGreater(decisions[0].prob, 15)
        self.assertLess(decisions[0].prob, 25)

    def test_btts_and_over_is_derived(self):
        decisions = resolve_questions(
            [question(1, "Will both teams score AND the match have 3 or more total goals?", "goals_totals", "btts_and_over", "both", 3)],
            self.book(),
        )
        self.assertEqual(decisions[0].source_tier, "Derived")
        self.assertGreater(decisions[0].prob, 35)
        self.assertLess(decisions[0].prob, 45)

    def test_missing_player_sot_is_15_percent_fallback(self):
        decisions = resolve_questions(
            [question(1, "Will Patrik Schick have at least 1 shot on target?", "player_markets", "player_shot_on_target")],
            self.book(),
        )
        self.assertEqual(decisions[0].source_tier, "Fallback")
        self.assertEqual(decisions[0].prob, 15)

    def test_one_sided_player_sot_haircut(self):
        decisions = resolve_questions(
            [question(1, "Will Adam Hlozek have at least 1 shot on target?", "player_markets", "player_shot_on_target")],
            self.book(),
        )
        self.assertEqual(decisions[0].source_tier, "Direct")
        self.assertEqual(decisions[0].prob, 31)

    def test_fouls_and_offsides_stay_away(self):
        decisions = resolve_questions(
            [
                question(1, "Will Czechia commit more fouls than Mexico?", "fouls", "fouls_comparison", "both"),
                question(2, "Will Mexico be caught offside 2 or more times?", "offsides", "team_offsides", "away", 2),
            ],
            self.book(),
        )
        self.assertEqual(decisions[0].source_tier, "STAY AWAY")
        self.assertEqual(decisions[1].source_tier, "STAY AWAY")

    def test_disappeared_line_becomes_review(self):
        previous = {
            "snapshot_time": "2026-06-24T23:45:00+00:00",
            "decisions": [
                {
                    "question": "Will Czechia win the match?",
                    "prob": 21,
                    "source_tier": "Direct",
                    "derivation": "prior h2h",
                    "signature": "h2h",
                }
            ],
        }
        empty_book = market_book_from_events([], "Czechia", "Mexico")
        decisions = resolve_questions(
            [question(1, "Will Czechia win the match?", "match_result", "team_win", "home")],
            empty_book,
            previous,
        )
        self.assertEqual(decisions[0].source_tier, "REVIEW")
        self.assertEqual(decisions[0].prob, 21)
        self.assertIn("LINE DISAPPEARED", decisions[0].derivation)


if __name__ == "__main__":
    unittest.main()


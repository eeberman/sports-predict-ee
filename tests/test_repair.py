import os
import unittest
from unittest.mock import patch

from raw_landing import config, r2
from raw_landing.reconcile import _source_url
from raw_landing.repair import build_plan
from raw_landing.sources.football_data_co_uk import LEAGUES, SEASONS


class RepairTests(unittest.TestCase):
    def test_endpoint_removes_dashboard_bucket_path(self):
        with patch.dict(os.environ, {"s3_api": "https://account.r2.cloudflarestorage.com/bucket"}, clear=False):
            self.assertEqual(r2.endpoint_url(), "https://account.r2.cloudflarestorage.com")

    @patch("raw_landing.repair._statsbomb_match_ids", return_value={"1", "2"})
    @patch("raw_landing.repair._filenames")
    def test_plan_contains_only_logical_gaps(self, filenames, _match_ids):
        all_football = {
            f"{label}_{season}.csv" for label in LEAGUES for season in SEASONS
        }
        all_football.remove("greece_G1_2425.csv")

        def values(prefix):
            if prefix == "raw/football_data_co_uk/csv/":
                return all_football
            if prefix == "raw/statsbomb_open_data/events/":
                return {"1.json"}
            if prefix == "raw/statsbomb_open_data/lineups/":
                return set()
            raise AssertionError(prefix)

        filenames.side_effect = values
        targets = build_plan()
        self.assertEqual(sum(t.source_name == "football_data_co_uk" for t in targets), 1)
        self.assertEqual(sum(t.entity_name == "events" for t in targets), 1)
        self.assertEqual(sum(t.entity_name == "lineups" for t in targets), 2)

    def test_reconciled_source_urls_are_inferable(self):
        football_key = "raw/football_data_co_uk/csv/ingested_date=2026-06-21/run_id=x/greece_G1_2425.csv"
        lineup_key = "raw/statsbomb_open_data/lineups/ingested_date=2026-06-21/run_id=x/3893833.json"
        self.assertEqual(
            _source_url("football_data_co_uk", "csv", football_key),
            "https://www.football-data.co.uk/mmz4281/2425/G1.csv",
        )
        self.assertTrue(_source_url("statsbomb_open_data", "lineups", lineup_key).endswith("/lineups/3893833.json"))


if __name__ == "__main__":
    unittest.main()

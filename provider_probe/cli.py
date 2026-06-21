"""
CLI entry point for the provider qualification probe.

Usage:
  python -m provider_probe.cli check-config
  python -m provider_probe.cli summarize-taxonomy [--taxonomy PATH]
  python -m provider_probe.cli probe-odds [--taxonomy PATH]
  python -m provider_probe.cli probe-football [--taxonomy PATH]
  python -m provider_probe.cli probe-lineups [--taxonomy PATH]
  python -m provider_probe.cli probe-weather [--taxonomy PATH]
  python -m provider_probe.cli probe-referees [--taxonomy PATH]
  python -m provider_probe.cli run-all [--taxonomy PATH]
  python -m provider_probe.cli build-report [--taxonomy PATH]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import config
from .probes import ProbeResult


# ---------------------------------------------------------------------------
# Individual commands
# ---------------------------------------------------------------------------

def cmd_check_config(_args) -> None:
    print("Checking environment configuration (values never shown):")
    keys = [
        "SPORTSPREDICT_API_KEY",
        "ODDS_API_KEY",
        "ODDS_PROVIDER",
        "FOOTBALL_DATA_PROVIDER",
        "FOOTBALL_DATA_API_KEY",
        "WEATHER_PROVIDER",
        "SPORTMONKS_API_KEY",
        "REFEREE_DATA_PROVIDER",
    ]
    for k in keys:
        config.key_present(k)


def cmd_summarize_taxonomy(args) -> None:
    from .taxonomy import load_taxonomy, print_summary
    df = load_taxonomy(args.taxonomy)
    print_summary(df)


def cmd_probe_odds(args) -> None:
    from .probes.odds_probe import run
    print("\n=== Probing: The Odds API ===")
    result = run()
    _print_result(result)
    _save_results([result], args)


def cmd_probe_football(args) -> None:
    from .probes.football_probe import run
    print("\n=== Probing: API-Football (match stats) ===")
    result = run()
    _print_result(result)
    _save_results([result], args)


def cmd_probe_lineups(args) -> None:
    from .probes.lineups_probe import run
    print("\n=== Probing: API-Football (lineups) ===")
    result = run()
    _print_result(result)
    _save_results([result], args)


def cmd_probe_weather(args) -> None:
    from .probes.weather_probe import run
    print("\n=== Probing: Open-Meteo (weather) ===")
    result = run()
    _print_result(result)
    _save_results([result], args)


def cmd_probe_referees(args) -> None:
    from .probes.referee_probe import run
    print("\n=== Probing: API-Football (referee data) ===")
    result = run()
    _print_result(result)
    _save_results([result], args)


def cmd_probe_referee_sources(args) -> None:
    from .probes.referee_source_probe import run
    print("\n=== Probing: Referee source qualification ===")
    rows, _report = run(args.taxonomy)
    print(f"\n  {len(rows)} sources assessed:")
    for r in rows:
        print(f"  {r['source_name']:20s}  {r['test_status']:12s}  {r['recommendation']}")


def cmd_run_all(args) -> None:
    from .probes.odds_probe import run as run_odds
    from .probes.football_probe import run as run_football
    from .probes.lineups_probe import run as run_lineups
    from .probes.weather_probe import run as run_weather
    from .probes.referee_probe import run as run_referee
    from .reports import build_all_reports

    results: list[ProbeResult] = []

    from .probes.referee_source_probe import run as run_ref_sources

    for label, runner in [
        ("The Odds API", run_odds),
        ("API-Football (match stats)", run_football),
        ("API-Football (lineups)", run_lineups),
        ("Open-Meteo (weather)", run_weather),
        ("API-Football (referee)", run_referee),
    ]:
        print(f"\n=== Probing: {label} ===")
        try:
            r = runner()
        except Exception as exc:
            print(f"  ERROR: {exc}")
            r = ProbeResult(
                provider=label.lower().replace(" ", "_"),
                data_area="unknown",
                status="error",
                api_key_present=False,
                notes=str(exc),
            )
        results.append(r)
        _print_result(r)

    # Referee source qualification (writes its own output files)
    print("\n=== Probing: Referee source qualification ===")
    try:
        ref_rows, _ = run_ref_sources(args.taxonomy)
        print(f"  {len(ref_rows)} sources assessed")
    except Exception as exc:
        print(f"  ERROR: {exc}")

    print("\n=== Building reports ===")
    build_all_reports(results, args.taxonomy)

    print("\n=== Run-all summary ===")
    for r in results:
        print(f"  {r.provider}/{r.data_area}: {r.status} | found={len(r.fields_found)} missing={len(r.fields_missing)}")


def cmd_build_report(args) -> None:
    # Load previously saved probe results if available
    results_path = config.OUTPUTS / "probe_results.json"
    if results_path.exists():
        raw = json.loads(results_path.read_text(encoding="utf-8"))
        results = [ProbeResult(**r) for r in raw]
        print(f"Loaded {len(results)} probe results from {results_path}")
    else:
        print("No saved probe results found. Run 'run-all' first, or running with empty results.")
        results = []

    from .reports import build_all_reports
    build_all_reports(results, args.taxonomy)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_print(text: str) -> str:
    """Encode to ASCII replacing non-ASCII so Windows console doesn't raise."""
    return text.encode("ascii", errors="replace").decode("ascii")


def _print_result(r: ProbeResult) -> None:
    print(f"\n  Status       : {r.status}")
    print(f"  Key present  : {r.api_key_present}")
    print(f"  Fields found : {r.fields_found}")
    print(f"  Fields missing: {r.fields_missing}")
    print(f"  Notes        : {_safe_print(r.notes[:300])}")
    if r.raw_sample_path:
        print(f"  Raw sample   : {r.raw_sample_path}")


def _save_results(results: list[ProbeResult], _args) -> None:
    config.OUTPUTS.mkdir(parents=True, exist_ok=True)
    path = config.OUTPUTS / "probe_results.json"
    existing: list[dict] = []
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            existing = []

    # Merge: replace any existing result with same provider+data_area
    existing_map = {(r["provider"], r["data_area"]): r for r in existing}
    for r in results:
        import dataclasses
        existing_map[(r.provider, r.data_area)] = dataclasses.asdict(r)

    path.write_text(
        json.dumps(list(existing_map.values()), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# CLI wiring
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m provider_probe.cli",
        description="SportsPredict data provider qualification probe",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def _add_taxonomy(p):
        p.add_argument("--taxonomy", default=None, type=Path,
                       help="Path to question_templates.csv (default: data/processed/question_templates.csv)")

    sub.add_parser("check-config", help="Show which API keys are present/missing")

    p = sub.add_parser("summarize-taxonomy", help="Print taxonomy summary")
    _add_taxonomy(p)

    p = sub.add_parser("probe-odds", help="Probe The Odds API")
    _add_taxonomy(p)

    p = sub.add_parser("probe-football", help="Probe API-Football for match stats")
    _add_taxonomy(p)

    p = sub.add_parser("probe-lineups", help="Probe API-Football for lineup data")
    _add_taxonomy(p)

    p = sub.add_parser("probe-weather", help="Probe Open-Meteo for weather data")
    _add_taxonomy(p)

    p = sub.add_parser("probe-referees", help="Probe API-Football for referee data")
    _add_taxonomy(p)

    p = sub.add_parser("probe-referee-sources", help="Qualify free referee stat sources (StatBunker etc.)")
    _add_taxonomy(p)

    p = sub.add_parser("run-all", help="Run all probes then build reports")
    _add_taxonomy(p)

    p = sub.add_parser("build-report", help="Build report files from saved probe results")
    _add_taxonomy(p)

    args = parser.parse_args(argv)
    dispatch = {
        "check-config": cmd_check_config,
        "summarize-taxonomy": cmd_summarize_taxonomy,
        "probe-odds": cmd_probe_odds,
        "probe-football": cmd_probe_football,
        "probe-lineups": cmd_probe_lineups,
        "probe-weather": cmd_probe_weather,
        "probe-referees": cmd_probe_referees,
        "probe-referee-sources": cmd_probe_referee_sources,
        "run-all": cmd_run_all,
        "build-report": cmd_build_report,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()

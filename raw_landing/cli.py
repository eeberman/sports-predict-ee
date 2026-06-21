"""
CLI entry point for raw data landing.

Usage:
  python -m raw_landing.cli check-config
  python -m raw_landing.cli test-r2
  python -m raw_landing.cli pull-sportspredict [--dry-run]
  python -m raw_landing.cli pull-football-data [--seasons 5] [--dry-run]
  python -m raw_landing.cli pull-statsbomb [--cycles 2] [--dry-run]
  python -m raw_landing.cli pull-statbunker [--dry-run]
  python -m raw_landing.cli pull-all-no-quota [--dry-run]
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from . import config, r2
from .manifest import load as load_manifest


# ---------------------------------------------------------------------------
# Logging setup (tee to file + stdout)
# ---------------------------------------------------------------------------

def _setup_logging(run_id: str) -> logging.Logger:
    config.LOGS.mkdir(parents=True, exist_ok=True)
    config.SAMPLES.mkdir(parents=True, exist_ok=True)
    log_path = config.LOGS / f"{run_id}.log"
    logger = logging.getLogger(f"raw_landing.{run_id}")
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    return logger


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------

def _write_report(run_id: str, sources_run: list[str], dry_run: bool) -> None:
    df = load_manifest()
    config.OUTPUTS.mkdir(parents=True, exist_ok=True)
    path = config.OUTPUTS / "raw_landing_report.md"

    lines = [
        "# Raw Landing Report",
        f"\n**Generated:** {datetime.now(timezone.utc).isoformat()}",
        f"**Last run_id:** `{run_id}`",
        f"**Mode:** {'DRY-RUN' if dry_run else 'LIVE'}",
        "\n---\n",
        "## Sources Attempted\n",
    ]
    for s in sources_run:
        lines.append(f"- {s}")

    if not df.empty:
        lines += ["\n## Files by Source / Entity\n",
                  "| source | entity | uploaded | skipped | error |",
                  "|---|---|---|---|---|"]
        for (src, ent), grp in df.groupby(["source_name", "entity_name"]):
            u = (grp["status"] == "uploaded").sum()
            sk = (grp["status"] == "skipped").sum()
            e = (grp["status"] == "error").sum()
            lines.append(f"| {src} | {ent} | {u} | {sk} | {e} |")

        total_bytes = df.loc[df["status"] == "uploaded", "bytes_uploaded"].apply(
            lambda x: int(x) if str(x).isdigit() else 0
        ).sum()
        lines += [
            f"\n**Total uploaded:** {df[df['status']=='uploaded'].shape[0]} files",
            f"**Total bytes to R2:** {total_bytes:,}",
            f"**Manifest rows:** {len(df)}",
        ]

        lines += ["\n## R2 Prefixes Written\n"]
        prefixes: set[str] = set()
        for key in df.loc[df["status"] == "uploaded", "r2_key"].dropna():
            parts = str(key).split("/")
            if len(parts) >= 3:
                prefixes.add("/".join(parts[:3]))
        for p in sorted(prefixes):
            lines.append(f"- `{p}/`")

    lines += [
        "\n## Quota-Limited Sources Excluded\n",
        "- API-Football: excluded (no historical pulls in this task)",
        "- The Odds API: excluded (no historical pulls in this task)",
        "\n## Local Disk Usage\n",
        "Raw data is stored in R2 only. Local files: `.env`, `raw_manifest.csv`, `outputs/logs/`.",
        "\n## Next Recommended Step\n",
        "1. Verify R2 bucket contents via Cloudflare dashboard",
        "2. Add international StatBunker comp_ids (see `outputs/statbunker_manual_todo.md`)",
        "3. Set up MotherDuck and begin processing layer (separate task)",
    ]

    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n  Report written: {path}")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_check_config(_args) -> None:
    print("=== check-config ===")
    config.validate_all()


def cmd_test_r2(_args) -> None:
    print("=== test-r2 ===")
    config.validate_r2()
    print("  Running R2 round-trip test...")
    ok = r2.test_roundtrip()
    if ok:
        print("  R2 test: PASS")
    else:
        print("  R2 test: FAIL")
        sys.exit(1)


def cmd_pull_sportspredict(args) -> None:
    from .sources.sportspredict import run
    run_id = uuid4().hex[:8]
    dry = args.dry_run
    print(f"=== pull-sportspredict {'(dry-run) ' if dry else ''}run_id={run_id} ===")
    config.validate_r2()
    _setup_logging(run_id)
    run(run_id, dry_run=dry)
    _write_report(run_id, ["sportspredict"], dry)


def cmd_pull_football_data(args) -> None:
    from .sources.football_data_co_uk import run
    run_id = uuid4().hex[:8]
    dry = args.dry_run
    seasons = args.seasons
    print(f"=== pull-football-data {'(dry-run) ' if dry else ''}seasons={seasons} run_id={run_id} ===")
    config.validate_r2()
    _setup_logging(run_id)
    run(run_id, seasons=seasons, dry_run=dry)
    _write_report(run_id, [f"football_data_co_uk ({seasons} seasons)"], dry)


def cmd_pull_statsbomb(args) -> None:
    from .sources.statsbomb_open_data import run
    run_id = uuid4().hex[:8]
    dry = args.dry_run
    cycles = args.cycles
    print(f"=== pull-statsbomb {'(dry-run) ' if dry else ''}cycles={cycles} run_id={run_id} ===")
    config.validate_r2()
    _setup_logging(run_id)
    run(run_id, cycles=cycles, dry_run=dry)
    _write_report(run_id, [f"statsbomb_open_data ({cycles} cycles)"], dry)


def cmd_pull_statbunker(args) -> None:
    from .sources.statbunker import run
    run_id = uuid4().hex[:8]
    dry = args.dry_run
    print(f"=== pull-statbunker {'(dry-run) ' if dry else ''}run_id={run_id} ===")
    config.validate_r2()
    _setup_logging(run_id)
    run(run_id, dry_run=dry)
    _write_report(run_id, ["statbunker"], dry)


def cmd_pull_all_no_quota(args) -> None:
    from .sources.sportspredict import run as run_sp
    from .sources.football_data_co_uk import run as run_fd
    from .sources.statsbomb_open_data import run as run_sb
    from .sources.statbunker import run as run_stb

    run_id = uuid4().hex[:8]
    dry = args.dry_run
    print(f"=== pull-all-no-quota {'(dry-run) ' if dry else ''}run_id={run_id} ===")
    print("  Sources: sportspredict, football_data_co_uk, statsbomb_open_data, statbunker")
    print("  Excluded: api_football, the_odds_api (quota-limited)")
    config.validate_r2()
    _setup_logging(run_id)

    print("\n--- SportsPredict ---")
    run_sp(run_id, dry_run=dry)

    print("\n--- Football-Data.co.uk ---")
    seasons = getattr(args, "seasons", 5)
    run_fd(run_id, seasons=seasons, dry_run=dry)

    print("\n--- StatsBomb Open Data ---")
    cycles = getattr(args, "cycles", 2)
    run_sb(run_id, cycles=cycles, dry_run=dry)

    print("\n--- StatBunker ---")
    run_stb(run_id, dry_run=dry)

    sources = [
        "sportspredict",
        f"football_data_co_uk ({seasons} seasons)",
        f"statsbomb_open_data ({cycles} cycles)",
        "statbunker",
    ]
    _write_report(run_id, sources, dry)


# ---------------------------------------------------------------------------
# Argparse wiring
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m raw_landing.cli",
        description="SportsPredict raw data landing to Cloudflare R2",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("check-config", help="Validate env vars (never prints values)")
    sub.add_parser("test-r2", help="Upload test file to R2 and verify")

    p = sub.add_parser("pull-sportspredict", help="Pull SP events/lobbies/matches/markets")
    p.add_argument("--dry-run", action="store_true")

    p = sub.add_parser("pull-football-data", help="Pull Football-Data.co.uk CSVs")
    p.add_argument("--seasons", type=int, default=5)
    p.add_argument("--dry-run", action="store_true")

    p = sub.add_parser("pull-statsbomb", help="Pull StatsBomb Open Data")
    p.add_argument("--cycles", type=int, default=2)
    p.add_argument("--dry-run", action="store_true")

    p = sub.add_parser("pull-statbunker", help="Pull StatBunker referee HTML tables")
    p.add_argument("--dry-run", action="store_true")

    p = sub.add_parser("pull-all-no-quota", help="Run all four no-quota sources in sequence")
    p.add_argument("--seasons", type=int, default=5)
    p.add_argument("--cycles", type=int, default=2)
    p.add_argument("--dry-run", action="store_true")

    args = parser.parse_args(argv)
    dispatch = {
        "check-config": cmd_check_config,
        "test-r2": cmd_test_r2,
        "pull-sportspredict": cmd_pull_sportspredict,
        "pull-football-data": cmd_pull_football_data,
        "pull-statsbomb": cmd_pull_statsbomb,
        "pull-statbunker": cmd_pull_statbunker,
        "pull-all-no-quota": cmd_pull_all_no_quota,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()

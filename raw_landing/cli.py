"""CLI for raw data landing and narrowly scoped repairs."""
from __future__ import annotations

import argparse
import sys
from uuid import uuid4

from . import config, r2


def cmd_check_config(_args) -> None:
    print("=== check-config ===")
    config.validate_all()


def cmd_test_r2(_args) -> None:
    print("=== test-r2 ===")
    config.validate_r2()
    if not r2.test_roundtrip():
        sys.exit(1)


def cmd_pull_sportspredict(args) -> None:
    from .sources.sportspredict import run
    config.validate_r2()
    run(uuid4().hex[:8], dry_run=args.dry_run)


def cmd_pull_football_data(args) -> None:
    from .sources.football_data_co_uk import run
    config.validate_r2()
    run(uuid4().hex[:8], seasons=args.seasons, dry_run=args.dry_run)


def cmd_pull_statsbomb(args) -> None:
    from .sources.statsbomb_open_data import run
    config.validate_r2()
    run(uuid4().hex[:8], cycles=args.cycles, dry_run=args.dry_run)


def cmd_pull_statbunker(args) -> None:
    from .sources.statbunker import run
    config.validate_r2()
    run(uuid4().hex[:8], dry_run=args.dry_run)


def cmd_pull_all_no_quota(args) -> None:
    from .sources.football_data_co_uk import run as run_fd
    from .sources.sportspredict import run as run_sp
    from .sources.statbunker import run as run_stb
    from .sources.statsbomb_open_data import run as run_sb

    config.validate_r2()
    run_id = uuid4().hex[:8]
    run_sp(run_id, dry_run=args.dry_run)
    run_fd(run_id, seasons=args.seasons, dry_run=args.dry_run)
    run_sb(run_id, cycles=args.cycles, dry_run=args.dry_run)
    run_stb(run_id, dry_run=args.dry_run)


def cmd_repair_non_sportspredict(args) -> None:
    from .repair import apply, build_plan, summarize

    config.validate_r2()
    targets = build_plan()
    summarize(targets)
    if not args.apply:
        print("No uploads performed. Re-run with --apply to execute this exact scoped repair.")
        return
    _, uploaded = apply(targets)
    if uploaded != len(targets):
        raise RuntimeError(f"Repair uploaded {uploaded}/{len(targets)} planned files")


def cmd_reconcile_manifest(_args) -> None:
    from .reconcile import reconcile

    config.validate_r2()
    reconcile()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m raw_landing.cli",
        description="SportsPredict raw data landing to Cloudflare R2",
    )
    parser.add_argument(
        "--env-file",
        help="Path to an env file. Values are loaded without being printed.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("check-config", help="Validate configured credentials")
    sub.add_parser("test-r2", help="Upload and verify a tiny R2 test object")

    command = sub.add_parser("pull-sportspredict", help="Pull SportsPredict raw entities")
    command.add_argument("--dry-run", action="store_true")

    command = sub.add_parser("pull-football-data", help="Pull Football-Data.co.uk CSVs")
    command.add_argument("--seasons", type=int, default=5)
    command.add_argument("--dry-run", action="store_true")

    command = sub.add_parser("pull-statsbomb", help="Pull StatsBomb Open Data")
    command.add_argument("--cycles", type=int, default=2)
    command.add_argument("--dry-run", action="store_true")

    command = sub.add_parser("pull-statbunker", help="Pull StatBunker referee HTML")
    command.add_argument("--dry-run", action="store_true")

    command = sub.add_parser("pull-all-no-quota", help="Run all configured no-quota sources")
    command.add_argument("--seasons", type=int, default=5)
    command.add_argument("--cycles", type=int, default=2)
    command.add_argument("--dry-run", action="store_true")

    command = sub.add_parser(
        "repair-non-sportspredict",
        help="Plan or apply only missing Football-Data and StatsBomb objects",
    )
    command.add_argument(
        "--apply",
        action="store_true",
        help="Perform immutable uploads; without this flag the command is read-only",
    )
    sub.add_parser(
        "reconcile-manifest",
        help="Rebuild raw_manifest.csv from audited R2 metadata",
    )

    args = parser.parse_args(argv)
    if args.env_file:
        config.load_env_file(args.env_file)

    dispatch = {
        "check-config": cmd_check_config,
        "test-r2": cmd_test_r2,
        "pull-sportspredict": cmd_pull_sportspredict,
        "pull-football-data": cmd_pull_football_data,
        "pull-statsbomb": cmd_pull_statsbomb,
        "pull-statbunker": cmd_pull_statbunker,
        "pull-all-no-quota": cmd_pull_all_no_quota,
        "repair-non-sportspredict": cmd_repair_non_sportspredict,
        "reconcile-manifest": cmd_reconcile_manifest,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()

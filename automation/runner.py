"""GitHub Actions entrypoint for SportsPredict email automation."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone

from . import config
from .emailer import render_email_md, send_resend_email, subject_for, write_email_artifacts
from .models import Decision, MatchInfo
from .odds import fetch_odds_for_match, market_book_from_events
from .resolver import resolve_questions
from .sports import fetch_probability_cup_matches, fetch_questions
from .state import load_match_snapshot, load_sent_state, save_match_snapshot, save_sent_state


def _parse_now(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _inside_send_window(match: MatchInfo, now: datetime) -> bool:
    minutes = (match.kickoff - now).total_seconds() / 60.0
    return config.SEND_WINDOW_END_MIN <= minutes <= config.SEND_WINDOW_START_MIN


def _inside_lookahead(match: MatchInfo, now: datetime) -> bool:
    return now < match.kickoff <= now + timedelta(hours=config.LOOKAHEAD_HOURS)


def _snapshot_payload(
    match: MatchInfo,
    questions: list[dict],
    decisions: list[Decision],
    *,
    snapshot_time: str,
    source_failures: list[str],
    odds_signature: str,
) -> dict:
    return {
        "match_id": match.match_id,
        "match": match.name,
        "home": match.home,
        "away": match.away,
        "kickoff": match.kickoff.astimezone(timezone.utc).isoformat(),
        "snapshot_time": snapshot_time,
        "source_failures": source_failures,
        "odds_signature": odds_signature,
        "questions": [
            {
                "number": q["number"],
                "market_id": q.get("market_id"),
                "question": q["question"],
                "normalized": q["normalized"],
            }
            for q in questions
        ],
        "decisions": [d.as_dict() for d in decisions],
    }


def _failure_email_for_snapshot(snapshot: dict, now: datetime, dry_run: bool, sent_state: dict) -> None:
    match_id = snapshot.get("match_id")
    if not match_id or match_id in sent_state.get("failure_emails", {}):
        return
    kickoff = datetime.fromisoformat(snapshot["kickoff"]).astimezone(timezone.utc)
    if not (config.SEND_WINDOW_END_MIN <= (kickoff - now).total_seconds() / 60.0 <= config.SEND_WINDOW_START_MIN):
        return
    subject = f"SportsPredict automation failed: {snapshot.get('match')}"
    body = (
        f"# SportsPredict automation failed: {snapshot.get('match')}\n\n"
        f"Could not fetch SportsPredict question list during the send window.\n\n"
        f"Kickoff: {kickoff.isoformat().replace('+00:00', 'Z')}\n"
        f"Last successful snapshot: {snapshot.get('snapshot_time', 'unknown')}\n"
    )
    send_resend_email(subject, body, dry_run=dry_run)
    sent_state.setdefault("failure_emails", {})[match_id] = {
        "sent_at": now.isoformat(),
        "match": snapshot.get("match"),
        "subject": subject,
    }


def _handle_sportspredict_failure(exc: Exception, now: datetime, dry_run: bool) -> int:
    print(f"SportsPredict fetch failed: {exc}")
    sent_state = load_sent_state()
    for path in config.SNAPSHOT_DIR.glob("*.json"):
        snapshot = json.loads(path.read_text(encoding="utf-8"))
        _failure_email_for_snapshot(snapshot, now, dry_run, sent_state)
    save_sent_state(sent_state)
    return 1


def run(now: datetime, *, dry_run_email: bool, match_id: str | None) -> int:
    now_iso = now.isoformat()
    config.STATE_DIR.mkdir(parents=True, exist_ok=True)
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sent_state = load_sent_state()

    try:
        matches = fetch_probability_cup_matches()
    except Exception as exc:
        return _handle_sportspredict_failure(exc, now, dry_run_email)

    candidates = [m for m in matches if _inside_lookahead(m, now)]
    if match_id:
        candidates = [m for m in matches if m.match_id == match_id]

    print(f"Automation run at {now_iso}: {len(candidates)} candidate match(es)")
    sent_count = 0
    for match in candidates:
        print(f"Processing {match.name} ({match.match_id}) kickoff={match.kickoff.isoformat()}")
        try:
            questions = fetch_questions(match)
        except Exception as exc:
            print(f"  questions fetch failed: {exc}")
            continue

        previous = load_match_snapshot(match.match_id)
        source_failures: list[str] = []
        try:
            book, odds_meta = fetch_odds_for_match(match.home, match.away)
            source_failures.extend(odds_meta.get("failures", []))
        except Exception as exc:
            book = market_book_from_events([], match.home, match.away)
            source_failures.append(f"The Odds API final pull failed: {exc}")

        if not book.found_event:
            source_failures.append("The Odds API did not return a matching event.")

        decisions = resolve_questions(questions, book, previous)
        snapshot = _snapshot_payload(
            match,
            questions,
            decisions,
            snapshot_time=now_iso,
            source_failures=source_failures,
            odds_signature=book.complete_market_signature(),
        )
        save_match_snapshot(match.match_id, snapshot)

        already_sent = match.match_id in sent_state.get("sent_emails", {})
        if already_sent or not _inside_send_window(match, now):
            print(f"  snapshot saved; send_window={_inside_send_window(match, now)} already_sent={already_sent}")
            continue

        subject = subject_for(match, decisions)
        placeholder_output = f"outputs/automation/{match.kickoff.date().isoformat()}/{match.match_id}_email.md"
        markdown = render_email_md(
            match,
            decisions,
            sports_snapshot_time=now_iso,
            odds_snapshot_times=[now_iso] if book.found_event else [],
            source_failures=source_failures,
            output_path=placeholder_output,
        )
        md_path, json_path = write_email_artifacts(match, subject, markdown, decisions)
        # Rewrite with exact path in footer.
        markdown = render_email_md(
            match,
            decisions,
            sports_snapshot_time=now_iso,
            odds_snapshot_times=[now_iso] if book.found_event else [],
            source_failures=source_failures,
            output_path=str(md_path.relative_to(config.REPO_ROOT)),
        )
        md_path.write_text(markdown, encoding="utf-8")

        send_result = send_resend_email(subject, markdown, dry_run=dry_run_email)
        sent_state.setdefault("sent_emails", {})[match.match_id] = {
            "sent_at": now_iso,
            "kickoff": match.kickoff.isoformat(),
            "match": match.name,
            "subject": subject,
            "email_markdown": str(md_path.relative_to(config.REPO_ROOT)),
            "decisions_json": str(json_path.relative_to(config.REPO_ROOT)),
            "send_result": send_result,
        }
        save_sent_state(sent_state)
        print(f"  email {'dry-run ' if dry_run_email else ''}sent: {subject}")
        sent_count += 1

    print(f"Run complete. Emails sent: {sent_count}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SportsPredict email automation")
    parser.add_argument("--now-utc", help="Override current UTC time, ISO-8601")
    parser.add_argument("--dry-run-email", action="store_true", help="Render/write but do not send email")
    parser.add_argument("--match-id", help="Only process one SportsPredict match id")
    args = parser.parse_args()
    raise SystemExit(run(_parse_now(args.now_utc), dry_run_email=args.dry_run_email, match_id=args.match_id))


if __name__ == "__main__":
    main()

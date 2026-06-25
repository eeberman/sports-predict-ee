"""Markdown rendering and Resend delivery."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import requests

from .models import Decision, MatchInfo


def coverage(decisions: Iterable[Decision]) -> dict[str, int]:
    out = {"Direct": 0, "Derived": 0, "Fallback": 0, "REVIEW": 0, "STAY AWAY": 0}
    for d in decisions:
        out[d.source_tier] = out.get(d.source_tier, 0) + 1
    return out


def subject_for(match: MatchInfo, decisions: list[Decision]) -> str:
    market_count = sum(1 for d in decisions if d.source_tier in {"Direct", "Derived"})
    return f"SportsPredict: {match.name} - {len(decisions)} questions - {market_count} market-derived"


def render_email_md(
    match: MatchInfo,
    decisions: list[Decision],
    *,
    sports_snapshot_time: str,
    odds_snapshot_times: list[str],
    source_failures: list[str],
    output_path: str,
) -> str:
    cov = coverage(decisions)
    cov_text = " | ".join(f"{k} {cov.get(k, 0)}" for k in ("Direct", "Derived", "Fallback", "REVIEW", "STAY AWAY"))
    lines = [
        f"# {match.name}",
        "",
        f"Kickoff: {match.kickoff.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')}",
        f"Market coverage: {cov_text}",
    ]
    if source_failures:
        lines += ["", "**SOURCE WARNING:** " + "; ".join(source_failures)]
    if cov.get("REVIEW", 0):
        lines += ["", "**REVIEW REQUIRED:** One or more previously available lines disappeared before send."]
    lines += [
        "",
        "| # | Question | Prob | Source tier | Derivation |",
        "|---:|---|---:|---|---|",
    ]
    for d in decisions:
        prob = "" if d.prob is None else f"{d.prob}%"
        lines.append(f"| {d.number} | {d.question} | {prob} | {d.source_tier} | {d.derivation} |")
    disappeared = sum(1 for d in decisions if d.source_tier == "REVIEW")
    lines += [
        "",
        "## Audit",
        "",
        f"- SportsPredict snapshot: {sports_snapshot_time}",
        f"- Odds snapshots used: {', '.join(odds_snapshot_times) if odds_snapshot_times else 'none'}",
        f"- Disappeared lines: {disappeared}",
        f"- Source failures: {'; '.join(source_failures) if source_failures else 'none'}",
        f"- Output artifact: {output_path}",
        "",
        "_No auto-submit. Probabilities are YES probabilities._",
    ]
    return "\n".join(lines)


def send_resend_email(subject: str, markdown: str, *, dry_run: bool = False) -> dict:
    if dry_run:
        return {"status": "dry_run", "subject": subject}

    api_key = os.environ.get("RESEND_API_KEY", "") or os.environ.get("resend_api", "")
    email_from = os.environ.get("EMAIL_FROM", "")
    email_to = os.environ.get("EMAIL_TO", "")
    if not api_key or not email_from or not email_to:
        raise RuntimeError("RESEND_API_KEY, EMAIL_FROM, and EMAIL_TO must be configured")

    resp = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "from": email_from,
            "to": [email_to],
            "subject": subject,
            "text": markdown,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def write_email_artifacts(match: MatchInfo, subject: str, markdown: str, decisions: list[Decision]) -> tuple[Path, Path]:
    from . import config
    import json
    import re

    day = match.kickoff.astimezone(timezone.utc).date().isoformat()
    outdir = config.OUTPUT_DIR / day
    outdir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "_", match.name.lower()).strip("_")
    md_path = outdir / f"{slug}_{match.match_id}_email.md"
    json_path = outdir / f"{slug}_{match.match_id}_decisions.json"
    md_path.write_text(markdown, encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "match_id": match.match_id,
                "match": match.name,
                "kickoff": match.kickoff.astimezone(timezone.utc).isoformat(),
                "subject": subject,
                "written_at": datetime.now(timezone.utc).isoformat(),
                "decisions": [d.as_dict() for d in decisions],
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return md_path, json_path

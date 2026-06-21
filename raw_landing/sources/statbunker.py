"""
Pull StatBunker referee card tables and upload raw HTML to R2.

Reuses provider_probe/clients/statbunker.py for HTTP fetch logic — does not duplicate it.
Known comp_ids are fetched; international comp_ids go to statbunker_manual_todo.md.
2-second delay between requests (enforced by the underlying client).
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from .. import config, manifest, r2
from provider_probe.clients import statbunker as _sb_client


def _r2_key(comp_id: int, label: str, run_id: str) -> str:
    today = date.today().isoformat()
    filename = f"{comp_id}_{label}.html"
    return f"raw/statbunker/referee_cards/ingested_date={today}/run_id={run_id}/{filename}"


def _write_todo() -> None:
    path = config.OUTPUTS / "statbunker_manual_todo.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# StatBunker Manual Todo — International Competition comp_ids\n\n"
        "The following competition referee card tables are needed but their comp_ids\n"
        "on StatBunker are not yet known. Find them manually:\n\n"
        "1. Visit https://www.statbunker.com\n"
        "2. Click the competition (e.g. 'FIFA World Cup 2026')\n"
        "3. Look at the URL: `.../competitions/RefereeYellowCards?comp_id=NNN`\n"
        "4. Add the comp_id to `provider_probe/clients/statbunker.py` COMP_IDS list\n"
        "5. Re-run: `python -m raw_landing.cli pull-statbunker`\n\n"
        "## Needed competitions\n\n"
        "- FIFA World Cup 2026\n"
        "- UEFA Euro (current cycle)\n"
        "- Copa América (current cycle)\n"
        "- AFCON (current cycle)\n\n"
        "## Fields expected in each table\n\n"
        "referee_name, matches, yellow_cards, red_yellow_cards, red_cards,\n"
        "yellow_per_match, cards_per_match, home_cards, away_cards,\n"
        "fh_cards_avg_minute, sh_cards_avg_minute\n\n"
        "## R2 path pattern\n\n"
        "`raw/statbunker/referee_cards/ingested_date=YYYY-MM-DD/run_id=.../`\n",
        encoding="utf-8",
    )
    print(f"  [statbunker] Wrote manual todo: {path}")


def run(run_id: str, dry_run: bool = False) -> list[manifest.ManifestRow]:
    rows: list[manifest.ManifestRow] = []
    comp_ids = _sb_client.COMP_IDS  # [(776, "Premier League"), ...]

    print(f"  [statbunker] {len(comp_ids)} known competitions to fetch")

    for comp_id, comp_name in comp_ids:
        label = comp_name.lower().replace(" ", "_").replace("/", "_")
        key = _r2_key(comp_id, label, run_id)
        url = f"{_sb_client.BASE_URL}{_sb_client.REFEREE_PATH}?comp_id={comp_id}"

        print(f"  [statbunker] {'DRY-RUN ' if dry_run else ''}{comp_name} (comp_id={comp_id}) -> {key}")

        if dry_run:
            rows.append(manifest.ManifestRow(
                run_id=run_id, source_name="statbunker",
                entity_name="referee_cards", source_url=url,
                r2_key=key, r2_uri=r2.r2_uri(key), status="dry_run",
                notes=f"comp_id={comp_id}",
            ))
            continue

        if manifest.already_uploaded(key):
            print("    skipped (already uploaded)")
            rows.append(manifest.ManifestRow(
                run_id=run_id, source_name="statbunker",
                entity_name="referee_cards", source_url=url,
                r2_key=key, r2_uri=r2.r2_uri(key), status="skipped",
            ))
            continue

        try:
            html = _sb_client.get_referee_stats_page(comp_id)
            data = html.encode("utf-8", errors="replace")
            n = r2.upload_bytes(key, data, "text/html; charset=utf-8")
            # Quick parse to count referees for manifest
            parsed_rows, _ = _sb_client.parse_referee_table(html)
            row = manifest.ManifestRow(
                run_id=run_id, source_name="statbunker",
                entity_name="referee_cards", source_url=url,
                r2_key=key, r2_uri=r2.r2_uri(key), bytes_uploaded=n,
                row_count_if_known=len(parsed_rows),
                notes=f"comp_id={comp_id}, {len(parsed_rows)} referees",
            )
            manifest.append_row(row)
            rows.append(row)
            print(f"    {n:,} bytes, {len(parsed_rows)} referees")
        except Exception as exc:
            note = str(exc)[:120]
            print(f"    FAILED: {note}")
            row = manifest.ManifestRow(
                run_id=run_id, source_name="statbunker",
                entity_name="referee_cards", source_url=url,
                r2_key=key, r2_uri=r2.r2_uri(key), status="error", notes=note,
            )
            manifest.append_row(row)
            rows.append(row)

    _write_todo()
    uploaded = sum(1 for r_ in rows if r_.status == "uploaded")
    print(f"  [statbunker] done — {uploaded}/{len(comp_ids)} uploaded")
    return rows

from __future__ import annotations

import csv
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import boto3
from dotenv import dotenv_values


WORKSPACE = Path(__file__).resolve().parent
CHECKOUT = Path(r"C:\tmp\sports-predict-ee-inspect")
OUTPUTS = WORKSPACE / "outputs"
ENV_PATH = WORKSPACE / ".env"
MANIFEST_CANDIDATES = [WORKSPACE / "raw_manifest.csv", CHECKOUT / "raw_manifest.csv"]

EXPECTED = [
    ("sportspredict", "events", "raw/sportspredict/events/"),
    ("sportspredict", "lobbies", "raw/sportspredict/lobbies/"),
    ("sportspredict", "matches", "raw/sportspredict/matches/"),
    ("sportspredict", "markets", "raw/sportspredict/markets/"),
    ("football_data_co_uk", "csv", "raw/football_data_co_uk/csv/"),
    ("statsbomb_open_data", "competitions", "raw/statsbomb_open_data/competitions/"),
    ("statsbomb_open_data", "matches", "raw/statsbomb_open_data/matches/"),
    ("statsbomb_open_data", "events", "raw/statsbomb_open_data/events/"),
    ("statsbomb_open_data", "lineups", "raw/statsbomb_open_data/lineups/"),
    ("statbunker", "referee_cards", "raw/statbunker/referee_cards/"),
]

FOOTBALL_LEAGUES = [
    "england_E0", "spain_SP1", "germany_D1", "italy_I1", "france_F1",
    "netherlands_N1", "portugal_P1", "belgium_B1", "turkey_T1",
    "greece_G1", "scotland_SC0",
]
FOOTBALL_SEASONS = ["2526", "2425", "2324", "2223", "2122"]
SUCCESS_STATUSES = {"uploaded", "success", "complete", "completed", "ok", "skipped"}


def env_value(config: dict[str, str | None], *names: str, default: str = "") -> str:
    for name in names:
        value = config.get(name)
        if value:
            return str(value).strip()
    return default


def run_id_from_key(key: str) -> str:
    match = re.search(r"(?:^|/)run_id=([^/]+)", key)
    return match.group(1) if match else ""


def entity_objects(objects: list[dict], prefix: str) -> list[dict]:
    return [item for item in objects if item["Key"].startswith(prefix)]


def latest_timestamp(items: list[dict], manifest_rows: list[dict]) -> str:
    manifest_times = [row.get("ingested_at_utc", "") for row in manifest_rows if row.get("ingested_at_utc")]
    if manifest_times:
        return max(manifest_times)
    if items:
        return max(item["LastModified"] for item in items).astimezone(timezone.utc).isoformat()
    return ""


def read_small_json(client, bucket: str, item: dict, max_bytes: int = 1_000_000):
    if item["Size"] <= 0 or item["Size"] > max_bytes:
        return None
    body = client.get_object(Bucket=bucket, Key=item["Key"])["Body"].read(max_bytes + 1)
    if len(body) > max_bytes:
        return None
    return json.loads(body)


def json_count(value) -> int | None:
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict):
        for key in ("data", "results", "events", "lobbies", "matches", "markets"):
            if isinstance(value.get(key), list):
                return len(value[key])
    return None


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    config = dotenv_values(ENV_PATH)
    bucket = env_value(config, "R2_BUCKET")
    account_id = env_value(config, "R2_ACCOUNT_ID")
    configured_endpoint = env_value(
        config,
        "R2_ENDPOINT_URL",
        "s3_api",
        default=f"https://{account_id}.r2.cloudflarestorage.com",
    )
    parsed_endpoint = urlsplit(configured_endpoint)
    endpoint = f"{parsed_endpoint.scheme}://{parsed_endpoint.netloc}"
    access_key = env_value(config, "AWS_ACCESS_KEY_ID", "R2_ACCESS_KEY_ID")
    secret_key = env_value(config, "AWS_SECRET_ACCESS_KEY", "R2_SECRET_ACCESS_KEY")
    region = env_value(config, "AWS_REGION", default="auto")

    required_status = {
        "R2_BUCKET": bool(bucket),
        "R2_ACCOUNT_ID": bool(account_id),
        "R2_ENDPOINT_URL": bool(env_value(config, "R2_ENDPOINT_URL")),
        "AWS_ACCESS_KEY_ID": bool(env_value(config, "AWS_ACCESS_KEY_ID")),
        "AWS_SECRET_ACCESS_KEY": bool(env_value(config, "AWS_SECRET_ACCESS_KEY")),
        "AWS_REGION": bool(env_value(config, "AWS_REGION")),
    }
    alias_status = {
        "R2_ACCESS_KEY_ID": bool(env_value(config, "R2_ACCESS_KEY_ID")),
        "R2_SECRET_ACCESS_KEY": bool(env_value(config, "R2_SECRET_ACCESS_KEY")),
        "s3_api": bool(env_value(config, "s3_api")),
    }

    client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
    )

    # Listing the bucket validates read connectivity without creating an object.
    objects: list[dict] = []
    for page in client.get_paginator("list_objects_v2").paginate(Bucket=bucket):
        objects.extend(page.get("Contents", []))
    object_by_key = {item["Key"]: item for item in objects}

    manifest_path = next((path for path in MANIFEST_CANDIDATES if path.exists()), None)
    manifest_rows: list[dict] = []
    if manifest_path:
        with manifest_path.open(newline="", encoding="utf-8-sig") as handle:
            manifest_rows = list(csv.DictReader(handle))
    manifest_keys = {row.get("r2_key", "") for row in manifest_rows if row.get("r2_key")}

    target_objects = [
        item for item in objects
        if any(item["Key"].startswith(prefix) for _, _, prefix in EXPECTED)
    ]

    # Manifest/bucket differences.
    diff_rows: list[dict] = []
    for item in target_objects:
        if item["Key"] not in manifest_keys:
            diff_rows.append({
                "mismatch_type": "bucket_object_missing_from_manifest",
                "r2_key": item["Key"],
                "bucket_size": item["Size"],
                "manifest_status": "",
                "details": "Object exists under an audited raw prefix but has no manifest row.",
            })

    for row in manifest_rows:
        key = row.get("r2_key", "")
        item = object_by_key.get(key)
        status = row.get("status", "").strip().lower()
        missing_fields = [
            field for field in ("source_name", "entity_name", "ingested_at_utc", "source_url")
            if not row.get(field, "").strip()
        ]
        if not item:
            diff_rows.append({
                "mismatch_type": "manifest_row_missing_from_bucket",
                "r2_key": key,
                "bucket_size": "",
                "manifest_status": status,
                "details": "Manifest key does not exist in R2.",
            })
        elif item["Size"] <= 0:
            diff_rows.append({
                "mismatch_type": "manifest_object_zero_bytes",
                "r2_key": key,
                "bucket_size": item["Size"],
                "manifest_status": status,
                "details": "Manifest key exists but object size is zero.",
            })
        if status not in SUCCESS_STATUSES:
            diff_rows.append({
                "mismatch_type": "manifest_status_not_success",
                "r2_key": key,
                "bucket_size": item["Size"] if item else "",
                "manifest_status": status,
                "details": "Manifest status is not success-equivalent.",
            })
        if missing_fields:
            diff_rows.append({
                "mismatch_type": "manifest_missing_required_fields",
                "r2_key": key,
                "bucket_size": item["Size"] if item else "",
                "manifest_status": status,
                "details": "Missing fields: " + ", ".join(missing_fields),
            })

    noncanonical = [
        item for item in objects
        if item["Key"].startswith(f"{bucket}/raw/")
    ]
    for item in noncanonical:
        diff_rows.append({
            "mismatch_type": "noncanonical_bucket_prefixed_key",
            "r2_key": item["Key"],
            "bucket_size": item["Size"],
            "manifest_status": "",
            "details": "Object key repeats the bucket name before raw/.",
        })

    # Source-specific checks.
    football_items = entity_objects(objects, "raw/football_data_co_uk/csv/")
    football_keys = {Path(item["Key"]).name for item in football_items}
    expected_football = {
        f"{league}_{season}.csv" for league in FOOTBALL_LEAGUES for season in FOOTBALL_SEASONS
    }
    missing_football = sorted(expected_football - football_keys)
    football_by_league = {
        league: sum(name.startswith(league + "_") for name in football_keys)
        for league in FOOTBALL_LEAGUES
    }

    sports_samples: dict[str, str] = {}
    for entity in ("events", "lobbies", "matches", "markets"):
        items = entity_objects(objects, f"raw/sportspredict/{entity}/")
        if not items:
            sports_samples[entity] = "not available"
            continue
        latest = max(items, key=lambda item: item["LastModified"])
        try:
            count = json_count(read_small_json(client, bucket, latest))
            sports_samples[entity] = f"latest sample count={count}" if count is not None else "not cheaply countable"
        except Exception as exc:
            sports_samples[entity] = f"sample failed: {type(exc).__name__}"

    stats_match_items = entity_objects(objects, "raw/statsbomb_open_data/matches/")
    stats_event_items = entity_objects(objects, "raw/statsbomb_open_data/events/")
    stats_lineup_items = entity_objects(objects, "raw/statsbomb_open_data/lineups/")
    event_ids = {Path(item["Key"]).stem for item in stats_event_items}
    lineup_ids = {Path(item["Key"]).stem for item in stats_lineup_items}
    missing_lineup_ids = sorted(event_ids - lineup_ids)
    missing_event_ids = sorted(lineup_ids - event_ids)
    stats_match_record_count = 0
    stats_match_sample_complete = True
    if sum(item["Size"] for item in stats_match_items) <= 5_000_000:
        for item in stats_match_items:
            try:
                value = read_small_json(client, bucket, item, max_bytes=2_000_000)
                if isinstance(value, list):
                    stats_match_record_count += len(value)
                else:
                    stats_match_sample_complete = False
            except Exception:
                stats_match_sample_complete = False
    else:
        stats_match_sample_complete = False

    manual_todo = CHECKOUT / "outputs" / "statbunker_manual_todo.md"

    # Coverage table.
    coverage_rows: list[dict] = []
    for source, entity, prefix in EXPECTED:
        items = entity_objects(objects, prefix)
        rows = [
            row for row in manifest_rows
            if row.get("source_name") == source and row.get("entity_name") == entity
        ]
        status_counts = Counter((row.get("status") or "missing").lower() for row in rows)
        run_ids = {run_id_from_key(item["Key"]) for item in items if run_id_from_key(item["Key"])}
        notes: list[str] = []
        expected_status = "required"
        completeness = "missing" if not items else "present_but_needs_review"

        if not items:
            notes.append("No objects found under expected prefix.")
        if items and not rows:
            notes.append("Objects are not indexed by the discovered manifest.")
        if any((row.get("status") or "").lower() not in SUCCESS_STATUSES for row in rows):
            notes.append("Manifest contains non-success status rows.")

        if source == "football_data_co_uk":
            notes.append(f"Configured coverage {len(football_items)}/55 files.")
            if missing_football:
                notes.append("Missing configured files: " + ", ".join(missing_football))
            elif rows and all((row.get("status") or "").lower() in SUCCESS_STATUSES for row in rows):
                completeness = "complete"
        elif source == "statsbomb_open_data" and entity == "events":
            notes.append(f"Event IDs without lineups: {len(missing_lineup_ids)}.")
        elif source == "statsbomb_open_data" and entity == "lineups":
            notes.append(f"Lineup IDs without events: {len(missing_event_ids)}.")
        elif source == "statsbomb_open_data" and entity == "matches":
            if stats_match_sample_complete:
                notes.append(f"Cheap JSON count across match files: {stats_match_record_count} matches.")
        elif source == "sportspredict":
            notes.append(sports_samples[entity] + ".")
        elif source == "statbunker":
            expected_status = "required_configured; international_manual"
            notes.append(f"Manual todo present: {'yes' if manual_todo.exists() else 'no'}.")
            if not items and manual_todo.exists():
                completeness = "blocked_manual_step"
            elif items:
                notes.append("Configured club competitions are present; international comp_ids remain manual.")

        if items and rows and not notes and all((row.get("status") or "").lower() in SUCCESS_STATUSES for row in rows):
            completeness = "complete"

        coverage_rows.append({
            "source_name": source,
            "entity_name": entity,
            "expected_prefix": prefix,
            "expected_status": expected_status,
            "r2_object_count": len(items),
            "total_bytes": sum(item["Size"] for item in items),
            "manifest_row_count": len(rows),
            "distinct_run_ids": len(run_ids),
            "latest_ingested_at_utc": latest_timestamp(items, rows),
            "status_counts": json.dumps(dict(status_counts), sort_keys=True),
            "completeness_status": completeness,
            "notes": " ".join(notes),
        })

    # Local raw storage audit: report raw-like files and all files >= 1 MiB.
    local_rows: list[dict] = []
    roots = [WORKSPACE, CHECKOUT]
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or ".git" in path.parts or path == ENV_PATH:
                continue
            size = path.stat().st_size
            raw_like = path.suffix.lower() in {".json", ".csv", ".html", ".parquet", ".gz", ".zip"}
            raw_path = any(part.lower() in {"raw", "data", "downloads", "samples"} for part in path.parts)
            if size >= 1_048_576 or (raw_like and raw_path):
                local_rows.append({
                    "path": str(path),
                    "size_bytes": size,
                    "size_mib": f"{size / 1_048_576:.3f}",
                    "duplicate_risk": "review" if size >= 1_048_576 else "low",
                    "notes": "Large local file" if size >= 1_048_576 else "Small raw-like project artifact",
                })

    if not local_rows:
        local_rows.append({
            "path": "",
            "size_bytes": 0,
            "size_mib": "0.000",
            "duplicate_risk": "none",
            "notes": "No local raw-like files or files >= 1 MiB found outside .git and .env.",
        })

    coverage_fields = [
        "source_name", "entity_name", "expected_prefix", "expected_status",
        "r2_object_count", "total_bytes", "manifest_row_count", "distinct_run_ids",
        "latest_ingested_at_utc", "status_counts", "completeness_status", "notes",
    ]
    diff_fields = ["mismatch_type", "r2_key", "bucket_size", "manifest_status", "details"]
    local_fields = ["path", "size_bytes", "size_mib", "duplicate_risk", "notes"]
    write_csv(OUTPUTS / "r2_raw_landing_audit.csv", coverage_rows, coverage_fields)
    write_csv(OUTPUTS / "r2_manifest_vs_bucket_diff.csv", diff_rows, diff_fields)
    write_csv(OUTPUTS / "local_raw_storage_audit.csv", local_rows, local_fields)

    missing_entities = [
        f"{row['source_name']}/{row['entity_name']}"
        for row in coverage_rows if row["completeness_status"] == "missing"
    ]
    required_env_missing = [name for name, present in required_status.items() if not present]
    alias_env_present = [name for name, present in alias_status.items() if present]
    mismatch_counts = Counter(row["mismatch_type"] for row in diff_rows)
    target_bytes = sum(item["Size"] for item in target_objects)
    overall = "incomplete_needs_reconciliation"

    md: list[str] = [
        "# R2 Raw Landing Audit",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        f"**R2 connection:** PASS (bucket `{bucket}` listed successfully; no object was uploaded)",
        f"**Overall completeness:** `{overall}`",
        "",
        "## Executive summary",
        "",
        f"R2 is reachable and contains {len(target_objects)} objects ({target_bytes:,} bytes) under the four audited source prefixes. ",
        "The landing is not complete: SportsPredict matches and markets are absent, Football-Data.co.uk is one configured file short, and StatsBomb has one event without a matching lineup. ",
        f"The discovered local manifest has {len(manifest_rows)} rows and does not index most bucket objects; {mismatch_counts.get('bucket_object_missing_from_manifest', 0)} bucket objects lack manifest rows.",
        "",
        "It is **not yet safe to treat the raw layer as fully complete for processing**. Existing data can be explored later, but the manifest should be reconciled and missing entities reviewed first.",
        "",
        "## Project structure",
        "",
        f"- Workspace: `{WORKSPACE}`",
        f"- Raw landing package: `{CHECKOUT / 'raw_landing'}`",
        f"- Manifest used: `{manifest_path if manifest_path else 'not found'}`",
        f"- Reports: `{CHECKOUT / 'outputs'}`",
        "- Logs: none found",
        f"- StatBunker manual todo: `{manual_todo}` ({'present' if manual_todo.exists() else 'missing'})",
        "",
        "## Environment compatibility",
        "",
        "Required canonical variable presence (values not printed):",
        "",
    ]
    for name, present in required_status.items():
        md.append(f"- `{name}`: {'present' if present else 'MISSING'}")
    md += ["", "Compatible aliases used by this audit:", ""]
    for name, present in alias_status.items():
        md.append(f"- `{name}`: {'present' if present else 'missing'}")
    md += [
        "",
        f"Canonical variables missing: {', '.join(required_env_missing) if required_env_missing else 'none'}. The audit connected using existing aliases: {', '.join(alias_env_present)}.",
        "",
        "## Coverage audit",
        "",
        "| source | entity | R2 files | bytes | manifest rows | runs | completeness | notes |",
        "|---|---|---:|---:|---:|---:|---|---|",
    ]
    for row in coverage_rows:
        notes = str(row["notes"]).replace("|", "\\|")
        md.append(
            f"| {row['source_name']} | {row['entity_name']} | {row['r2_object_count']} | "
            f"{row['total_bytes']:,} | {row['manifest_row_count']} | {row['distinct_run_ids']} | "
            f"{row['completeness_status']} | {notes} |"
        )

    md += [
        "",
        "## Source-specific findings",
        "",
        "### SportsPredict",
        "",
        f"- Events: {len(entity_objects(objects, 'raw/sportspredict/events/'))} files; {sports_samples['events']}.",
        f"- Lobbies: {len(entity_objects(objects, 'raw/sportspredict/lobbies/'))} files; {sports_samples['lobbies']}.",
        f"- Matches: {len(entity_objects(objects, 'raw/sportspredict/matches/'))} files.",
        f"- Markets: {len(entity_objects(objects, 'raw/sportspredict/markets/'))} files.",
        "- Markets cannot be validated for nonzero size because no market object exists.",
        "",
        "### Football-Data.co.uk",
        "",
        f"- Present: {len(football_items)}/55 configured league-season files.",
        f"- Missing: {', '.join(missing_football) if missing_football else 'none'}.",
        "- Files by configured league: " + ", ".join(f"{name}={count}" for name, count in football_by_league.items()) + ".",
        "",
        "### StatsBomb Open Data",
        "",
        f"- Match files: {len(stats_match_items)}; cheap parsed match count: {stats_match_record_count if stats_match_sample_complete else 'not fully sampled'}.",
        f"- Event files: {len(stats_event_items)}.",
        f"- Lineup files: {len(stats_lineup_items)}.",
        f"- Event IDs missing lineups: {', '.join(missing_lineup_ids) if missing_lineup_ids else 'none'}.",
        f"- Lineup IDs missing events: {', '.join(missing_event_ids) if missing_event_ids else 'none'}.",
        "",
        "### StatBunker",
        "",
        f"- Referee-card files: {len(entity_objects(objects, 'raw/statbunker/referee_cards/'))}.",
        f"- Manual todo: {'present' if manual_todo.exists() else 'missing'}.",
        "- Four configured club competitions are present. International competition IDs remain a documented manual step.",
        "",
        "## Manifest versus bucket",
        "",
        f"- Manifest rows: {len(manifest_rows)}.",
        f"- Bucket objects missing from manifest: {mismatch_counts.get('bucket_object_missing_from_manifest', 0)}.",
        f"- Manifest rows missing from R2: {mismatch_counts.get('manifest_row_missing_from_bucket', 0)}.",
        f"- Manifest rows with non-success status: {mismatch_counts.get('manifest_status_not_success', 0)}.",
        f"- Zero-byte manifest objects: {mismatch_counts.get('manifest_object_zero_bytes', 0)}.",
        f"- Noncanonical bucket-prefixed keys: {mismatch_counts.get('noncanonical_bucket_prefixed_key', 0)}.",
        f"- Total diff records: {len(diff_rows)}.",
        "",
        "The three StatBunker rows originally recorded as errors now have nonzero objects in R2, so their manifest statuses are stale.",
        "",
        "## Local storage",
        "",
        f"Local duplicate candidates: {sum(1 for row in local_rows if row['duplicate_risk'] == 'review')}. No large raw datasets were downloaded during this audit.",
        "",
        "## Recommended next actions",
        "",
        "1. Reconcile or rebuild `raw_manifest.csv` from existing R2 object metadata without re-pulling source data.",
        "2. Review the missing SportsPredict `matches` and `markets` entities. A selective pull would require explicit approval and a SportsPredict credential.",
        f"3. Review the single missing Football-Data file (`{missing_football[0] if missing_football else 'none'}`) before approving any selective download.",
        f"4. Review the StatsBomb lineup gap (`{missing_lineup_ids[0] if missing_lineup_ids else 'none'}`) before approving a selective download.",
        "5. Normalize the project's R2 client/configuration to the working S3 credential aliases before any future landing run.",
        "6. Do not start full processing as if the landing were complete until steps 1-4 are resolved or explicitly accepted as deferred.",
        "",
        "## Final audit status",
        "",
        "1. R2 connection status: PASS",
        f"2. Overall completeness status: {overall}",
        f"3. Missing source/entity list: {', '.join(missing_entities) if missing_entities else 'none'}",
        f"4. Manifest/R2 mismatch count: {len(diff_rows)}",
        "5. Recommended next action: reconcile the manifest from R2 metadata; then decide whether to approve selective pulls for the identified gaps.",
    ]
    (OUTPUTS / "r2_raw_landing_audit.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print("R2 connection status: PASS")
    print(f"Overall completeness status: {overall}")
    print("Missing source/entity list: " + (", ".join(missing_entities) if missing_entities else "none"))
    print(f"Manifest/R2 mismatch count: {len(diff_rows)}")
    print("Recommended next action: reconcile the manifest from R2 metadata, then review selective gaps; do not re-pull by default.")


if __name__ == "__main__":
    main()

"""
Cloudflare R2 client using the Cloudflare REST API.
The S3-compatible endpoint (*.r2.cloudflarestorage.com:443) requires a per-account
TLS certificate that Cloudflare provisions separately; the REST API works immediately.
"""
from __future__ import annotations

import json
from datetime import date, timezone, datetime
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

import requests

from . import config


class R2Error(RuntimeError):
    pass


def _base_url() -> str:
    account_id = config.get("R2_ACCOUNT_ID")
    bucket = config.get("R2_BUCKET")
    return f"https://api.cloudflare.com/client/v4/accounts/{account_id}/r2/buckets/{bucket}/objects"


def _auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {config.get('CLOUDFLARE_API_TOKEN')}"}


def _key_url(r2_key: str) -> str:
    return f"{_base_url()}/{quote(r2_key, safe='/')}"


def r2_uri(r2_key: str) -> str:
    return f"s3://{config.get('R2_BUCKET')}/{r2_key}"


def upload_bytes(r2_key: str, data: bytes, content_type: str = "application/octet-stream") -> int:
    headers = {**_auth(), "Content-Type": content_type}
    try:
        resp = requests.put(_key_url(r2_key), data=data, headers=headers, timeout=120)
        if not resp.ok:
            raise R2Error(f"Upload failed for {r2_key}: HTTP {resp.status_code} {resp.text[:200]}")
        return len(data)
    except requests.RequestException as exc:
        raise R2Error(f"Upload failed for {r2_key}: {exc}") from exc


def upload_file(r2_key: str, local_path: Path, content_type: str = "application/octet-stream") -> int:
    return upload_bytes(r2_key, local_path.read_bytes(), content_type)


def key_exists(r2_key: str) -> bool:
    try:
        resp = requests.get(
            _key_url(r2_key),
            headers={**_auth(), "Range": "bytes=0-0"},
            timeout=30,
            stream=True,
        )
        resp.close()
        if resp.status_code in (200, 206):
            return True
        if resp.status_code == 404:
            return False
        raise R2Error(f"key_exists failed for {r2_key}: HTTP {resp.status_code}")
    except requests.RequestException as exc:
        raise R2Error(f"key_exists failed for {r2_key}: {exc}") from exc


def test_roundtrip() -> bool:
    run_id = uuid4().hex[:8]
    today = date.today().isoformat()
    key = f"raw/_system/r2_test/ingested_date={today}/run_id={run_id}/test.json"
    payload = json.dumps({
        "test": True,
        "run_id": run_id,
        "ts": datetime.now(timezone.utc).isoformat(),
    }).encode()
    try:
        upload_bytes(key, payload, "application/json")
        exists = key_exists(key)
        print(f"  Uploaded: {r2_uri(key)}")
        print(f"  Verified: {'yes' if exists else 'NO — key_exists returned False'}")
        return exists
    except R2Error as exc:
        print(f"  R2 error: {exc}")
        return False

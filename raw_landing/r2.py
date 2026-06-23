"""Immutable Cloudflare R2 client using its S3-compatible API."""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from . import config


class R2Error(RuntimeError):
    pass


_CLIENT = None


def endpoint_url() -> str:
    parsed = urlsplit(config.get("R2_ENDPOINT_URL"))
    if not parsed.scheme or not parsed.netloc:
        raise R2Error("R2_ENDPOINT_URL is not a valid absolute URL")
    return f"{parsed.scheme}://{parsed.netloc}"


def client():
    global _CLIENT
    if _CLIENT is None:
        missing = [key for key in config.R2_REQUIRED if not config.get(key)]
        if missing:
            raise R2Error(f"Missing required R2 environment variables: {missing}")
        _CLIENT = boto3.client(
            "s3",
            endpoint_url=endpoint_url(),
            aws_access_key_id=config.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=config.get("AWS_SECRET_ACCESS_KEY"),
            region_name=config.get("AWS_REGION", "auto"),
        )
    return _CLIENT


def bucket_name() -> str:
    return config.get("R2_BUCKET")


def r2_uri(r2_key: str) -> str:
    return f"s3://{bucket_name()}/{r2_key}"


def head_object(r2_key: str) -> dict | None:
    try:
        return client().head_object(Bucket=bucket_name(), Key=r2_key)
    except ClientError as exc:
        code = str(exc.response.get("Error", {}).get("Code", ""))
        status = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        if code in {"404", "NoSuchKey", "NotFound"} or status == 404:
            return None
        raise R2Error(f"head_object failed for {r2_key}: {code or status}") from exc
    except BotoCoreError as exc:
        raise R2Error(f"head_object failed for {r2_key}: {exc}") from exc


def key_exists(r2_key: str) -> bool:
    return head_object(r2_key) is not None


def upload_bytes(r2_key: str, data: bytes, content_type: str = "application/octet-stream") -> int:
    if key_exists(r2_key):
        raise R2Error(f"Refusing to overwrite existing immutable key: {r2_key}")
    try:
        client().put_object(Bucket=bucket_name(), Key=r2_key, Body=data, ContentType=content_type)
    except (BotoCoreError, ClientError) as exc:
        raise R2Error(f"Upload failed for {r2_key}: {exc}") from exc
    metadata = head_object(r2_key)
    if not metadata or int(metadata.get("ContentLength", -1)) != len(data):
        raise R2Error(f"Upload verification failed for {r2_key}")
    return len(data)


def upload_file(r2_key: str, local_path: Path, content_type: str = "application/octet-stream") -> int:
    return upload_bytes(r2_key, local_path.read_bytes(), content_type)


def download_bytes(r2_key: str, max_bytes: int | None = None) -> bytes:
    metadata = head_object(r2_key)
    if metadata is None:
        raise R2Error(f"Object does not exist: {r2_key}")
    size = int(metadata.get("ContentLength", 0))
    if max_bytes is not None and size > max_bytes:
        raise R2Error(f"Object exceeds read limit ({size} > {max_bytes}): {r2_key}")
    try:
        return client().get_object(Bucket=bucket_name(), Key=r2_key)["Body"].read()
    except (BotoCoreError, ClientError) as exc:
        raise R2Error(f"Download failed for {r2_key}: {exc}") from exc


def list_objects(prefix: str = "") -> list[dict]:
    items: list[dict] = []
    try:
        paginator = client().get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket_name(), Prefix=prefix):
            items.extend(page.get("Contents", []))
        return items
    except (BotoCoreError, ClientError) as exc:
        raise R2Error(f"R2 list failed for prefix {prefix!r}: {exc}") from exc


def test_roundtrip() -> bool:
    run_id = uuid4().hex[:8]
    key = f"raw/_system/r2_test/ingested_date={date.today().isoformat()}/run_id={run_id}/test.json"
    payload = json.dumps({"test": True, "run_id": run_id, "ts": datetime.now(timezone.utc).isoformat()}).encode()
    try:
        upload_bytes(key, payload, "application/json")
        print(f"  Uploaded and verified: {r2_uri(key)}")
        return True
    except R2Error as exc:
        print(f"  R2 error: {exc}")
        return False

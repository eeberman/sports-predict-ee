import json
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

import boto3
from dotenv import dotenv_values


config = dotenv_values(Path(__file__).with_name(".env"))
endpoint = config.get("s3_api") or (
    f"https://{config['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com"
)
client = boto3.client(
    "s3",
    endpoint_url=endpoint,
    aws_access_key_id=config["R2_ACCESS_KEY_ID"],
    aws_secret_access_key=config["R2_SECRET_ACCESS_KEY"],
    region_name="auto",
)

key = (
    f"raw/_system/r2_test/ingested_date={date.today().isoformat()}"
    f"/run_id={uuid.uuid4().hex[:8]}/test.json"
)
body = json.dumps(
    {"test": True, "ts": datetime.now(timezone.utc).isoformat()}
).encode()

client.put_object(
    Bucket=config["R2_BUCKET"],
    Key=key,
    Body=body,
    ContentType="application/json",
)
metadata = client.head_object(Bucket=config["R2_BUCKET"], Key=key)

print("R2 S3 test: PASS")
print(f"Key: {key}")
print(f"Size: {metadata['ContentLength']}")
print(f"ETag present: {bool(metadata.get('ETag'))}")

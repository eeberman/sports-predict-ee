from collections import Counter
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

objects = []
paginator = client.get_paginator("list_objects_v2")
for page in paginator.paginate(Bucket=config["R2_BUCKET"]):
    objects.extend(page.get("Contents", []))

print(f"Bucket: {config['R2_BUCKET']}")
print(f"Objects: {len(objects)}")
print(f"Bytes: {sum(item['Size'] for item in objects)}")

prefixes = Counter("/".join(item["Key"].split("/")[:3]) for item in objects)
print("Prefixes:")
for prefix, count in sorted(prefixes.items()):
    print(f"  {prefix}: {count}")

print("Latest objects:")
for item in sorted(objects, key=lambda value: value["LastModified"], reverse=True)[:20]:
    print(f"  {item['LastModified'].isoformat()}  {item['Size']:>10}  {item['Key']}")

# Assignment 3 release demo: deployed automatically from GitHub main.
import hashlib
import json
import os
from urllib.error import HTTPError
from urllib.parse import unquote_plus
from urllib.request import Request, urlopen

import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

session = boto3.Session()
s3 = session.client("s3")
rekognition = session.client("rekognition")


def es_request(method, path, body=None):
    url = os.environ["ES_ENDPOINT"].rstrip("/") + path
    data = json.dumps(body).encode("utf-8") if body is not None else None

    request = AWSRequest(
        method=method,
        url=url,
        data=data,
        headers={"Content-Type": "application/json"}
    )

    credentials = session.get_credentials().get_frozen_credentials()
    SigV4Auth(credentials, "es", os.environ["AWS_REGION"]).add_auth(request)

    signed = Request(
        url,
        data=data,
        headers=dict(request.headers),
        method=method
    )

    try:
        with urlopen(signed, timeout=10) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else {}
    except HTTPError as error:
        raw = error.read().decode("utf-8")
        try:
            details = json.loads(raw) if raw else {}
        except ValueError:
            details = {"message": raw}
        return error.code, details


def ensure_index():
    status, details = es_request("HEAD", "/photos")

    if status == 200:
        return
    if status != 404:
        raise RuntimeError(f"Index check failed: {status} {details}")

    mapping = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0
        },
        "mappings": {
            "properties": {
                "objectKey": {"type": "keyword"},
                "bucket": {"type": "keyword"},
                "createdTimestamp": {"type": "date"},
                "labels": {
                    "type": "text",
                    "analyzer": "english",
                    "fields": {
                        "raw": {"type": "keyword"}
                    }
                }
            }
        }
    }

    status, details = es_request("PUT", "/photos", mapping)
    error_type = (details.get("error") or {}).get("type")

    if status not in (200, 201):
        if error_type != "resource_already_exists_exception":
            raise RuntimeError(
                f"Index creation failed: {status} {details}"
            )


def lambda_handler(event, context):
    ensure_index()
    count = 0

    for record in event.get("Records", []):
        if record.get("eventSource") != "aws:s3":
            continue

        bucket = record["s3"]["bucket"]["name"]
        key = unquote_plus(record["s3"]["object"]["key"])

        metadata = s3.head_object(Bucket=bucket, Key=key)
        custom = metadata.get("Metadata", {}).get(
            "customlabels", ""
        ).split(",")

        detected = rekognition.detect_labels(
            Image={"S3Object": {"Bucket": bucket, "Name": key}},
            MaxLabels=100,
            MinConfidence=80
        )

        labels = custom + [
            label["Name"] for label in detected["Labels"]
        ]
        labels = list(dict.fromkeys(
            label.strip().lower()
            for label in labels
            if label.strip()
        ))

        document = {
            "objectKey": key,
            "bucket": bucket,
            "createdTimestamp": metadata["LastModified"].isoformat(),
            "labels": labels
        }

        document_id = hashlib.sha256(
            f"{bucket}/{key}".encode()
        ).hexdigest()

        path = f"/photos/_doc/{document_id}"

        status, result = es_request(
            "PUT",
            path + "?refresh=wait_for",
            document
        )

        if status not in (200, 201):
            raise RuntimeError(f"Indexing failed: {status} {result}")

        print("INDEXED_PHOTO:", json.dumps(result))

        status, stored = es_request("GET", path)

        if status != 200:
            raise RuntimeError(f"Read-back failed: {status} {stored}")

        print("STORED_PHOTO:", json.dumps(stored["_source"]))
        count += 1

    return {"indexed": count}
# Backend pipeline deployment verification v1

# Installed GitHub App trigger verification v2

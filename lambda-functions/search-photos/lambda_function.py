# Assignment 3 release demo: deployed automatically from GitHub main.
import json
import logging
import os
import re
import uuid
from urllib.parse import urlparse

import boto3
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

logger = logging.getLogger()
logger.setLevel(logging.INFO)

session = boto3.Session()
region = session.region_name or "us-east-1"
lex = session.client("lexv2-runtime")
s3 = session.client("s3")

endpoint = urlparse(os.environ["ES_ENDPOINT"])
auth = AWS4Auth(
    region=region,
    service="es",
    refreshable_credentials=session.get_credentials(),
)

es = Elasticsearch(
    hosts=[{"host": endpoint.hostname, "port": 443}],
    http_auth=auth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
    timeout=10,
    max_retries=1,
    retry_on_timeout=True,
)


def respond(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }


def literal_search_keywords(query):
    """Recover literal labels only after Lex recognizes SearchIntent."""
    text = " ".join(query.lower().strip().split()).strip(" .?!")
    text = re.sub(
        r"^(?:show me(?: (?:photos|pictures)(?: (?:with|of))?)?|"
        r"find(?: (?:photos|pictures)(?: (?:with|of))?)?|"
        r"(?:photos|pictures) (?:of|with))\s+",
        "", text,
    )
    text = re.sub(r"\s+in them$", "", text).strip()
    parts = re.split(r"\s+and\s+", text)
    if not 1 <= len(parts) <= 2:
        return []
    return list(dict.fromkeys(part for part in parts if part))


def extract_keywords(query):
    response = lex.recognize_text(
        botId=os.environ["LEX_BOT_ID"],
        botAliasId=os.environ["LEX_ALIAS_ID"],
        localeId="en_US",
        sessionId=str(uuid.uuid4()),
        text=query,
    )

    intent = response.get("sessionState", {}).get("intent", {})
    if intent.get("name") != "SearchIntent":
        return []

    slots = intent.get("slots") or {}
    keywords = []

    for name in ("KeywordOne", "KeywordTwo"):
        slot = slots.get(name) or {}
        value = slot.get("value") or {}
        keyword = (
            value.get("originalValue")
            or value.get("interpretedValue")
            or ""
        ).strip().lower()

        if keyword and keyword not in keywords:
            keywords.append(keyword)

    # Custom labels are open vocabulary: Lex may recognize the intent but
    # leave optional slots empty for labels absent from its training values.
    if not keywords:
        keywords = literal_search_keywords(query)
        logger.info("SEARCH_KEYWORD_SOURCE: literal SearchIntent recovery")

    logger.info("SEARCH_KEYWORDS: %s", json.dumps(keywords))
    return keywords


def search_photos(keywords):
    clauses = []
    for keyword in keywords:
        clauses.extend([
            {"term": {"labels.raw": keyword}},
            {"match_phrase": {"labels": keyword}},
        ])

    body = {
        "query": {
            "bool": {
                "filter": [
                    {"term": {"bucket": os.environ["PHOTO_BUCKET"]}}
                ],
                "should": clauses,
                "minimum_should_match": 1,
            }
        }
    }

    results = []
    seen = set()
    scroll_id = None

    try:
        page = es.search(
            index="photos",
            body=body,
            size=100,
            scroll="1m",
        )

        while True:
            scroll_id = page.get("_scroll_id") or scroll_id
            hits = page.get("hits", {}).get("hits", [])
            if not hits:
                break

            for hit in hits:
                photo = hit["_source"]
                bucket = photo["bucket"]
                key = photo["objectKey"]

                if bucket != os.environ["PHOTO_BUCKET"]:
                    continue
                if (bucket, key) in seen:
                    continue

                seen.add((bucket, key))
                url = s3.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": bucket, "Key": key},
                    ExpiresIn=3600,
                )
                results.append({
                    "url": url,
                    "labels": photo.get("labels", []),
                })

            if not scroll_id:
                break

            page = es.scroll(scroll_id=scroll_id, scroll="1m")
    finally:
        if scroll_id:
            try:
                es.clear_scroll(scroll_id=scroll_id)
            except Exception:
                logger.warning("Could not clear search scroll", exc_info=True)

    return results


def lambda_handler(event, context):
    params = event.get("queryStringParameters") or {}
    query = (params.get("q") or "").strip()

    if not query:
        return respond(200, {"results": []})

    if len(query) > 1000:
        return respond(400, {"message": "Search query is too long"})

    try:
        keywords = extract_keywords(query)
        if not keywords:
            return respond(200, {"results": []})

        results = search_photos(keywords)
        logger.info("SEARCH_RESULT_COUNT: %s", len(results))
        return respond(200, {"results": results})
    except Exception:
        logger.exception("Photo search failed")
        return respond(500, {"message": "Photo search failed"})
# Backend pipeline deployment verification v1

# Installed GitHub App trigger verification v2

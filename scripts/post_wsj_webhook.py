from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import requests


def _read_json_payloads(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if isinstance(payload, list):
        return [dict(item) for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        return [payload]
    raise ValueError("JSON input must be an object or list of objects")


def _read_jsonl_payloads(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            payload = json.loads(text)
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def _split_tickers(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [
        ticker.strip().upper()
        for ticker in str(value).split(",")
        if ticker.strip()
    ]


def _read_csv_payloads(path: Path) -> List[Dict[str, Any]]:
    payloads: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            headline = str(row.get("headline") or "").strip()
            if not headline:
                continue
            payloads.append(
                {
                    "headline": headline,
                    "tickers": _split_tickers(row.get("tickers")),
                    "article_id": row.get("article_id") or None,
                    "article_url": row.get("article_url") or None,
                    "author": row.get("author") or None,
                    "published_at": row.get("published_at") or None,
                }
            )
    return payloads


def load_payloads(path: Path) -> List[Dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return _read_json_payloads(path)
    if suffix == ".jsonl":
        return _read_jsonl_payloads(path)
    if suffix == ".csv":
        return _read_csv_payloads(path)
    raise ValueError("Supported formats are .json, .jsonl, and .csv")


def post_payloads(
    endpoint: str,
    payloads: Iterable[Dict[str, Any]],
    timeout: int,
) -> List[Dict[str, Any]]:
    responses: List[Dict[str, Any]] = []
    for payload in payloads:
        response = requests.post(endpoint, json=payload, timeout=timeout)
        response.raise_for_status()
        responses.append(response.json())
    return responses


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Post WSJ headline payloads to the Bentley /wsj-webhook endpoint",
    )
    parser.add_argument(
        "--file",
        required=True,
        help="Path to .json, .jsonl, or .csv payload file",
    )
    parser.add_argument(
        "--endpoint",
        default="http://127.0.0.1:8000/wsj-webhook",
        help="Webhook endpoint URL",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=20,
        help="Request timeout in seconds",
    )
    args = parser.parse_args()

    payload_file = Path(args.file)
    payloads = load_payloads(payload_file)
    responses = post_payloads(args.endpoint, payloads, timeout=args.timeout)
    print(json.dumps(responses, indent=2, default=str))


if __name__ == "__main__":
    main()
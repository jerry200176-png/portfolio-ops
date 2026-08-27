#!/usr/bin/env python3
"""Read-only post-deploy evidence check for a product's health and version endpoints."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


VERSION_KEYS = ("build_sha", "hash", "commit", "sha", "version")


def fetch_json(url: str, timeout: float = 15.0) -> tuple[int, dict[str, Any]]:
    """Fetch a JSON endpoint without printing its response body."""
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("endpoint must be an absolute http(s) URL")
    if parsed.username or parsed.password:
        raise ValueError("endpoint must not contain embedded credentials")

    request = Request(url, headers={"Accept": "application/json", "User-Agent": "portfolio-release-evidence/1"})
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - URL is an explicit operator input
            status = int(response.status)
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"endpoint returned HTTP {exc.code}") from exc
    except (URLError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise RuntimeError(f"endpoint read failed: {type(exc).__name__}") from exc

    if not isinstance(payload, dict):
        raise RuntimeError("endpoint returned a non-object JSON payload")
    return status, payload


def normalized(value: Any) -> str:
    return str(value or "").strip().lower()


def sha_matches(expected: str, candidate: Any) -> bool:
    wanted = normalized(expected)
    actual = normalized(candidate)
    if len(wanted) < 7 or not actual:
        return False
    return wanted == actual or wanted.startswith(actual) or actual.startswith(wanted)


def build_evidence(
    *,
    expected_sha: str,
    version_status: int,
    version_payload: dict[str, Any],
    health_status: int,
    health_payload: dict[str, Any],
    generated_at: str | None = None,
) -> dict[str, Any]:
    version_candidates = [
        {"key": key, "value": version_payload.get(key)}
        for key in VERSION_KEYS
        if version_payload.get(key) not in (None, "")
    ]
    matched = next(
        (candidate for candidate in version_candidates if sha_matches(expected_sha, candidate["value"])),
        None,
    )
    health_ok = health_payload.get("status") == "ok" or health_payload.get("ok") is True
    evidence = {
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(),
        "expected_sha": normalized(expected_sha),
        "version": {
            "http_status": version_status,
            "candidates": version_candidates,
            "matched": matched,
        },
        "health": {
            "http_status": health_status,
            "ok": health_ok,
        },
    }
    evidence["passed"] = version_status == 200 and health_status == 200 and health_ok and matched is not None
    return evidence


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version-url", required=True)
    parser.add_argument("--health-url", required=True)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)

    try:
        version_status, version_payload = fetch_json(args.version_url, args.timeout)
        health_status, health_payload = fetch_json(args.health_url, args.timeout)
        evidence = build_evidence(
            expected_sha=args.expected_sha,
            version_status=version_status,
            version_payload=version_payload,
            health_status=health_status,
            health_payload=health_payload,
        )
    except (RuntimeError, ValueError) as exc:
        print(f"release evidence failed: {exc}", file=sys.stderr)
        return 2

    output = json.dumps(evidence, ensure_ascii=False, indent=2) + "\n"
    if args.json_out:
        args.json_out.write_text(output, encoding="utf-8")
    print(f"Release evidence: {'PASS' if evidence['passed'] else 'FAIL'}")
    print(f"Expected serving SHA: `{evidence['expected_sha']}`")
    print(f"Health: HTTP {evidence['health']['http_status']}, ok={evidence['health']['ok']}")
    print(f"Version match: {'yes' if evidence['version']['matched'] else 'no'}")
    return 0 if evidence["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

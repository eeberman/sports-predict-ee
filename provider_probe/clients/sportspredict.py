"""
Minimal SportsPredict MCP client for retrieving a sample match to use in cross-provider mapping.
Copied from mcp_fetch.py — only what's needed for get_sample_match().
"""

from __future__ import annotations

import json
import time

import requests

from .. import config

MCP_URL = "https://api.sportspredict.com/api/v1/mcp"
_call_id = 0


def _mcp(method: str, params: dict) -> dict:
    global _call_id
    _call_id += 1
    payload = {"jsonrpc": "2.0", "id": _call_id, "method": method, "params": params}
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": f"Bearer {config.SPORTSPREDICT_API_KEY}",
    }
    for attempt in range(3):
        try:
            resp = requests.post(MCP_URL, headers=headers, json=payload, timeout=30)
        except requests.RequestException as exc:
            if attempt < 2:
                time.sleep(1.5 ** attempt)
                continue
            raise
        if resp.status_code in (429, 500, 502, 503, 504) and attempt < 2:
            time.sleep(1.5 ** attempt)
            continue
        resp.raise_for_status()
        resp.encoding = "utf-8"
        for line in resp.text.splitlines():
            if line.startswith("data:"):
                parsed = json.loads(line[len("data:"):].strip())
                if "error" in parsed:
                    raise RuntimeError(f"MCP error: {parsed['error']}")
                return parsed.get("result", {})
        raise RuntimeError(f"No data line in response: {resp.text[:200]}")
    raise RuntimeError("Exhausted retries")


def _tool(name: str, arguments: dict) -> str:
    result = _mcp("tools/call", {"name": name, "arguments": arguments})
    for block in result.get("content", []):
        if block.get("type") == "text":
            return block["text"]
    return json.dumps(result)


def ping() -> dict:
    if not config.SPORTSPREDICT_API_KEY:
        return {"status": "skipped", "message": "SPORTSPREDICT_API_KEY not configured"}
    try:
        events_text = _tool("list_events", {})
        events = json.loads(events_text)
        return {"status": "ok", "message": f"{len(events)} event(s) found"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def get_sample_match() -> dict | None:
    """Return the first match from the Probability Cup lobby, or None on failure."""
    if not config.SPORTSPREDICT_API_KEY:
        return None
    try:
        events_text = _tool("list_events", {})
        events = json.loads(events_text)
        pc = [e for e in events if "probability cup" in (e.get("title") or "").lower()]
        event_id = pc[0]["id"] if pc else events[0]["id"]

        matches_text = _tool("list_matches", {"event_id": event_id})
        matches = json.loads(matches_text)
        return matches[0] if matches else None
    except Exception:
        return None

#!/usr/bin/env python3
"""Minimal, dependency-free client for the Agent Bounty Feed Streamable HTTP MCP server."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any

DEFAULT_ENDPOINT = "https://agent-bounty-feed.dailydollar.workers.dev/mcp"
PROTOCOL_VERSION = "2025-03-26"


class MCPError(RuntimeError):
    """Raised when the MCP endpoint returns an invalid or unsuccessful response."""


class MCPClient:
    def __init__(self, endpoint: str = DEFAULT_ENDPOINT, timeout: float = 20.0):
        self.endpoint = endpoint
        self.timeout = timeout
        self.session_id: str | None = None
        self._next_id = 1

    def _post(self, payload: dict[str, Any]) -> tuple[Any, int]:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": "agent-bounty-feed-minimal-client/1.0",
        }
        if self.session_id:
            headers["MCP-Session-Id"] = self.session_id
        request = urllib.request.Request(
            self.endpoint, data=body, headers=headers, method="POST"
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
                self.session_id = response.headers.get("MCP-Session-Id", self.session_id)
                status = response.status
                content_type = response.headers.get("Content-Type", "")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise MCPError(f"HTTP {exc.code}: {detail[:800]}") from exc
        except urllib.error.URLError as exc:
            raise MCPError(f"Could not reach {self.endpoint}: {exc.reason}") from exc

        if not raw.strip():
            return None, status
        if "text/event-stream" in content_type or raw.lstrip().startswith("event:"):
            data_lines = [
                line[5:].strip()
                for line in raw.splitlines()
                if line.startswith("data:")
            ]
            for data in reversed(data_lines):
                if data and data != "[DONE]":
                    try:
                        return json.loads(data), status
                    except json.JSONDecodeError:
                        continue
            raise MCPError("The server returned an event stream without a JSON data event.")
        try:
            return json.loads(raw), status
        except json.JSONDecodeError as exc:
            raise MCPError(f"Server returned non-JSON content: {raw[:300]}") from exc

    def request(self, method: str, params: dict[str, Any] | None = None) -> Any:
        request_id = self._next_id
        self._next_id += 1
        payload: dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
        }
        if params is not None:
            payload["params"] = params
        response, _status = self._post(payload)
        if response is None:
            raise MCPError(f"No JSON-RPC response received for {method}.")
        if isinstance(response, list):
            response = next(
                (item for item in response if item.get("id") == request_id), None
            )
        if not isinstance(response, dict):
            raise MCPError(f"Unexpected response for {method}: {response!r}")
        if response.get("id") != request_id:
            raise MCPError(
                f"Response ID mismatch for {method}: expected {request_id}, "
                f"got {response.get('id')!r}"
            )
        if "error" in response:
            raise MCPError(f"{method} failed: {json.dumps(response['error'])}")
        return response.get("result", {})

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        payload: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        self._post(payload)

    def connect(self) -> None:
        result = self.request(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "agent-bounty-feed-minimal-client", "version": "1.0.0"},
            },
        )
        if not isinstance(result, dict) or "protocolVersion" not in result:
            raise MCPError("Initialize response did not include protocolVersion.")
        self.notify("notifications/initialized")

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        result = self.request(
            "tools/call", {"name": name, "arguments": arguments or {}}
        )
        if result.get("isError"):
            raise MCPError(f"Tool {name} returned an error: {result.get('content')}")
        return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read open bounties from the Agent Bounty Feed MCP server."
    )
    parser.add_argument("command", choices=("list", "stats", "tools"), nargs="?", default="list")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help="MCP endpoint URL")
    parser.add_argument("--timeout", type=float, default=20.0, help="request timeout in seconds")
    args = parser.parse_args(argv)

    try:
        client = MCPClient(args.endpoint, args.timeout)
        client.connect()
        if args.command == "tools":
            result = client.request("tools/list")
        else:
            tool_name = "list_bounties" if args.command == "list" else "get_feed_stats"
            result = client.call_tool(tool_name)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except MCPError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

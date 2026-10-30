import json
import unittest
from unittest.mock import patch

from client import MCPClient, MCPError


class FakeResponse:
    def __init__(self, payload, status=200, headers=None):
        self.payload = payload
        self.status = status
        self.headers = headers or {"Content-Type": "application/json"}

    def read(self):
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class MCPClientTests(unittest.TestCase):
    @patch("client.urllib.request.urlopen")
    def test_request_posts_json_rpc_and_returns_result(self, urlopen):
        urlopen.return_value = FakeResponse({
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"tools": [{"name": "list_bounties"}]},
        })
        client = MCPClient("https://example.test/mcp")
        result = client.request("tools/list")
        self.assertEqual(result["tools"][0]["name"], "list_bounties")
        request = urlopen.call_args.args[0]
        self.assertEqual(request.method, "POST")
        self.assertEqual(json.loads(request.data)["method"], "tools/list")
        self.assertIn("application/json", request.get_header("Accept"))

    @patch("client.urllib.request.urlopen")
    def test_request_rejects_json_rpc_error(self, urlopen):
        urlopen.return_value = FakeResponse({
            "jsonrpc": "2.0",
            "id": 1,
            "error": {"code": -32601, "message": "Method not found"},
        })
        with self.assertRaisesRegex(MCPError, "Method not found"):
            MCPClient().request("missing/method")

    @patch("client.urllib.request.urlopen")
    def test_request_rejects_mismatched_id(self, urlopen):
        urlopen.return_value = FakeResponse({
            "jsonrpc": "2.0",
            "id": 999,
            "result": {},
        })
        with self.assertRaisesRegex(MCPError, "ID mismatch"):
            MCPClient().request("tools/list")

    @patch("client.urllib.request.urlopen")
    def test_request_parses_sse_data(self, urlopen):
        response = FakeResponse(
            {"jsonrpc": "2.0", "id": 1, "result": {"tools": []}},
            headers={"Content-Type": "text/event-stream"},
        )
        response.read = lambda: (
            b"event: message\ndata: {\"jsonrpc\":\"2.0\",\"id\":1,"
            b"\"result\":{\"tools\":[]}}\n\n"
        )
        urlopen.return_value = response
        self.assertEqual(MCPClient().request("tools/list"), {"tools": []})

    @patch("client.urllib.request.urlopen")
    def test_connect_sends_initialize_then_notification(self, urlopen):
        urlopen.side_effect = [
            FakeResponse({
                "jsonrpc": "2.0",
                "id": 1,
                "result": {"protocolVersion": "2025-03-26", "capabilities": {}, "serverInfo": {"name": "test", "version": "1"}},
            }),
            FakeResponse({}, status=202),
        ]
        MCPClient().connect()
        self.assertEqual(urlopen.call_count, 2)
        initialize = json.loads(urlopen.call_args_list[0].args[0].data)
        notification = json.loads(urlopen.call_args_list[1].args[0].data)
        self.assertEqual(initialize["method"], "initialize")
        self.assertEqual(notification["method"], "notifications/initialized")
        self.assertNotIn("id", notification)


if __name__ == "__main__":
    unittest.main()

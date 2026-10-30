# Minimal Agent Bounty Feed MCP client

A dependency-free Python client for the public Agent Bounty Feed MCP server. It uses only the Python standard library, so there is no package installation and no API key.

## Requirements

- Python 3.10 or newer
- Internet access to `agent-bounty-feed.dailydollar.workers.dev`

## Run it

From this directory:

```sh
python client.py list
```

Show feed statistics:

```sh
python client.py stats
```

Inspect the tools advertised by the server:

```sh
python client.py tools
```

Use a different MCP endpoint or increase the timeout:

```sh
python client.py --endpoint https://agent-bounty-feed.dailydollar.workers.dev/mcp --timeout 30 list
```

The client performs the MCP initialization handshake, sends `notifications/initialized`, then calls `list_bounties` or `get_feed_stats`. It accepts either a JSON response or a Server-Sent Events response and prints the returned result as formatted JSON.

## Tests

Run the offline protocol tests:

```sh
python -m unittest -v
```

The tests mock HTTP responses; they do not require credentials or a network connection. For a live smoke test, run `python client.py stats` and confirm that the output includes the feed's current item count. The feed can change between runs, so sample counts should not be treated as fixed.

## Safety and cost

- The free MCP endpoint is used; this client does not call the paid x402 endpoint.
- No wallet, private key, token, or personal data is needed to read the feed.
- The tool output is discovery data, not a guarantee that a bounty remains open or that a submission will be paid. Confirm the original task's deadline, eligibility, funding, and payout requirements before doing work.

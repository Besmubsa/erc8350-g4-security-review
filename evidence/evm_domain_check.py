#!/usr/bin/env python3
"""Deploy compiled AgentMemoryStateRegistry bytecode on py-evm and call
computeDomainSeparator / computeSigningDigest / typehash getters.
Settles the golden-vector eip712 question with real EVM execution."""
import json, subprocess, sys
from eth_tester import EthereumTester, PyEVMBackend

REPO = "/home/z/my-project/bugbounty/repos/erc8350"
SOLC = "/tmp/solc"

# 1) compile
r = subprocess.run(
    [SOLC, "--bin", "--optimize", "--optimize-runs", "200", "--evm-version", "cancun",
     "--allow-paths", REPO,
     f"{REPO}/contracts/src/reference/AgentMemoryStateRegistry.sol"],
    capture_output=True, text=True)
if r.returncode != 0:
    print("SOLC ERR:", r.stderr[:2000]); sys.exit(1)
# parse bin from stdout: lines "======= file:Contract =======" then "Binary:" hex
lines = r.stdout.splitlines()
bincode = None
for i, l in enumerate(lines):
    if "AgentMemoryStateRegistry" in l and l.startswith("======="):
        for j in range(i + 1, min(i + 8, len(lines))):
            if lines[j].strip().startswith("Binary:"):
                # hex may be on same line or next non-empty line
                parts = lines[j].split()
                bincode = parts[1] if len(parts) > 1 else lines[j + 1].strip()
                break
        break
assert bincode, "no bytecode parsed"

# 2) deploy on py-evm
backend = PyEVMBackend()
t = EthereumTester(backend)
acct = backend.get_accounts()[0]
acct = acct.hex() if isinstance(acct, bytes) else str(acct)
if not acct.startswith("0x"): acct = "0x" + acct
tx = t.send_transaction({"from": acct, "data": "0x" + bincode, "gas": 3_000_000, "gas_price": 1_000_000_000})
addr = t.get_transaction_receipt(tx)["contract_address"]
addr = addr.hex() if isinstance(addr, bytes) else str(addr)
if not addr.startswith("0x"): addr = "0x" + addr
print("deployed at:", addr)

# 3) call computeDomainSeparator(1, 0x4444...)
def call(selector, args_hex):
    data = "0x" + selector + args_hex
    return t.call({"from": acct, "to": addr, "data": data, "gas": 1_000_000})["raw_log"]["output"][2:] if False else t.call({"from": acct, "to": addr, "data": data, "gas": 1_000_000})

from eth_utils import keccak
def sel(sig): return keccak(text=sig)[:4].hex()

def callout(res):
    if isinstance(res, str):
        return res[2:] if res.startswith("0x") else res
    if isinstance(res, dict):
        out = res.get("raw_log", {}).get("output") if isinstance(res.get("raw_log"), dict) else None
        if out is None:
            out = res.get("output")
        if isinstance(out, str):
            return out[2:] if out.startswith("0x") else out
        if isinstance(out, bytes):
            return out.hex()
    return res

out_dom = callout(t.call({"from": acct, "to": addr, "data": "0x" + sel("computeDomainSeparator(uint256,address)") + (1).to_bytes(32, "big").hex() + ("00"*12 + "44"*20), "gas": 1_000_000}))
print("computeDomainSeparator(1, 0x4444..):", "0x" + out_dom)

res_t = t.call({"from": acct, "to": addr, "data": "0x" + sel("EXPERIENCE_DELTA_TYPEHASH()"), "gas": 100_000})
print("EXPERIENCE_DELTA_TYPEHASH():", "0x" + callout(res_t))

# compare
v = json.load(open(f"{REPO}/test-vectors/v1.json"))
e = v["eip712"]
print("vector domainSeparator        :", e["domainSeparator"])
print("MATCH vs vector:", out_dom == e["domainSeparator"][2:])
print("NOTE: independent Python recompute (with correct address padding) matches the vector; see vector_recompute_output.txt")

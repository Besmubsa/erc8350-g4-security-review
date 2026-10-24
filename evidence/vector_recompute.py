#!/usr/bin/env python3
"""ERC-8350 G4 review methodology: independent golden-vector verification in Python.
Recomputes commitment, typehashes, transitionId, nextStateRoot, EIP-712 digest
from test-vectors/v1.json WITHOUT using project code (pure hashlib)."""
import json, hashlib

REPO = "/home/z/my-project/bugbounty/repos/erc8350"
v = json.load(open(f"{REPO}/test-vectors/v1.json"))

def h(b): return hashlib.sha256(b).digest()
def kec(b):
    # keccak256 via pycryptodome / sha3 fallback
    try:
        from Crypto.Hash import keccak
        k = keccak.new(digest_bits=256); k.update(b); return k.digest()
    except ImportError:
        import sha3
        return sha3.keccak_256(b).digest()

def to_bytes(s):
    if isinstance(s, str):
        if s.startswith("0x"): return bytes.fromhex(s[2:])
        return s.encode()
    return s

def addr(a): return bytes.fromhex(a[2:].rjust(40, "0"))

ok = True
def check(name, got, exp):
    global ok
    same = got == exp
    ok &= same
    print(f"{'PASS' if same else 'FAIL'} {name}: {('0x'+got.hex())[:70]}")

# --- 1. deltaCommitment ---
c = v["commitment"]
payload_hash = kec(to_bytes(c["payload"]))
delta_commitment = kec(
    kec(b"AgentMemoryState.deltaCommitment.v1") + to_bytes(c["profileId"]) + to_bytes(c["deltaSalt"]) + payload_hash
)
check("deltaCommitment", delta_commitment, to_bytes(c["deltaCommitment"]))

# --- 2. ExperienceDelta typehash + transitionId ---
d = v["delta"]
types = v["types"]
exp_typehash = kec(types["experienceDelta"].encode())
print("experienceDelta typehash string:", types["experienceDelta"])

sequence = int(d["sequence"]) if isinstance(d.get("sequence"), (str, int)) else None
seq_b = sequence.to_bytes(32, "big")  # abi.encode pads uint64 to 32 bytes

struct = (
    exp_typehash
    + to_bytes(d["spaceId"])
    + seq_b
    + to_bytes(d["prevStateRoot"])
    + to_bytes(d["deltaCommitment"])
    + to_bytes(d["provenanceCommitment"])
    + to_bytes(d["profileId"])
    + to_bytes(d["locatorCommitment"])
)
transition_id = kec(struct)
check("transitionId", transition_id, to_bytes(v["expected"]["transitionId"]))

# --- 3. nextStateRoot ---
ms_typehash = kec(types["memoryState"].encode())
next_root = kec(ms_typehash + to_bytes(d["prevStateRoot"]) + transition_id)
check("nextStateRoot", next_root, to_bytes(v["expected"]["nextStateRoot"]))

# --- 4. EIP-712 domain separator + signing digest ---
e = v["eip712"]
dom_typehash = kec(b"EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)")
name_h = kec(b"AgentMemoryState")
ver_h = kec(b"1")
chain_id = int(e["chainId"]).to_bytes(32, "big")
contract = addr(e["verifyingContract"]).rjust(32, b"\x00")  # address = 20 bytes, LEFT-padded to ABI word
domain = kec(dom_typehash + name_h + ver_h + chain_id + contract)
check("domainSeparator", domain, to_bytes(e["domainSeparator"]))

digest = kec(b"\x19\x01" + domain + transition_id)
check("signingDigest", digest, to_bytes(e["signingDigest"]))

# --- 0. typehashes from expected ---
check("experienceDeltaTypehash", exp_typehash, to_bytes(v["expected"]["experienceDeltaTypehash"]))
check("memoryStateTypehash", ms_typehash, to_bytes(v["expected"]["memoryStateTypehash"]))
ms_typehash2 = kec(types["memorySpace"].encode())
check("memorySpaceTypehash", ms_typehash2, to_bytes(v["expected"]["memorySpaceTypehash"]))

# --- 5. spaceId derivation + registration/authorization struct hashes ---
sa = v.get("spaceAuthorization", {})
if sa:
    space_id = kec(ms_typehash2 + addr(sa["controller"]).rjust(32, b"\x00") + to_bytes(sa["spaceSalt"]))
    reg_typehash = kec(b"SpaceRegistration(bytes32 spaceId,address controller,address authorizer)")
    registration_id = kec(reg_typehash + space_id + addr(sa["controller"]).rjust(32, b"\x00")
                          + addr(sa["authorizer"]).rjust(32, b"\x00"))
    check("spaceId (via registrationId)", registration_id, to_bytes(sa["registrationId"]))
    auth_typehash = kec(b"SpaceAuthorization(bytes32 spaceId,address newController,address newAuthorizer,uint64 nonce)")
    nonce = int(sa["updateNonce"])
    authorization_id = kec(auth_typehash + space_id + addr(sa["controller"]).rjust(32, b"\x00")
                           + addr(sa["authorizer"]).rjust(32, b"\x00") + nonce.to_bytes(32, "big"))
    check("authorizationId", authorization_id, to_bytes(sa["authorizationId"]))

print("\nRESULT:", "ALL VECTORS PASS" if ok else "MISMATCH FOUND")

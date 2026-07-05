#!/usr/bin/env python3
"""
sign-drop.py — Sign an LTP drop JSON file with Ed25519.

Usage:
    python sign-drop.py <input.json> [output.json]

If output.json is omitted, the signed drop is written back to input.json.

Reads the Ed25519 private key from tools/ltp-publisher.key (relative to repo root).
Computes prev_drop_hash if not already set.
"""

import json
import sys
import hashlib
import base64
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import load_pem_private_key


REPO_ROOT = Path(__file__).resolve().parent.parent
PRIVATE_KEY_PATH = REPO_ROOT / "tools" / "ltp-publisher.key"


def canonical_json(obj: dict) -> str:
    """Serialize to canonical JSON: sorted keys, no whitespace."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def load_private_key() -> Ed25519PrivateKey:
    pem_bytes = PRIVATE_KEY_PATH.read_bytes()
    key = load_pem_private_key(pem_bytes, password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise TypeError("Key is not Ed25519")
    return key


def compute_genesis_hash() -> str:
    """SHA-256 of the UTF-8 string 'LTP-GENESIS-DROP'."""
    return hashlib.sha256(b"LTP-GENESIS-DROP").hexdigest()


def sign_drop(drop: dict, private_key: Ed25519PrivateKey) -> dict:
    """Sign a drop dict in place and return it."""
    # If this is sequence 1 and prev_drop_hash is missing or placeholder, set genesis
    if drop.get("sequence") == 1 and not drop.get("prev_drop_hash"):
        drop["prev_drop_hash"] = compute_genesis_hash()

    # Remove signature field for signing payload
    drop_for_signing = {k: v for k, v in drop.items() if k != "signature"}
    payload = canonical_json(drop_for_signing).encode("utf-8")

    # Sign
    sig_bytes = private_key.sign(payload)
    drop["signature"] = base64.b64encode(sig_bytes).decode("ascii")

    return drop


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <input.json> [output.json]", file=sys.stderr)
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else input_path

    drop = json.loads(input_path.read_text("utf-8"))
    private_key = load_private_key()
    signed_drop = sign_drop(drop, private_key)

    output_path.write_text(
        json.dumps(signed_drop, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    print(f"Signed drop written to {output_path}")
    print(f"  sequence: {signed_drop.get('sequence')}")
    print(f"  signature: {signed_drop['signature'][:40]}...")
    print(f"  prev_drop_hash: {signed_drop.get('prev_drop_hash', 'N/A')}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
verify-drop.py — Verify the Ed25519 signature on an LTP drop JSON file.

Usage:
    python verify-drop.py <drop.json>

Reads the Ed25519 public key from public/keys/ltp-publisher.pub (relative to repo root).
Strips comment lines (starting with #) from the PEM file before parsing.
"""

import json
import sys
import base64
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.exceptions import InvalidSignature


REPO_ROOT = Path(__file__).resolve().parent.parent
PUBLIC_KEY_PATH = REPO_ROOT / "public" / "keys" / "ltp-publisher.pub"


def canonical_json(obj: dict) -> str:
    """Serialize to canonical JSON: sorted keys, no whitespace."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def load_public_key() -> Ed25519PublicKey:
    raw = PUBLIC_KEY_PATH.read_text("utf-8")
    # Strip comment lines (lines starting with #)
    pem_lines = [line for line in raw.splitlines() if not line.startswith("#")]
    pem_bytes = "\n".join(pem_lines).strip().encode("utf-8")
    key = load_pem_public_key(pem_bytes)
    if not isinstance(key, Ed25519PublicKey):
        raise TypeError("Key is not Ed25519")
    return key


def verify_drop(drop: dict, public_key: Ed25519PublicKey) -> bool:
    """Verify the signature on a drop. Returns True if valid, False otherwise."""
    signature_b64 = drop.get("signature")
    if not signature_b64:
        print("ERROR: Drop has no 'signature' field.", file=sys.stderr)
        return False

    # Remove signature field for verification payload
    drop_for_verify = {k: v for k, v in drop.items() if k != "signature"}
    payload = canonical_json(drop_for_verify).encode("utf-8")

    try:
        sig_bytes = base64.b64decode(signature_b64)
    except Exception as e:
        print(f"ERROR: Could not decode base64 signature: {e}", file=sys.stderr)
        return False

    try:
        public_key.verify(sig_bytes, payload)
        return True
    except InvalidSignature:
        return False


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <drop.json>", file=sys.stderr)
        sys.exit(1)

    input_path = Path(sys.argv[1])
    drop = json.loads(input_path.read_text("utf-8"))
    public_key = load_public_key()

    if verify_drop(drop, public_key):
        print(f"VALID: Signature verified for {input_path}")
        print(f"  drop_date: {drop.get('drop_date')}")
        print(f"  sequence:  {drop.get('sequence')}")
        sys.exit(0)
    else:
        print(f"INVALID: Signature verification FAILED for {input_path}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

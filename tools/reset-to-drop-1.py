#!/usr/bin/env python3
"""Reset the current latest.json to Drop #1.

Run on VPS where the signing key lives:
    cd /docker/ltp-drop && python3 tools/reset-to-drop-1.py

This re-signs the current drop with:
  - sequence: 1
  - tuning_day: computed from LT start date (Feb 8, 2026)
  - prev_drop_hash: GENESIS_HASH
Then cleans the old sample archive and pushes.
"""

import json
import hashlib
import base64
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path("/docker/ltp-drop")
LATEST = REPO / "public" / "latest.json"
KEY_PATH = REPO / "tools" / "ltp-publisher.key"
GENESIS_HASH = hashlib.sha256(b"LTP-GENESIS-DROP").hexdigest()
LT_START = datetime(2026, 2, 8, tzinfo=ZoneInfo("America/New_York"))


def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sign(payload_bytes):
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    key = load_pem_private_key(KEY_PATH.read_bytes(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise TypeError("Not Ed25519")
    return base64.b64encode(key.sign(payload_bytes)).decode("ascii")


def main():
    drop = json.loads(LATEST.read_text("utf-8"))

    print(f"Current: Drop #{drop['sequence']}, {drop['drop_date']}")
    print(f"  Frequency: {drop['frequency']['name']}")
    print(f"  Principle: {drop['tuning_key']['source_song']}")

    # Compute tuning day
    drop_dt = datetime.strptime(drop["drop_date"], "%Y-%m-%d").replace(tzinfo=ZoneInfo("America/New_York"))
    tuning_day = (drop_dt.replace(hour=0) - LT_START.replace(hour=0)).days + 1

    # Reset sequence and chain
    drop["sequence"] = 1
    drop["tuning_day"] = tuning_day
    drop["prev_drop_hash"] = GENESIS_HASH

    # Remove old signature, re-sign
    drop.pop("signature", None)
    payload = canonical_json(drop).encode("utf-8")
    drop["signature"] = sign(payload)

    # Write latest.json
    drop_json = json.dumps(drop, indent=2, ensure_ascii=True) + "\n"
    LATEST.write_text(drop_json, encoding="utf-8")

    # Write to correct archive slot
    year, month, day = drop["drop_date"].split("-")
    archive_dir = REPO / "public" / "drops" / year / month
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_path = archive_dir / f"{day}.json"
    archive_path.write_text(drop_json, encoding="utf-8")

    # Clean old sample drop archive entries (anything not today)
    drops_root = REPO / "public" / "drops"
    if drops_root.exists():
        for ydir in drops_root.iterdir():
            if not ydir.is_dir():
                continue
            for mdir in ydir.iterdir():
                if not mdir.is_dir():
                    continue
                for f in mdir.iterdir():
                    if f.name.endswith(".json") and f != archive_path:
                        print(f"  Removing old archive: {f.relative_to(REPO)}")
                        f.unlink()
                # Remove empty month dirs
                if not any(mdir.iterdir()):
                    mdir.rmdir()
            # Remove empty year dirs
            if not any(ydir.iterdir()):
                ydir.rmdir()

    print(f"\nReset to Drop #1 (tuning day {tuning_day})")
    print(f"  prev_drop_hash: GENESIS")
    print(f"  signature: {drop['signature'][:32]}...")
    print(f"\nNext: git add + commit + push")


if __name__ == "__main__":
    main()

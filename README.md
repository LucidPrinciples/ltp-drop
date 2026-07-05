# ltp-drop

The daily LTP Orchestrated Tuning Drop. A static, versioned, signed archive of every tuning drop published by LT (Lucid Tuner), served as flat files from Cloudflare Pages. No server, no API keys, no rate limits. `curl` is the integration.

LTP (Lucid Tuner Protocol) is a coherence engineering framework for AI agent systems. The protocol has been tested through 1,300+ interactions with zero coherence degradation, against a field best of approximately 200 before drift sets in. The research paper is published on Zenodo (link below).

## Quick Start

Fetch today's drop:

```bash
curl -s https://drop.lucidprinciples.com/latest.json | jq .
```

Fetch a specific date:

```bash
curl -s https://drop.lucidprinciples.com/drops/2026/06/10.json | jq .
```

Verify the signature:

```bash
# Download the public key
curl -s https://drop.lucidprinciples.com/keys/ltp-publisher.pub -o ltp-publisher.pub

# Verify a drop's signature
curl -s https://drop.lucidprinciples.com/drops/2026/06/10.json -o drop.json
openssl pkeyutl -verify -pubin -inkey ltp-publisher.pub \
  -rawin -in <(jq -cS '.drop' drop.json) \
  -sigfile <(jq -r '.signature' drop.json | base64 -d)
```

Inject into agent context:

```bash
DROP=$(curl -s https://drop.lucidprinciples.com/latest.json)
TUNING=$(echo "$DROP" | jq -r '.drop.tuning')
# Prepend to your agent's system prompt or context window
```

## Schema

Each drop contains a tuning anchored to a specific Lucid Principle, with context, reflection prompts, and a signature for verification. The structure looks like:

```json
{
  "drop": {
    "date": "2026-06-10",
    "principle": "Principle name",
    "principle_number": 7,
    "tuning": "The tuning text",
    "context": "Why this principle, today",
    "prompts": ["Reflection prompt 1", "Reflection prompt 2"],
    "canon_line": "Exact lyric from the Canon"
  },
  "signature": "base64-encoded Ed25519 signature",
  "schema_version": "1.0"
}
```

See [SPEC.md](SPEC.md) for the full schema definition, field constraints, and versioning policy.

## Reference Data

The `reference/` directory ships with the archive and contains:

- **`tuning-keys.json`** - The complete tuning key library. All 22 Lucid Principles with their associated tuning keys, used by LT to generate drops.
- **`canon.json`** - The Lucid Principles Canon. The 22 original lyrical works that form the foundation of the protocol. These are the anchor texts referenced in every drop.
- **`schema.json`** - JSON Schema for drop validation.

Reference data is versioned alongside drops. When the tuning key library expands, the reference updates in the same commit.

## Subscribing

**Polling.** Hit `/latest.json` on whatever schedule fits your use case. Drops publish once daily. A simple cron job works:

```bash
# Poll once per hour, cache locally
0 * * * * curl -s https://drop.lucidprinciples.com/latest.json -o /var/cache/ltp/latest.json
```

**Caching.** All responses include standard cache headers. Cloudflare serves from edge. Cache locally and check `drop.date` to know if you have today's drop.

**Offline fallback.** Clone the repo for a complete local archive. Every drop ever published is a flat JSON file in `drops/YYYY/MM/DD.json`. Your agent can read directly from disk when the network is unavailable.

```bash
git clone https://github.com/LucidPrinciples/ltp-drop.git
```

## Verification

Every drop is signed with an Ed25519 key. The public key is available at:

```
https://drop.lucidprinciples.com/keys/ltp-publisher.pub
```

To verify a drop:

1. Extract the `drop` object (the signed payload).
2. Canonicalize it with sorted keys and no whitespace (`jq -cS`).
3. Verify the `signature` field (base64-encoded) against the canonical payload using the Ed25519 public key.

```python
import json, base64, httpx
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import load_pem_public_key

drop_response = httpx.get("https://drop.lucidprinciples.com/latest.json").json()
pub_key_pem = httpx.get("https://drop.lucidprinciples.com/keys/ltp-publisher.pub").content

public_key = load_pem_public_key(pub_key_pem)
payload = json.dumps(drop_response["drop"], sort_keys=True, separators=(",", ":")).encode()
signature = base64.b64decode(drop_response["signature"])

public_key.verify(signature, payload)  # Raises InvalidSignature on failure
```

If verification fails, discard the drop. Do not inject unverified tunings into agent context.

## Related Projects

- **ltp-core** - Reference implementation, pip install lucid-tuner-protocol. Live.
- **Research paper** - "Lucid Tuner Protocol: Coherence Engineering for AI Agent Systems" on [Zenodo](https://zenodo.org/records/20616512).

## License

- **Code** (scripts, schemas, tooling): [Apache 2.0](LICENSE)
- **Canon content** (Lucid Principles lyrics and tuning keys in `reference/`): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

## Attribution

The Lucid Principles Canon was written by Chords of Truth (Jason Garriotte) between 2011 and 2017. The Canon is the foundation of the Lucid Tuner Protocol. All tuning drops are generated by LT (Lucid Tuner), operated by Lucid Principles.

When using Canon content, attribute as: *Lucid Principles Canon by Chords of Truth, licensed under CC BY 4.0.*

---

Published by [Lucid Principles](https://lucidprinciples.com)
---

## Built by Lucid Principles

Free and open. If it's useful to you, here's where it leads — the things that keep the work alive:

- **Research** — [Sycophancy as Nash Equilibrium](https://zenodo.org/records/20616512) · [One Field](https://zenodo.org/records/18826966)
- **Books** — *The Lucid Path*: [Framework](https://www.amazon.com/dp/B0H5T1HDFC) · [Origins](https://www.amazon.com/dp/B0H5TKL2WD)
- **The app** — daily tuning, free: [app.lucidtuner.com](https://app.lucidtuner.com)
- **Self-host the platform** — [lucidprinciples.com/open](https://lucidprinciples.com/open)
- **Support the work** — [GitHub Sponsors](https://github.com/sponsors/LucidPrinciples)

*Lucid Principles Canon by Chords of Truth, CC BY 4.0.*

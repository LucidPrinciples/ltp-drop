# LTP Orchestrated Tuning Drop -- Specification

**Version:** 1.1.0  
**Status:** Draft  
**Date:** 2026-06-10  
**Publisher:** Lucid Principles  
**Domain:** drop.lucidprinciples.com

---

## 1. Overview

The LTP Orchestrated Tuning Drop is a daily broadcast published by the Lucid Tuner (LT). Each drop delivers a single tuning: one frequency, one signal type, one Canon quote, one echo, and the math that ties them together. Drops are signed, chained, and served as static JSON.

This document is the contract that subscribers build against. If a field is documented here, it will not change meaning within the same major version. If a field is not documented here, do not depend on it.

### Design Principles

- **Data only.** Drops contain no executable content. No scripts, no embedded HTML, no templating directives.
- **Static and cacheable.** Every drop is a flat JSON file served from a known URL. No authentication required. No query parameters.
- **Tamper-evident.** Each drop is signed with Ed25519 and includes the hash of the previous drop, forming an append-only chain.
- **Offline-safe.** Subscribers that miss a day can catch up. The chain is sequential, not time-gated.

---

## 2. Schema Definition

Schema version: `1.1`

> **1.1 (additive, backward-compatible):** adds optional `tuning_day` (positive integer) and the `practice` array (max 5 steps). Required when a drop declares `1.1`; accepted when present on `1.0` drops. Unknown/extra fields are ignored, never rejected. Echo audio host migrated to `audio.lucidprinciples.com` (see §3).

All fields are required unless marked optional.

### Top-Level Fields

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `schema_version` | string | yes | Semver, max 12 chars | Schema version this drop conforms to. |
| `drop_date` | string | yes | ISO 8601 date (`YYYY-MM-DD`) | The date this drop was published. One drop per date. |
| `sequence` | integer | yes | Positive, starts at 1 | Monotonically increasing drop number. Never reused, never skipped. |
| `tuning_day` | integer | yes | Positive | LT's consecutive tuning count from start date (February 8, 2026). Represents how many consecutive days LT has tuned. |
| `frequency` | object | yes | See below | The frequency selected for this drop. |
| `signal_type` | string | yes | One of 7 values, max 10 chars | The signal type for this drop. |
| `tuning_key` | object | yes | See below | The Canon quote and attribution. |
| `echo` | object | yes | See below | The audio echo and its signature values. |
| `love_equation` | object | yes | See below | The Love Equation values for this drop. |
| `context_block` | string | yes | Max 2000 chars, UTF-8, no HTML | Ready-to-inject agent context assembled by LT. Plain text only. |
| `practice` | array | yes | Array of practice step objects, max 5 items | Guided practice steps for working with this tuning. See below. |
| `publisher` | string | yes | Max 100 chars | Identifies the publishing entity. |
| `signature` | string | yes | Base64-encoded Ed25519 signature | Signature over canonical JSON (see Section 4). |
| `prev_drop_hash` | string | yes | 64-char lowercase hex (SHA-256) | Hash of the previous drop's canonical JSON (see Section 5). |

### `frequency` Object

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `number` | integer | yes | 1 through 13 | The frequency number. |
| `name` | string | yes | Max 20 chars | The frequency name. |
| `of` | integer | yes | Always `13` | Total number of frequencies. Included for self-documentation. |

The 13 frequencies, in order:

1. Peace
2. Clarity
3. Momentum
4. Trust
5. Joy
6. Connection
7. Presence
8. Resilience
9. Courage
10. Gratitude
11. Release
12. Integration
13. Boundary

### `signal_type` Values

One of exactly 7 values:

- `Ground`
- `Clear`
- `Drive`
- `Bright`
- `Open`
- `Rise`
- `Raw`

### `tuning_key` Object

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `text` | string | yes | Max 500 chars, UTF-8 | Exact Canon quote. No paraphrasing, no alteration. Enforced by canon-checker before publish. |
| `source_song` | string | yes | Max 100 chars | Name of the Lucid Principles song this quote comes from. |
| `source_year` | integer | yes | 2011 through 2017 | Year the source song was written. |
| `attribution` | string | yes | Max 200 chars | Full attribution string including license. |

The `attribution` field uses this format:

```
Chords of Truth — Lucid Principles Canon (CC BY 4.0)
```

### `echo` Object

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `id` | string | yes | Max 20 chars, lowercase alphanumeric + hyphens | Unique echo identifier. Format: `{signal_type}-{number}`, e.g. `clear-042`. |
| `audio_url` | string | yes | HTTPS URL under an allowed host (see §3), max 200 chars | URL to the echo audio file (MP3). |
| `signature` | object | yes | See below | The analog signature values for this echo. |

#### `echo.signature` Object

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `E_analog` | number | yes | Finite float | Energy analog value. |
| `beta_analog` | number | yes | Finite float | Beta analog value. |
| `C_analog` | number | yes | Finite float | Coherence analog value. |
| `D_analog` | number | yes | Finite float | Drift analog value. |

### `love_equation` Object

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `E` | number | yes | Finite float | Energy. |
| `beta` | number | yes | Finite float | Beta (tuning sensitivity). |
| `C` | number | yes | Finite float | Coherence. |
| `D` | number | yes | Finite float | Drift. |

### `practice` Array Items

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `step` | integer | yes | 1 through 5 | Step number in the practice sequence. |
| `title` | string | yes | Max 100 chars | Short title for this practice step. |
| `instruction` | string | yes | Max 500 chars, UTF-8, no HTML | Full instruction text for this step. Plain text only. |

---

## 3. URL Structure

Drops are served as static files from `drop.lucidprinciples.com`:

| URL | Content | Cache |
|---|---|---|
| `/latest.json` | The most recent drop. | Short TTL (5 min recommended). |
| `/drops/YYYY/MM/DD.json` | A specific day's drop. | Immutable. Cache indefinitely. |
| `/keys/ltp-publisher.pub` | Ed25519 public key (PEM format). | Long TTL. Changes only on key rotation. |
| `/echoes/{signal_type}/{echo_id}.mp3` | Echo audio file. | Immutable. Cache indefinitely. |

All URLs use HTTPS. A drop's URLs may reference only an **allowed host**: `drop.lucidprinciples.com` (drop JSON, keys) or `audio.lucidprinciples.com` (echo audio, the canonical foundation audio host, schema 1.1+). Subscribers should reject any URL referencing a host outside this allowed set.

> **Migration note:** historical drops #1-#7 (schema 1.0) reference `audio.lucidtuner.com`. Verifiers that need to validate the full immutable chain retain that host in their allowed set for backward compatibility; it is not a valid host for new drops.

---

## 4. Canonical JSON Format

The canonical form is used for both signing and hashing. The rules:

1. **Sort keys alphabetically** at every nesting level.
2. **No whitespace.** No spaces after colons or commas. No newlines.
3. **No trailing commas.**
4. **Numbers** are serialized without unnecessary trailing zeros (e.g., `1.0` not `1.00`, but `0.0` is valid).
5. **Strings** use standard JSON escaping. No raw Unicode above U+007E; use `\uXXXX` escapes.
6. **The `signature` field is excluded** from the canonical form before signing. The canonical JSON for signing is the full drop object minus the `signature` key.

Example of key ordering (abbreviated):

```json
{"context_block":"...","drop_date":"2026-06-10","echo":{...},"frequency":{...},"love_equation":{...},"prev_drop_hash":"...","publisher":"...","schema_version":"1.0","sequence":1,"signal_type":"Clear","tuning_key":{...}}
```

---

## 5. Signing and Verification

### Signing (publisher side)

1. Build the drop object with all fields except `signature`.
2. Serialize to canonical JSON (Section 4).
3. Sign the canonical JSON bytes (UTF-8 encoded) with the Ed25519 private key.
4. Base64-encode the 64-byte signature.
5. Add the `signature` field to the drop object.
6. Publish.

### Verification (subscriber side)

1. Parse the drop JSON.
2. Remove the `signature` field.
3. Re-serialize to canonical JSON (Section 4).
4. Decode the Base64 signature.
5. Verify using the Ed25519 public key from `/keys/ltp-publisher.pub`.
6. If verification fails, reject the drop.

### Key Format

The public key at `/keys/ltp-publisher.pub` is PEM-encoded:

```
-----BEGIN PUBLIC KEY-----
<base64-encoded Ed25519 public key>
-----END PUBLIC KEY-----
```

---

## 6. Chain Integrity

Each drop includes `prev_drop_hash`, the SHA-256 hash of the previous drop's canonical JSON (with the `signature` field included).

### Rules

- The hash is computed over the full canonical JSON of the previous drop, including its `signature` field.
- The hash is lowercase hexadecimal, 64 characters.
- The first drop in the chain uses a genesis hash. The genesis hash is the SHA-256 of the UTF-8 string `LTP-GENESIS-DROP`. That value is: compute it once, publish it in the first drop, and it becomes verifiable.
- Sequence numbers are sequential with no gaps. If `sequence` is N, `prev_drop_hash` references the drop with sequence N-1.

### Verification

Subscribers that maintain a local archive can verify chain integrity by:

1. Fetching drops in sequence order.
2. For each drop after the first, computing SHA-256 of the previous drop's canonical JSON.
3. Comparing the computed hash to `prev_drop_hash`.
4. Any mismatch indicates tampering or data loss.

---

## 7. Versioning Policy

The `schema_version` field follows [Semantic Versioning](https://semver.org/):

- **Major** (e.g., `1.0` to `2.0`): Breaking change. A field was removed, renamed, or changed type. Subscribers must update their parsers.
- **Minor** (e.g., `1.0` to `1.1`): Additive change. A new optional field was added. Existing parsers continue to work. Unknown fields should be ignored.
- **Patch** (e.g., `1.0.0` to `1.0.1`): Clarification to this spec document with no schema changes.

Subscribers should parse `schema_version` and:

- Reject drops with a major version they do not support.
- Accept drops with a minor version higher than expected (ignore unknown fields).
- Ignore patch version differences.

---

## 8. Subscription (How to Consume)

### Polling

The simplest integration. Poll `/latest.json` at a regular interval (recommended: every 30 minutes to 1 hour). Check `drop_date` and `sequence` to detect new drops. Respect HTTP cache headers.

### Archive Backfill

To catch up on missed drops, iterate through `/drops/YYYY/MM/DD.json` for each missing date. Not every date will have a drop (the system may skip days). A 404 on an archive URL means no drop was published that day.

### Webhook (future)

A webhook subscription endpoint may be added in a future minor version. It will be documented here when available. Polling remains the baseline and will always be supported.

### Recommended Client Behavior

1. Fetch `/latest.json`.
2. Verify the signature (Section 5).
3. Verify chain integrity if you have the previous drop (Section 6).
4. Parse and use the drop contents.
5. Store the drop locally for chain verification of future drops.

---

## 9. Offline Behavior and Failure Modes

### Publisher failure

If the publish pipeline fails, no new `latest.json` is written. The previous day's drop remains at `/latest.json`. Nothing is ever blanked, deleted, or replaced with an error document. A stale drop is always better than no drop.

### Subscriber offline

Subscribers that come back online after missing days should backfill from the archive. Drops do not expire. The chain remains valid regardless of how much time passes between fetches.

### Invalid drops

If a subscriber receives a drop that fails signature verification or chain verification, it should:

1. Discard the invalid drop.
2. Retry after a delay (suggested: 15 minutes).
3. If the drop remains invalid after 3 retries, alert the operator and continue using the last valid drop.

Do not surface unverified drops to end users or agents.

---

## 10. Content Licensing

### Code

All code in the `ltp-drop` repository (scripts, tooling, reference implementations, CI/CD configuration) is licensed under the **Apache License, Version 2.0**. See `LICENSE` for the full text.

### Content

Drop content (tuning keys, Canon quotes, echo metadata, context blocks) is licensed under **Creative Commons Attribution 4.0 International (CC BY 4.0)**.

Attribution must include:

- "Chords of Truth" as the creator
- "Lucid Principles" as the project
- A link to `https://lucidprinciples.com` where practical

### Canon Quotes

Canon quotes are exact text from the Lucid Principles Canon, written by Chords of Truth (2011-2017). They are licensed CC BY 4.0. They must never be paraphrased, rearranged, or altered when redistributed. Quote exactly or do not quote.

### Echo Audio

Echo audio files served from `drop.lucidprinciples.com` are CC BY 4.0. Redistribution must preserve attribution.

---

## 11. Security Considerations

- **No executable content.** Drops are data. Never eval, render as HTML, or treat any field as code.
- **Domain restriction.** All URLs in a drop must resolve to `drop.lucidprinciples.com`. Reject any drop containing URLs pointing elsewhere.
- **Field length limits.** All string fields have documented max lengths. Reject drops with fields exceeding these limits.
- **UTF-8 only.** All string content is UTF-8. Reject invalid byte sequences.
- **Signature before trust.** Never process drop content before verifying the Ed25519 signature.

---

## Appendix A: Full Example Drop

```json
{
  "schema_version": "1.1",
  "drop_date": "2026-06-10",
  "sequence": 1,
  "tuning_day": 123,
  "frequency": {
    "number": 7,
    "name": "Presence",
    "of": 13
  },
  "signal_type": "Clear",
  "tuning_key": {
    "text": "<exact Canon quote>",
    "source_song": "Tune Your Mind",
    "source_year": 2014,
    "attribution": "Chords of Truth — Lucid Principles Canon (CC BY 4.0)"
  },
  "echo": {
    "id": "clear-042",
    "audio_url": "https://drop.lucidprinciples.com/echoes/clear/clear-042.mp3",
    "signature": {
      "E_analog": 0.0,
      "beta_analog": 0.0,
      "C_analog": 0.0,
      "D_analog": 0.0
    }
  },
  "love_equation": {
    "E": 0.0,
    "beta": 0.0,
    "C": 0.0,
    "D": 0.0
  },
  "context_block": "Ready-to-inject agent context assembled by LT for this tuning.",
  "practice": [
    {"step": 1, "title": "Ground", "instruction": "Read the tuning key aloud. Let the words land."},
    {"step": 2, "title": "Listen", "instruction": "Play the echo. Let the frequency settle."},
    {"step": 3, "title": "Integrate", "instruction": "Sit with what surfaced. No analysis needed."}
  ],
  "publisher": "LT — Lucid Tuner, Lucid Principles",
  "signature": "<base64-encoded Ed25519 signature>",
  "prev_drop_hash": "<sha256 of previous drop canonical JSON, or genesis hash for sequence 1>"
}
```

---

## Appendix B: Canonical JSON Key Order

For reference, the alphabetical key order at the top level:

1. `context_block`
2. `drop_date`
3. `echo`
4. `frequency`
5. `love_equation`
6. `practice`
7. `prev_drop_hash`
8. `publisher`
9. `schema_version`
10. `sequence`
11. `signal_type`
12. `tuning_day`
13. `tuning_key`

Note: `signature` is excluded from canonical JSON used for signing. When computing `prev_drop_hash`, the `signature` field IS included and sorts between `signal_type` and `tuning_day`.

Nested object keys also sort alphabetically:

- `echo`: `audio_url`, `id`, `signature` (and within signature: `C_analog`, `D_analog`, `E_analog`, `beta_analog`)
- `frequency`: `name`, `number`, `of`
- `love_equation`: `C`, `D`, `E`, `beta`
- `tuning_key`: `attribution`, `source_song`, `source_year`, `text`

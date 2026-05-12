# Changelog

## 2026-05-12 — Publication-Readiness Pass

**Upstream baseline:** Validated against
[meshcore-dev/MeshCore](https://github.com/meshcore-dev/MeshCore) at commit
`1a7b3614a8439894714a58af55ab7f501e6bb928` (2026-04-28). Every normative
claim in this pass was cross-checked against this commit. Where the in-tree
spec disagreed with upstream, upstream won.

### Process

- Adopted **conventional commits** as the commit-message convention for this
  repo. Types: `spec(<section>)`, `corpus(<area>)`, `docs`, `tools`,
  `chore`, `fix`, `feat`. Subject ≤ 70 chars; body explains *why* and cites
  the upstream commit/function the change was validated against.
- Established **"upstream firmware is the golden source of truth"** as a
  load-bearing principle for the project: DongLoRa firmware, the ai-bot,
  this spec, and prior audit notes are all downstream of the official C++.
  When any of them disagree with upstream, upstream wins. This is now
  reflected in the README's Provenance section and applied to every edit
  below.

### Added

- **`corpus/crypto/sha256/ack-crc.json`** — four SHA-256-truncation test
  vectors covering ACK CRC computation across attempts 0..3. Each vector
  pairs a structured ACK packet with the plaintext + sender pub_key it was
  derived from, pinning the algorithm
  `SHA-256(timestamp(4) || txt_type_attempt(1) || text || sender_pub_key(32))[0..3]`.
- **`spec/04-payload-ack.md`** — explicit ACK CRC computation algorithm
  written out, including the `TXT_TYPE_SIGNED_PLAIN` variant (which uses the
  receiver's public key and includes the 4-byte signature in the prefix).
- **`spec/06-payload-encrypted.md`** — new "Attempt Counter Semantics"
  subsection covering the 2-bit attempt encoding, the `[NUL][attempt_full]`
  tail-byte mechanism upstream uses for attempts > 3, and the ACK-CRC
  collision implications when attempts roll over. New "Reliable DM Delivery"
  subsection covering expected-ACK tracking, retry, MULTIPART/plain ACK
  consumption, and the optional duplicate-DM reply cache.
- **`spec/11-payload-multipart.md`** — new "Multipart ACK Usage Constraints"
  subsection: direct-routed paths only, CRC dedup, ~300 ms inter-copy delay,
  emission count controlled by `getExtraAckTransmitCount()` (upstream
  default 0). Clarified that the chain terminates with a plain
  `PAYLOAD_TYPE_ACK`, not a MULTIPART with `remaining = 0`.
- **`spec/17-routing.md`** — new "Sender Behavior (Informational)" section:
  path learning, PATH_RETURN emission and timing, flood/direct fallback on
  retry, sender-side transmission priority table.
- **`README.md`** — prominent **Provenance** disclosure block, plus a new
  **Author** section.

### Clarified

- **`spec/06-payload-encrypted.md`** — encryption procedure now spells out
  zero-padding to a 16-byte AES block boundary before AES-128-ECB, and
  warns that the scheme is not unambiguous (receiver disambiguates trailing
  zeros via the inner plaintext format).
- **`spec/11-payload-multipart.md`** — the MULTIPART chain definition now
  explicitly notes the descending `remaining` count and the plain-ACK
  finalizer.

### Corrected

- **`spec/17-routing.md`** — the previous wording described the reference
  implementation's path-replacement as a hash-size/SNR heuristic. In fact,
  `BaseChatMesh::onContactPathRecv()` in upstream does an **unconditional
  replace**, with an inline source comment flagging selection heuristics as
  future work. Likewise, the spec no longer implies the reference
  implementation has a path TTL — it doesn't. Quality heuristics and TTL
  policies are noted as implementation extensions.

### Out of scope this pass

Several observations from `donglora/firmware` and `donglora/ai-bot` were
considered and **dropped** when found to be ai-bot/firmware-specific rather
than upstream behavior. Examples: a 30-minute route TTL, a 3 dB SNR margin
for path upgrades, rejection of 1-byte path hashes, a 150 ms PATH_RETURN
delay, hard-coded sync word `0x1424`, and a pending-ACK table capped at 64
entries / 125 s. Per the upstream-is-golden principle, these would have
read like upstream-blessed reference values, which they are not. They are
implementation extensions that downstream projects may adopt at their
discretion.

Radio/hardware-state behaviors surfaced by the DongLoRa firmware audit
(CAD/LBT retry strategy, RX session preservation across SET_CONFIG,
host-side backpressure, UART frame-decoder reset) were also excluded —
they are radio-driver concerns rather than packet-format/protocol
semantics. A future non-normative "Implementation Notes" appendix could
collect such items.

## 2026-04-01 — Comprehensive Spec Audit

### Removed

- `ERRATA.md` — Reviewed and removed. Its ACK CRC formula was correct but
  already fully covered by the audit findings (C2). Its claim about ACK routing
  (flood vs tflood) is standard behavior for all packet types (route type is
  always set by the send function, not create), not errata.

### Added

- `PYMC_CORE_ISSUES.md` — Seven detailed, evidence-based bug reports for the
  pyMC_core Python reference implementation, ready to file as GitHub issues:
  1. `CIPHER_MAC_SIZE` in `constants.py` is 32, should be 2
  2. `MAX_HASH_SIZE` in `constants.py` is 32, should be 8
  3. `MAX_PACKET_PAYLOAD` in `constants.py` is 256, should be 184
  4. `MAX_ADVERT_DATA_SIZE` in `constants.py` is 96, should be 32
  5. `packet.py` `read_from()` treats `path_len` as raw byte count instead of
     decoding hash_size/hash_count bitfield encoding
  6. `packet_utils.py` `calculate_packet_hash()` hashes TRACE `path_len` as 1
     byte instead of 2 (C++ uses `sizeof(uint16_t)`)
  7. `packet_utils.py` `calculate_snr_db()` returns raw value instead of
     dividing by 4.0

### Identified (spec issues to fix in future commits)

- **Critical errors in spec**:
  - `16-packet-hash.md`: TRACE `path_len` documented as 1-byte hash input, but
    C++ hashes it as `uint16_t` (2 bytes LE)
  - `04-payload-ack.md`: ACK CRC computation described vaguely ("from the
    original message's timestamp, text, and sender public key") — actual
    algorithm is SHA-256 over `(plaintext_data || sender_pub_key)` truncated to
    4 bytes
  - `16-packet-hash.md` / `17-routing.md`: ACK deduplication uses 4-byte CRC
    directly from payload, not the 8-byte packet hash — undocumented

- **Major missing documentation**:
  - End-to-end DM data flow (discovery, flood send, path return + ACK, route
    update, switch to direct)
  - Text message plaintext format (`TXT_TYPE_PLAIN=0`, `TXT_TYPE_CLI_DATA=1`,
    `TXT_TYPE_SIGNED_PLAIN=2`), signed message format, ACK computation per type
  - Room server login flow (ANON_REQ with password, login response format,
    connection keepalive at 2.5x timeout)
  - Group/channel message plaintext format (`"sender_name: text"` prefix,
    channel PSK derivation)
  - Remote administration protocol: REQ_TYPE constants (0x01-0x07), status
    response struct, telemetry permissions, CLI-over-mesh via TXT_TYPE_CLI_DATA,
    anonymous request subtypes (REGIONS, OWNER, BASIC/clock sync), neighbour
    queries with sort/pagination
  - Transport codes computation (HMAC-SHA256 based, region key derivation)
  - Duty cycle / airtime budget (formulas, budget factor, refill, enforcement)
  - Retransmit delay formulas (flood random delay, score-based RX delay, CAD
    fail retry)
  - Private key validation (0x00/0xFF rejection, ECDH mutual test, zero-secret
    rejection)

- **Moderate issues**:
  - `17-routing.md`: Priority table is misleading — flood forwarding priority is
    dynamic (`hash_count`), not fixed
  - `05-payload-advert.md`: feat1/feat2 only encoded when non-zero (not
    documented)
  - `16-packet-hash.md`: payload_type byte extraction could be clearer (4-bit
    value zero-extended to a byte)

- **Companion/KISS/Bridge protocol issues** (lower priority):
  - Companion protocol: spec documents 19 commands, code has 61; framing format
    is wrong (spec says type-byte, code uses `>/<` delimiters with 2-byte LE
    length)
  - KISS: missing default parameter values, CSMA algorithm, RxMeta auto-send
  - Bridge: missing ESP-NOW XOR encryption documentation

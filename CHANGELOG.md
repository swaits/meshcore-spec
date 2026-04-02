# Changelog

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

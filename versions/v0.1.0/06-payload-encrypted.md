# MeshCore Protocol Specification

## Section 6: Payload — Encrypted (REQ / RESPONSE / TXT_MSG)

### Overview

The REQUEST, RESPONSE, and TXT_MSG payload types share an identical wire format.
They consist of a destination hash, source hash, and an encrypt-then-MAC
ciphertext blob. The three types differ only in their semantic meaning at the
application layer.

### Payload Types

| Value | Name | Description |
|-------|------|-------------|
| 0x00 | REQUEST | Encrypted request (e.g., login, data query) |
| 0x01 | RESPONSE | Encrypted response to a REQUEST or ANON_REQ |
| 0x02 | TXT_MSG | Encrypted text message |

### Wire Format

```
 0
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| dest_hash(1)  |  src_hash(1)  |    Cipher MAC (2 bytes)       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
|              Ciphertext (N × 16 bytes, N ≥ 1)                |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### Fields

| Field | Offset | Size | Type | Description |
|-------|--------|------|------|-------------|
| dest_hash | 0 | PATH_HASH_SIZE (1) | raw | First byte of recipient's Ed25519 public key |
| src_hash | 1 | PATH_HASH_SIZE (1) | raw | First byte of sender's Ed25519 public key |
| cipher_mac | 2 | CIPHER_MAC_SIZE (2) | raw | Truncated HMAC-SHA256 over ciphertext |
| ciphertext | 4 | variable (multiple of 16) | raw | AES-128-ECB encrypted data |

### Minimum Size

- Minimum payload: 4 + 16 = 20 bytes (dest_hash + src_hash + MAC + 1 AES block)

### Encryption

The ciphertext is produced using the encrypt-then-MAC scheme described in
[Section 14](14-crypto.md):

1. Compute the ECDH shared secret between sender and recipient.
2. Zero-pad the plaintext on the right with `0x00` bytes until its length is a
   multiple of 16 (AES block size). If the plaintext is already a multiple of
   16, no padding is added (the scheme is not unambiguous PKCS#7-style
   padding — the receiver MUST disambiguate trailing zeros using the inner
   plaintext format; see "Plaintext Format" below).
3. Encrypt the padded plaintext using AES-128-ECB with the first 16 bytes of
   the shared secret as the key.
4. Compute HMAC-SHA256 over the ciphertext using the full 32-byte shared
   secret as the HMAC key. Truncate to 2 bytes.
5. Prepend the 2-byte MAC to the ciphertext.

### Decryption

1. Extract dest_hash and src_hash.
2. If dest_hash matches this node, search for peers matching src_hash.
3. For each matching peer, compute or retrieve the shared secret.
4. Verify the MAC: compute HMAC-SHA256 over the ciphertext portion using the
   full 32-byte shared secret. Compare the first 2 bytes with cipher_mac.
5. If the MAC is valid, decrypt the ciphertext using AES-128-ECB with the first
   16 bytes of the shared secret. The decrypted data may contain trailing zero
   bytes from padding.
6. If no peer's MAC matches, the packet is not for this node (or the peer is
   unknown). The packet MAY still be forwarded.

### Plaintext Format (TXT_MSG)

For TXT_MSG payloads, the decrypted plaintext has this structure:

| Field | Offset | Size | Type | Description |
|-------|--------|------|------|-------------|
| timestamp | 0 | 4 bytes | uint32_le | Message timestamp |
| txt_type_attempt | 4 | 1 byte | uint8 | Bits 2-7: message type (see [Section 4](04-payload-ack.md)); bits 0-1: attempt counter (0-3). See "Attempt Counter Semantics" below. |
| text | 5 | remaining | UTF-8 | Message text |

#### Attempt Counter Semantics

The `attempt` sub-field (bits 0-1 of `txt_type_attempt`) carries the low two
bits of a transmission attempt counter used by the sender's retry logic. For
a given logical TXT_MSG:

- The `timestamp` field MUST remain stable across all retries of the same
  message.
- The `attempt` counter MUST be 0 on the first transmission and MUST be
  incremented by 1 on each retry.
- Bits 0–1 of `txt_type_attempt` MUST always carry `attempt & 3`. These bits
  are part of the ACK CRC input (see
  [Section 4](04-payload-ack.md#ack-crc-computation)), so each retry of a
  message produces a distinct expected ACK CRC.
- For attempts in `0..3`, no further encoding is needed; the plaintext ends
  with the text.
- For attempts `> 3`, the sender MUST append a 2-byte tail
  `[NUL_terminator(1)][attempt_full(1)]` to the plaintext after the text,
  where `attempt_full` is the full 1-byte counter value (not just the low
  2 bits). The receiver locates the text by scanning for the NUL terminator
  and recovers the full attempt value from the trailing byte. Because this
  tail costs 2 bytes of plaintext capacity, the maximum text length is
  reduced by 2 bytes when `attempt > 3`.
- The ACK CRC is computed over `timestamp(4) || txt_type_attempt(1) || text`
  only. The `[NUL][attempt_full]` tail (when present) and the implicit C
  string NUL terminator (when not) are excluded from the hash input. This
  means a retry with attempt 4 and a retry with attempt 0 produce ACK CRCs
  that match (since `4 & 3 == 0`); senders relying on attempts beyond 3
  SHOULD also verify the trailing attempt byte if they need to distinguish
  rolled-over attempts.

See `BaseChatMesh::composeMsgPacket()` in
`src/helpers/BaseChatMesh.cpp` for the reference encoding.

### Reliable DM Delivery

The following sender-side behavior is informational and documents how
interoperating implementations deliver TXT_MSG reliably. Exact timeouts,
backoff schedules, and queue depths are implementation-defined; see
[Section 17 — Sender Behavior](17-routing.md#sender-behavior-informational)
for routing-layer details.

- **Expected-ACK tracking.** On transmit, the sender SHOULD compute the
  expected `ack_crc` (see [Section 4](04-payload-ack.md#ack-crc-computation))
  and record it in a pending-ACK table keyed by CRC. The table SHOULD bound
  entries by capacity and age out entries after the retry schedule has
  completed (plus a margin for in-flight ACKs).
- **Retry.** If no matching ACK is received within an implementation-defined
  timeout, the sender SHOULD retransmit with `attempt` incremented (per
  "Attempt Counter Semantics" above) and re-register the new expected
  `ack_crc`. Up to 4 attempts are representable in the 2-bit `attempt`
  field.
- **ACK consumption.** On receipt of a PAYLOAD_TYPE_ACK or a MULTIPART-wrapped
  ACK whose `ack_crc` matches a pending entry, the sender MUST treat the
  message as delivered, remove the pending-ACK entry, and cancel any queued
  retries for that CRC.
- **Duplicate DM handling at the receiver.** A receiver MAY cache its most
  recent reply per peer keyed by the inbound DM's plaintext and, on a
  duplicate inbound DM within a short window, re-emit the cached reply as a
  loss-recovery optimization. This is not normative; the normative behavior
  is "process once and rely on [Section 16](16-packet-hash.md) dedup."
  Implementations that re-emit cached replies SHOULD suppress re-emission
  while a retry for that reply is still pending, to avoid piling on.

### Plaintext Format (REQUEST / RESPONSE)

The plaintext format for REQUEST and RESPONSE is application-defined. Common
patterns include:

- **REQUEST**: `[timestamp(4)][request_data...]`
- **RESPONSE**: `[timestamp(4)][response_data...]`

### Cross-References

- [Section 14: Cryptography](14-crypto.md) — Encrypt-then-MAC details
- [Section 15: Identity](15-identity.md) — ECDH shared secret computation
- Test vectors: [`corpus/payloads/encrypted/`](https://github.com/swaits/meshcore-spec/tree/v0.1.0/corpus/payloads/encrypted/)

### Reference Implementation

- `Mesh::createDatagram()` in `src/Mesh.cpp` — Encoding
- `Mesh::onRecvPacket()`, cases `PAYLOAD_TYPE_REQ/RESPONSE/TXT_MSG` — Decoding
- `Utils::encryptThenMAC()` in `src/Utils.cpp` — Encryption
- `Utils::MACThenDecrypt()` in `src/Utils.cpp` — Decryption and verification

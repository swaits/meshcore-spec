# MeshCore Protocol Specification

## Section 8: Payload — Group (GRP_TXT / GRP_DATA)

### Overview

Group payloads enable encrypted communication within a channel. All members of a
channel share a symmetric secret. The payload begins with a 1-byte channel hash
(derived from the channel's shared key), followed by an encrypt-then-MAC blob.

### Payload Types

| Value | Name | Description |
|-------|------|-------------|
| 0x05 | GRP_TXT | Group text message |
| 0x06 | GRP_DATA | Group datagram (binary data) |

### Wire Format

```
 0
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|channel_hash(1)|    Cipher MAC (2 bytes)       |               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+               |
|              Ciphertext (N × 16 bytes, N ≥ 1)                |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### Fields

| Field | Offset | Size | Type | Description |
|-------|--------|------|------|-------------|
| channel_hash | 0 | 1 byte | raw | First byte of SHA-256(channel_shared_key) |
| cipher_mac | 1 | 2 bytes | raw | Truncated HMAC-SHA256 over ciphertext |
| ciphertext | 3 | variable (multiple of 16) | raw | AES-128-ECB encrypted data |

### Minimum Size

- Minimum payload: 1 + 2 + 16 = 19 bytes

### Channel Hash Derivation

The channel_hash is the first byte of the SHA-256 hash of the channel's 32-byte
shared key (PUB_KEY_SIZE bytes):

```
channel_hash = SHA256(channel_shared_key)[0]
```

This means hash collisions are expected (1 in 256 chance). When a receiver finds
a matching channel_hash, it attempts decryption with each matching channel's
secret. Only a successful MAC verification confirms the correct channel.

### Encryption

1. Encrypt plaintext using AES-128-ECB with first 16 bytes of the channel's
   shared key (GroupChannel.secret).
2. Compute HMAC-SHA256 over ciphertext using all 32 bytes of the channel's
   shared key. Truncate to 2 bytes.
3. Assemble: channel_hash || MAC || ciphertext.

### Decryption

1. Read channel_hash (1 byte).
2. Search local channel database for channels with matching hash. Multiple
   channels may match (up to 4 in reference implementation).
3. For each matching channel, attempt MAC verification and decryption using the
   channel's shared key.
4. The first channel that produces a valid MAC yields the correct decryption.

### Inner Plaintext Format

The decrypted ciphertext begins with a 4-byte little-endian `timestamp`. The
remaining bytes depend on the payload type.

**GRP_TXT** uses the same `timestamp ‖ flags` prefix as TXT_MSG (see
[Section 6 — Plaintext Format (TXT_MSG)](06-payload-encrypted.md#plaintext-format-txt_msg)):

| Field | Offset | Size | Type | Description |
|-------|--------|------|------|-------------|
| timestamp | 0 | 4 bytes | uint32_le | Message timestamp |
| flags | 4 | 1 byte | uint8 | Bits 2–7: message type (`0` = plain text); bits 0–1: attempt counter |
| message | 5 | remaining | UTF-8 | `"<sender_name>: <body>"` |

For GRP_TXT the reference chat firmware always sets `flags` to `0x00`
(`TXT_TYPE_PLAIN`, attempt 0). The `message` joins the sender's display name
and the body as `"<sender_name>: <body>"` (for example, `alice: on my way`), so
every channel member can attribute the message without a separate sender field.
The receiver requires the plaintext to be longer than 5 bytes and reads
`message` as a NUL-terminated string: trailing zero bytes from AES-ECB padding
(see [Section 14](14-crypto.md)) act as the terminator, and a receiver MUST
treat the first `0x00` byte at or after offset 5 as the end of the message.

**GRP_DATA** carries `timestamp(4)` followed by an application-defined binary
blob. MeshCore prescribes no structure for the blob.

### Length Limits

The ciphertext is AES-128-ECB output, so it is always a positive multiple of
`CIPHER_BLOCK_SIZE` (16 bytes). With a 1-byte `channel_hash` and 2-byte
`cipher_mac`, the encoder (`Mesh::createGroupDatagram`) rejects any plaintext
longer than 168 bytes (`data_len + 1 + CIPHER_BLOCK_SIZE − 1 ≤
MAX_PACKET_PAYLOAD`).

For GRP_TXT the reference chat firmware applies a tighter limit: `MAX_TEXT_LEN`
= `10 × CIPHER_BLOCK_SIZE` = **160 bytes** (`BaseChatMesh.h`). This bound is
applied to the combined `"<sender_name>: " + body` text; the 4-byte `timestamp`
and 1-byte `flags` are additional.

Because the sender's display name is embedded in the plaintext, the body length
available to an application is **not fixed** — it shrinks as the sender name
grows. For sender names of 0–32 characters the usable body runs roughly from
153 bytes (short name) down to 121 bytes (32-character name). Implementations
MUST handle this variability and MUST NOT assume a single fixed maximum body
length.

> **Note (informational).** Upstream issue
> [#2583](https://github.com/meshcore-dev/MeshCore/issues/2583) proposes raising
> the GRP_TXT limit to 11 blocks (~172 bytes), since a 1-byte `channel_hash`,
> 2-byte `cipher_mac`, and an 11-block ciphertext still fit within
> `MAX_PACKET_PAYLOAD`. That change is not present in the reference firmware
> this specification tracks.

### Cross-References

- [Section 14: Cryptography](14-crypto.md) — Encrypt-then-MAC
- Test vectors: [`corpus/payloads/group/`](https://github.com/swaits/meshcore-spec/tree/main/corpus/payloads/group/)

### Reference Implementation

- `Mesh::createGroupDatagram()` in `src/Mesh.cpp` — Encoding
- `Mesh::onRecvPacket()`, cases `PAYLOAD_TYPE_GRP_TXT/GRP_DATA` — Decoding
- `Mesh::searchChannelsByHash()` — Channel lookup

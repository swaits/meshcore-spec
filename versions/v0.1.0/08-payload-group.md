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

### Cross-References

- [Section 14: Cryptography](14-crypto.md) — Encrypt-then-MAC
- Test vectors: [`corpus/payloads/group/`](https://github.com/swaits/meshcore-spec/tree/main/versions/v0.1.0/corpus/payloads/group/)

### Reference Implementation

- `Mesh::createGroupDatagram()` in `src/Mesh.cpp` — Encoding
- `Mesh::onRecvPacket()`, cases `PAYLOAD_TYPE_GRP_TXT/GRP_DATA` — Decoding
- `Mesh::searchChannelsByHash()` — Channel lookup

# MeshCore Protocol Specification

## Section 7: Payload — Anonymous Request

### Overview

The anonymous request payload allows a node to send an encrypted message to a
recipient without the recipient needing to know the sender in advance. Instead of
a 1-byte source hash, the full 32-byte Ed25519 public key of the sender is
included, enabling the recipient to compute the shared secret for decryption.

### Payload Type

Header payload type field: `0x07` (ANON_REQ)

### Wire Format

```
 0
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| dest_hash(1)  |                                               |
+-+-+-+-+-+-+-+-+                                               |
|                   Sender Public Key (32 bytes)                |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|    Cipher MAC (2 bytes)       |                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+                               |
|              Ciphertext (N × 16 bytes, N ≥ 1)                |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### Fields

| Field | Offset | Size | Type | Description |
|-------|--------|------|------|-------------|
| dest_hash | 0 | 1 byte | raw | First byte of recipient's Ed25519 public key |
| sender_pub_key | 1 | 32 bytes | raw | Full Ed25519 public key of sender |
| cipher_mac | 33 | 2 bytes | raw | Truncated HMAC-SHA256 over ciphertext |
| ciphertext | 35 | variable (multiple of 16) | raw | AES-128-ECB encrypted data |

### Minimum Size

- Minimum payload: 1 + 32 + 2 + 16 = 51 bytes

### Encryption

1. Sender computes ECDH shared secret using its private key and the recipient's
   public key.
2. Encrypt plaintext using AES-128-ECB with first 16 bytes of shared secret.
3. Compute HMAC-SHA256 over ciphertext with full 32-byte shared secret.
   Truncate to 2 bytes.
4. Assemble: dest_hash || sender_pub_key || MAC || ciphertext.

### Decryption

1. Read dest_hash. If it does not match this node, the packet is not for us
   (but MAY be forwarded).
2. Read 32-byte sender_pub_key. Construct an Identity from it.
3. Compute ECDH shared secret between this node's private key and sender's
   public key.
4. Verify the MAC and decrypt as in [Section 14](14-crypto.md).

### Cross-References

- [Section 6: Encrypted Payloads](06-payload-encrypted.md) — Standard encrypted format
- [Section 14: Cryptography](14-crypto.md) — Encrypt-then-MAC
- [Section 15: Identity](15-identity.md) — ECDH key exchange
- Test vectors: `corpus/payloads/anon-req/`

### Reference Implementation

- `Mesh::createAnonDatagram()` in `src/Mesh.cpp` — Encoding
- `Mesh::onRecvPacket()`, case `PAYLOAD_TYPE_ANON_REQ` — Decoding

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
2. Encrypt the plaintext using AES-128-ECB with the first 16 bytes of the
   shared secret as the key. Zero-pad the final block.
3. Compute HMAC-SHA256 over the ciphertext using the full 32-byte shared secret
   as the HMAC key. Truncate to 2 bytes.
4. Prepend the 2-byte MAC to the ciphertext.

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
| txt_type_attempt | 4 | 1 byte | uint8 | Upper 6 bits: message type, lower 2 bits: attempt (0-3) |
| text | 5 | remaining | UTF-8 | Message text |

### Plaintext Format (REQUEST / RESPONSE)

The plaintext format for REQUEST and RESPONSE is application-defined. Common
patterns include:

- **REQUEST**: `[timestamp(4)][request_data...]`
- **RESPONSE**: `[timestamp(4)][response_data...]`

### Cross-References

- [Section 14: Cryptography](14-crypto.md) — Encrypt-then-MAC details
- [Section 15: Identity](15-identity.md) — ECDH shared secret computation
- Test vectors: `corpus/payloads/encrypted/`

### Reference Implementation

- `Mesh::createDatagram()` in `src/Mesh.cpp` — Encoding
- `Mesh::onRecvPacket()`, cases `PAYLOAD_TYPE_REQ/RESPONSE/TXT_MSG` — Decoding
- `Utils::encryptThenMAC()` in `src/Utils.cpp` — Encryption
- `Utils::MACThenDecrypt()` in `src/Utils.cpp` — Decryption and verification

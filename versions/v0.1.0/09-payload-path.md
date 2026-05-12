# MeshCore Protocol Specification

## Section 9: Payload — Path Return

### Overview

The PATH payload carries an encrypted return path from one node to another. It
uses the same dest_hash + src_hash + encrypt-then-MAC envelope as REQ/RESPONSE/
TXT_MSG, but the decrypted contents contain routing path data and optional extra
application data.

### Payload Type

Header payload type field: `0x08` (PATH)

### Wire Format (Outer)

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

The outer format is identical to [Section 6](06-payload-encrypted.md).

### Decrypted Inner Format

```
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  path_len(1)  |         Path (hash_count × hash_size)        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| extra_type(1) |         Extra Data (variable)                 |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

| Field | Size | Type | Description |
|-------|------|------|-------------|
| path_len | 1 byte | encoded | Same bitfield encoding as packet path_len (see [Section 3](03-path.md)) |
| path | hash_count × hash_size | raw | The return path to the sender |
| extra_type | 1 byte | uint8 | Type of extra data (lower 4 bits used; upper 4 reserved) |
| extra | remaining | raw | Extra data (may include trailing zero padding from AES) |

### Extra Type Values

| Value | Description |
|-------|-------------|
| 0x00 | No meaningful extra data (reciprocal path) |
| 0xFF | Dummy/padding (used when no real extra data; followed by 4 random bytes) |
| Other | Application-defined |

When creating a path return with no extra data, the reference implementation
appends `0xFF` as extra_type followed by 4 random bytes to ensure the packet
hash is unique.

### Encoding

1. Build the inner plaintext:
   a. Write path_len byte (encoded hash_size and hash_count).
   b. Write path bytes (hash_count × hash_size).
   c. If extra data is provided: write extra_type (lower 4 bits), write extra.
   d. If no extra data: write `0xFF`, write 4 random bytes.
2. Encrypt the inner plaintext using encrypt-then-MAC with the shared secret.
3. Prepend dest_hash and src_hash.

### Decoding

1. Decode the outer envelope (dest_hash, src_hash, MAC, ciphertext) as in
   [Section 6](06-payload-encrypted.md).
2. After decryption:
   a. Read 1 byte as path_len. Decode hash_size and hash_count.
   b. Read hash_count × hash_size bytes as the path.
   c. Read 1 byte as extra_type (use lower 4 bits only).
   d. Remaining bytes are extra data (may include AES zero-padding).

### Cross-References

- [Section 3: Path](03-path.md) — Path length encoding
- [Section 6: Encrypted Payloads](06-payload-encrypted.md) — Outer envelope format
- [Section 14: Cryptography](14-crypto.md) — Encrypt-then-MAC
- Test vectors: `corpus/payloads/path-return/`

### Reference Implementation

- `Mesh::createPathReturn()` in `src/Mesh.cpp` — Encoding
- `Mesh::onRecvPacket()`, PATH case within REQ/RESPONSE/TXT_MSG handling — Decoding

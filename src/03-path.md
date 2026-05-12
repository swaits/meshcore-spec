# MeshCore Protocol Specification

## Section 3: Path

### Overview

The path field carries routing information as a sequence of node hashes. In
flood routing, intermediate nodes append their hash to the path as they forward
the packet. In direct routing, the sender supplies the full path. The path
length byte uses bit packing to encode both the number of hashes and the size of
each hash.

### Path Length Byte

The path length byte immediately follows the header (and transport codes, if
present). It encodes two values:

```
  Bit:  7   6   5   4   3   2   1   0
      +---+---+---+---+---+---+---+---+
      | S1  S0| C5  C4  C3  C2  C1  C0|
      +---+---+---+---+---+---+---+---+
             |              |
             |              +-- Hash Count (bits 0-5): 0-63
             +----------------- Hash Size Code (bits 6-7): 0-2 (3 is reserved)
```

| Field | Bits | Extraction | Range | Description |
|-------|------|-----------|-------|-------------|
| Hash Count | 0-5 | `path_len & 0x3F` | 0-63 | Number of hashes in the path |
| Hash Size Code | 6-7 | `path_len >> 6` | 0-2 | Encoded hash size: actual size = code + 1 |

The **actual hash size** in bytes is:

```
hash_size = (path_len >> 6) + 1
```

| Hash Size Code | Actual Hash Size | Description |
|---------------|-----------------|-------------|
| 0 (`0b00`) | 1 byte | V1 default (PATH_HASH_SIZE) |
| 1 (`0b01`) | 2 bytes | Extended precision |
| 2 (`0b10`) | 3 bytes | Extended precision |
| 3 (`0b11`) | **RESERVED** | MUST be rejected as invalid |

The path length byte is constructed as:

```
path_len = ((hash_size - 1) << 6) | (hash_count & 0x3F)
```

### Path Field

The path field immediately follows the path length byte. Its size in bytes is:

```
path_byte_length = hash_count × hash_size
```

The path contains `hash_count` consecutive hashes, each `hash_size` bytes long.
Each hash is a prefix of a node's Ed25519 public key (see [Section 15](15-identity.md)).

```
+----------+----------+-----+----------+
| Hash 0   | Hash 1   | ... | Hash N-1 |
| (H bytes)| (H bytes)| ... | (H bytes)|
+----------+----------+-----+----------+

where H = hash_size, N = hash_count
```

When hash_count is 0, the path field is empty (zero bytes on the wire).

### Validation Rules

A conforming implementation MUST reject a packet if any of the following are
true:

1. **Reserved hash size**: Hash size code is 3 (bits 6-7 = `0b11`), meaning
   hash_size would be 4. This value is reserved for future use.

2. **Path overflow**: `hash_count × hash_size > MAX_PATH_SIZE` (64 bytes).

The maximum number of hashes depends on hash size:

| Hash Size | Max Hash Count | Max Path Bytes |
|-----------|---------------|----------------|
| 1 byte | 63 | 63 |
| 2 bytes | 32 | 64 |
| 3 bytes | 21 | 63 |

Note: With 1-byte hashes the maximum hash count is 63 (not 64), because the
count field is only 6 bits wide. With 2-byte hashes, 32 × 2 = 64 bytes exactly
fills MAX_PATH_SIZE. With 3-byte hashes, 21 × 3 = 63 bytes is the maximum
before 22 × 3 = 66 would overflow.

### Path Manipulation

**Appending a hash (flood routing):**
When a node forwards a flood-routed packet, it appends its own hash to the path:

1. Let `n` = current hash_count.
2. Verify `(n + 1) × hash_size <= MAX_PATH_SIZE`. If not, the node MUST NOT
   forward the packet.
3. Copy the node's hash (first `hash_size` bytes of its public key) to
   `path[n × hash_size]`.
4. Increment hash_count: `setPathHashCount(n + 1)`.

**Setting hash size and count:**
```
path_len = ((hash_size - 1) << 6) | (hash_count & 0x3F)
```

### Encoding Examples

| path_len byte | Binary | Hash Size Code | Hash Count | Hash Size | Path Bytes |
|---------------|--------|---------------|------------|-----------|------------|
| `0x00` | `00 000000` | 0 | 0 | 1 | 0 |
| `0x01` | `00 000001` | 0 | 1 | 1 | 1 |
| `0x03` | `00 000011` | 0 | 3 | 1 | 3 |
| `0x3F` | `00 111111` | 0 | 63 | 1 | 63 |
| `0x41` | `01 000001` | 1 | 1 | 2 | 2 |
| `0x42` | `01 000010` | 1 | 2 | 2 | 4 |
| `0x60` | `01 100000` | 1 | 32 | 2 | 64 |
| `0x81` | `10 000001` | 2 | 1 | 3 | 3 |
| `0x95` | `10 010101` | 2 | 21 | 3 | 63 |
| `0xC0` | `11 000000` | 3 | 0 | **INVALID** | — |
| `0xFF` | `11 111111` | 3 | 63 | **INVALID** | — |

### Known Implementation Discrepancy

The Rust implementation [meshcore-rs](https://github.com/Duncaen/meshcore-rs)
treats the path_len byte as a raw byte count rather than decoding hash_count and
hash_size from the bitfields. For example, a path_len value of `0x42` (binary
`01 000010`) should decode as hash_size=2, hash_count=2, path_bytes=4. The
incorrect interpretation reads it as a raw count of 66 bytes.

Test vectors in this corpus specifically exercise multi-byte hash sizes to catch
this class of bug.

### Cross-References

- [Section 1: Wire Format](01-wire-format.md) — Overall packet structure
- [Section 2: Header](02-header.md) — Header encoding
- [Section 15: Identity](15-identity.md) — Hash derivation from public keys
- Test vectors: `corpus/wire-format/path/`

### Reference Implementation

- `Packet::getPathHashSize()` in `src/Packet.h` — `(path_len >> 6) + 1`
- `Packet::getPathHashCount()` in `src/Packet.h` — `path_len & 63`
- `Packet::getPathByteLen()` in `src/Packet.h` — `getPathHashCount() * getPathHashSize()`
- `Packet::setPathHashSizeAndCount()` in `src/Packet.h` — `((sz - 1) << 6) | (n & 63)`
- `Packet::isValidPathLen()` in `src/Packet.cpp` — Validation logic
- `Packet::writePath()` in `src/Packet.cpp` — Path serialization

# MeshCore Protocol Specification

## Section 16: Packet Hash

### Overview

MeshCore uses SHA-256 hashing for packet deduplication. Each node maintains a
table of recently seen packet hashes and discards packets it has already
processed. The hash is computed over the payload type and payload contents, with
a special case for TRACE packets.

### Hash Computation

The packet hash is computed as:

```
hash = SHA-256(payload_type_byte || payload_data)[0..MAX_HASH_SIZE-1]
```

Where:
- `payload_type_byte` is a single byte: `(header >> 2) & 0x0F`
- `payload_data` is the raw payload bytes (payload_len bytes)
- The SHA-256 output is truncated to MAX_HASH_SIZE (8) bytes

### TRACE Packet Special Case

For TRACE packets (payload_type = 0x09), the path_len byte is included in the
hash to distinguish trace packets that revisit the same node on their return
path:

```
hash = SHA-256(payload_type_byte || path_len_byte || payload_data)[0..MAX_HASH_SIZE-1]
```

### Algorithm

```
function calculatePacketHash(packet):
    sha = SHA256_init()
    type_byte = getPayloadType(packet.header)  // single byte
    SHA256_update(sha, type_byte)
    if type_byte == 0x09:  // TRACE
        SHA256_update(sha, packet.path_len)  // 1 byte (as uint8)
    SHA256_update(sha, packet.payload, packet.payload_len)
    hash = SHA256_finalize(sha)
    return hash[0..7]  // first MAX_HASH_SIZE bytes
```

### Properties

- The hash does NOT include the header byte, path, or transport codes. This
  means the same logical message received via different routes produces the
  same hash.
- The hash does NOT include the route type or version. Only the payload type
  and payload content determine the hash.
- For TRACE packets, including path_len ensures that the same trace payload
  at different stages of traversal produces different hashes.

### Cross-References

- [Section 10: Trace](10-payload-trace.md) — TRACE packet special handling
- Test vectors: [`corpus/crypto/sha256/packet-hash.json`](https://github.com/swaits/meshcore-spec/blob/main/versions/v0.1.0/corpus/crypto/sha256/packet-hash.json)

### Reference Implementation

- `Packet::calculatePacketHash()` in `src/Packet.cpp`
- `MeshTables::hasSeen()` — Deduplication table lookup

# MeshCore Protocol Specification

## Section 5: Payload — Advertisement

### Overview

The advertisement payload allows a node to announce its identity to the mesh. It
contains the node's Ed25519 public key, a timestamp, a signature proving
ownership of the key, and optional application data describing the node's type,
location, features, and name.

### Payload Type

Header payload type field: `0x04` (ADVERT)

### Wire Format

```
 0                                                              31
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
|                   Ed25519 Public Key (32 bytes)               |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Timestamp (uint32_le)                       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
|                   Ed25519 Signature (64 bytes)                |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                   App Data (0-32 bytes)                       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### Fields

| Field | Offset | Size | Type | Description |
|-------|--------|------|------|-------------|
| pub_key | 0 | 32 bytes | raw | Ed25519 public key of the advertising node |
| timestamp | 32 | 4 bytes | uint32_le | Unix epoch timestamp of advertisement creation |
| signature | 36 | 64 bytes | raw | Ed25519 signature (see Signature section below) |
| app_data | 100 | 0-32 bytes | structured | Optional application data (see App Data section below) |

### Minimum and Maximum Sizes

- Minimum payload: 100 bytes (pub_key + timestamp + signature, no app_data)
- Maximum payload: 132 bytes (100 + MAX_ADVERT_DATA_SIZE of 32)

### Signature

The signature is computed over the concatenation of:

```
message = pub_key(32) || timestamp_le(4) || app_data(0-32)
```

The node signs this message using its Ed25519 private key. Receivers MUST verify
the signature using the public key from the payload. Packets with invalid
signatures MUST be discarded.

### App Data Format

When present (payload_len > 100), app_data is a structured field beginning with
a flags byte:

```
 Bit:  7       6       5       4       3   2   1   0
     +-------+-------+-------+-------+---+---+---+---+
     |has_   |has_   |has_   |has_   |    Node Type   |
     |name   |feat2  |feat1  |loc    |   (4 bits)     |
     +-------+-------+-------+-------+---+---+---+---+
```

| Field | Offset | Size | Condition | Type | Description |
|-------|--------|------|-----------|------|-------------|
| flags | 0 | 1 byte | Always | uint8 | See bit layout above |
| latitude | 1 | 4 bytes | flags bit 4 set | int32_le | Latitude × 1,000,000 |
| longitude | 5 | 4 bytes | flags bit 4 set | int32_le | Longitude × 1,000,000 |
| feat1 | varies | 2 bytes | flags bit 5 set | uint16_le | Feature field 1 |
| feat2 | varies | 2 bytes | flags bit 6 set | uint16_le | Feature field 2 |
| name | varies | remaining | flags bit 7 set | UTF-8 | Node name (no null terminator) |

Fields appear in the order listed. The offset of each field depends on which
preceding optional fields are present.

### Node Types (flags bits 0-3)

| Value | Name | Description |
|-------|------|-------------|
| 0 | None | Unspecified |
| 1 | Chat | Chat client node |
| 2 | Repeater | Mesh repeater node |
| 3 | Room | Room server node |
| 4 | Sensor | Sensor node |

### Decoding Algorithm

1. Read 32 bytes as pub_key.
2. Read 4 bytes as timestamp (uint32_le).
3. Read 64 bytes as signature.
4. If offset (100) > payload_len, the packet is INVALID (incomplete).
5. If offset (100) == payload_len, there is no app_data. Done.
6. Read remaining bytes as app_data (up to MAX_ADVERT_DATA_SIZE = 32 bytes).
   If more than 32 bytes remain, implementations MUST truncate to 32.
7. Construct the signature verification message: pub_key || timestamp_le || app_data.
8. Verify the Ed25519 signature. If invalid, the receiver MUST discard the packet.
9. Parse app_data:
   a. Read 1 byte as flags.
   b. If flags bit 4 set: read 4 bytes latitude (int32_le), 4 bytes longitude (int32_le).
   c. If flags bit 5 set: read 2 bytes feat1 (uint16_le).
   d. If flags bit 6 set: read 2 bytes feat2 (uint16_le).
   e. If flags bit 7 set: read remaining bytes as UTF-8 name.

### Cross-References

- [Section 15: Identity](15-identity.md) — Ed25519 key management
- [Section 14: Cryptography](14-crypto.md) — Signature operations
- Test vectors: [`corpus/payloads/advert/`](https://github.com/swaits/meshcore-spec/tree/main/corpus/payloads/advert/)

### Reference Implementation

- `Mesh::createAdvert()` in `src/Mesh.cpp` — Encoding
- `Mesh::onRecvPacket()`, case `PAYLOAD_TYPE_ADVERT` in `src/Mesh.cpp` — Decoding and verification

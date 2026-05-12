# MeshCore Protocol Specification

## Section 13: Payload — Raw Custom

### Overview

The RAW_CUSTOM payload carries application-defined raw bytes with no prescribed
structure. It is intended for applications that implement their own encryption,
framing, or payload formats on top of the MeshCore transport.

### Payload Type

Header payload type field: `0x0F` (RAW_CUSTOM)

### Wire Format

```
 0
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|     Raw Data (1-184 bytes)    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### Fields

| Field | Offset | Size | Type | Description |
|-------|--------|------|------|-------------|
| data | 0 | 1-184 bytes | raw | Application-defined payload |

### Routing

In the current reference implementation, RAW_CUSTOM packets are only processed
when received via direct routing. They are NOT flood-routed.

### Constraints

- Payload MUST be at least 1 byte.
- Maximum payload: 184 bytes (MAX_PACKET_PAYLOAD).
- Maximum total data: limited by `sizeof(Packet::payload)` which is
  MAX_PACKET_PAYLOAD (184).

### Cross-References

- Test vectors: [`corpus/payloads/raw-custom/`](https://github.com/swaits/meshcore-spec/tree/main/versions/v0.1.0/corpus/payloads/raw-custom/)

### Reference Implementation

- `Mesh::createRawData()` in `src/Mesh.cpp` — Encoding
- `Mesh::onRecvPacket()`, case `PAYLOAD_TYPE_RAW_CUSTOM` — Processing (direct only)

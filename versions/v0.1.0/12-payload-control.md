# MeshCore Protocol Specification

## Section 12: Payload — Control

### Overview

The CONTROL payload carries control and discovery data. Control packets are raw
byte payloads whose structure is determined by the first byte. A subset of
control packets (those with bit 7 of the first byte set) are restricted to
zero-hop delivery only.

### Payload Type

Header payload type field: `0x0B` (CONTROL)

### Wire Format

```
 0
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Control Byte |  Data...      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### Fields

| Field | Offset | Size | Type | Description |
|-------|--------|------|------|-------------|
| control_byte | 0 | 1 byte | uint8 | Control type identifier |
| data | 1 | variable | raw | Control-specific data |

### Zero-Hop Restriction

When bit 7 (`0x80`) of the control byte is set, the packet is restricted to
zero-hop delivery only. The reference implementation enforces this:

- If `(payload[0] & 0x80) != 0` AND the packet is direct-routed:
  - It is processed only if `getPathHashCount() == 0`.
  - It is NOT forwarded to other nodes.

### Discovery Protocols

Control packets are commonly used for node discovery. The specific sub-protocol
formats are application-defined, but typically include:

- **Discovery Request**: Sent zero-hop to find nearby nodes
- **Discovery Response**: Contains node type, name, SNR, and other metadata

### Encoding

1. Construct the raw control data bytes.
2. If the control packet should be zero-hop only, set bit 7 of the first byte.
3. Copy data to payload, set payload_len.

### Constraints

- Payload MUST be at least 1 byte (the control byte).
- Maximum payload: 184 bytes (MAX_PACKET_PAYLOAD).

### Cross-References

- [Section 17: Routing](17-routing.md) — Zero-hop delivery
- Test vectors: [`corpus/payloads/control/`](https://github.com/swaits/meshcore-spec/tree/v0.1.0/corpus/payloads/control/)

### Reference Implementation

- `Mesh::createControlData()` in `src/Mesh.cpp` — Encoding
- `Mesh::onRecvPacket()`, CONTROL handling — Zero-hop check and delivery

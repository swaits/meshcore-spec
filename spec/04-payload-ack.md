# MeshCore Protocol Specification

## Section 4: Payload — ACK

### Overview

The ACK (acknowledgment) payload is the simplest payload type. It consists of a
single 4-byte CRC value used to confirm receipt of a previously sent message.
The CRC is computed by the sender from the original message's timestamp, text,
and sender public key.

### Payload Type

Header payload type field: `0x03` (ACK)

### Wire Format

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                      ACK CRC (uint32_le)                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### Fields

| Field | Offset | Size | Type | Description |
|-------|--------|------|------|-------------|
| ack_crc | 0 | 4 bytes | uint32_le | CRC identifying the acknowledged message |

### Encoding

1. Compute the 4-byte CRC value for the message being acknowledged.
2. Write the CRC as a little-endian 32-bit unsigned integer.
3. Set payload_len to 4.

### Decoding

1. Read 4 bytes from the payload as a little-endian uint32.
2. If fewer than 4 bytes are available, the packet is INVALID.

### Constraints

- The payload MUST be exactly 4 bytes.
- Implementations SHOULD log or discard ACK packets with payload_len < 4.

### Cross-References

- [Section 1: Wire Format](01-wire-format.md) — Packet framing
- [Section 11: Multipart](11-payload-multipart.md) — Multipart ACK encoding
- Test vectors: `corpus/payloads/ack/`

### Reference Implementation

- `Mesh::createAck()` in `src/Mesh.cpp`
- ACK reception in `Mesh::onRecvPacket()`, case `PAYLOAD_TYPE_ACK`

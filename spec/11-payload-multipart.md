# MeshCore Protocol Specification

## Section 11: Payload — Multipart

### Overview

The MULTIPART payload wraps another payload type to indicate it is part of a
multi-packet sequence. The first byte encodes the number of remaining packets in
the sequence and the sub-payload type. Currently, only multipart ACK is defined
in the reference implementation.

### Payload Type

Header payload type field: `0x0A` (MULTIPART)

### Wire Format

```
 0                   1
 0 1 2 3 4 5 6 7 8 9 0 ...
+-+-+-+-+-+-+-+-+-+-+-+-+
|Rem|  SubType  | Sub-payload  |
+-+-+-+-+-+-+-+-+-+-+-+-+
```

First byte encoding:

```
  Bit:  7   6   5   4   3   2   1   0
      +---+---+---+---+---+---+---+---+
      | Remaining (4) |  Sub-Type (4) |
      +---+---+---+---+---+---+---+---+
```

### Fields

| Field | Offset | Size | Type | Description |
|-------|--------|------|------|-------------|
| remaining | 0 (bits 4-7) | 4 bits | uint | Number of remaining packets in sequence (0-15) |
| sub_type | 0 (bits 0-3) | 4 bits | uint | Payload type of the wrapped content |
| sub_payload | 1 | variable | raw | The wrapped payload data |

```
first_byte = (remaining << 4) | (sub_type & 0x0F)
```

### Multipart ACK

The only currently defined multipart sub-type is ACK (sub_type = 0x03):

```
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  (rem<<4)|0x03|                ACK CRC (uint32_le)            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

Total payload: 5 bytes (1 byte header + 4 byte CRC).

Multipart ACKs are used to send additional ACK retransmissions for reliability.
The `remaining` field indicates how many more ACK packets follow this one.

### Encoding (Multipart ACK)

1. Set first byte to `(remaining << 4) | PAYLOAD_TYPE_ACK`.
2. Copy the 4-byte ACK CRC starting at offset 1.
3. Set payload_len to 5.

### Decoding (Multipart ACK)

1. Read first byte. Extract remaining = byte >> 4, sub_type = byte & 0x0F.
2. If sub_type == 0x03 (ACK) and payload_len >= 5:
   a. Read 4 bytes at offset 1 as ACK CRC (uint32_le).
3. For other sub_types: reserved for future use.

### Constraints

- Payload MUST be at least 2 bytes (1 header + 1 sub-payload minimum).
- For multipart ACK, payload MUST be at least 5 bytes.

### Cross-References

- [Section 4: ACK](04-payload-ack.md) — ACK CRC format
- Test vectors: `corpus/payloads/multipart/`

### Reference Implementation

- `Mesh::createMultiAck()` in `src/Mesh.cpp` — Encoding
- `Mesh::onRecvPacket()`, case `PAYLOAD_TYPE_MULTIPART` — Decoding

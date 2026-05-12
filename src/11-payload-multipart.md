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
The `remaining` field indicates how many more ACK packets follow this one,
counting down: a chain of K extra copies is emitted as MULTIPART with
`remaining = K, K-1, …, 1`, followed by exactly one final plain
`PAYLOAD_TYPE_ACK` packet (NOT a MULTIPART with `remaining = 0`). All copies
in the chain carry the same `ack_crc`. Receivers MUST treat the first copy
received as the authoritative ACK and dedup subsequent copies by `ack_crc`
at the application layer.

### Multipart ACK Usage Constraints

- A sender MUST only emit MULTIPART-wrapped ACKs on direct-routed return
  paths (i.e., when a direct path to the original sender is known). When the
  return path is unknown, the sender MUST fall back to emitting a plain
  PAYLOAD_TYPE_ACK via flood routing. This reflects the firmware behavior in
  `Mesh::routeDirectRecvAcks()` (which emits MULTIPART copies only when a
  direct path is available) and `BaseChatMesh::sendAckTo()` (which falls back
  to `sendFloodScoped()` when `out_path_len == OUT_PATH_UNKNOWN`).
- All MULTIPART-ACK copies and the final plain ACK for the same acknowledged
  message carry an identical 4-byte `ack_crc`. Receivers MUST treat them as
  the same logical ACK: the first one received satisfies the acknowledgment,
  and subsequent duplicates MUST be deduplicated per
  [Section 16](16-packet-hash.md) (each copy has a distinct packet hash
  because the wrapper byte differs, so ordinary dedup does not suppress them
  on the wire — application-level dedup by `ack_crc` is required).
- The typical inter-copy delay in the reference implementation is
  approximately 300 ms plus the direct retransmit delay
  (`Mesh::routeDirectRecvAcks()`); exact timing is implementation-defined.
- The number of extra copies is configured via `getExtraAckTransmitCount()`
  and is implementation-defined. The firmware default is 0 (plain ACK only).

A receiver MUST NOT infer delivery reliability from the `remaining` counter
alone: the counter is a hint about how many additional copies the sender
intends to emit, not a guarantee that they will arrive.

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
- Test vectors: [`corpus/payloads/multipart/`](https://github.com/swaits/meshcore-spec/tree/main/corpus/payloads/multipart/)

### Reference Implementation

- `Mesh::createMultiAck()` in `src/Mesh.cpp` — Encoding
- `Mesh::routeDirectRecvAcks()` in `src/Mesh.cpp` — Direct-only gating and
  inter-copy spacing
- `BaseChatMesh::sendAckTo()` in `src/helpers/BaseChatMesh.cpp` — Flood
  fallback when no direct return path is known
- `Mesh::onRecvPacket()`, case `PAYLOAD_TYPE_MULTIPART` — Decoding

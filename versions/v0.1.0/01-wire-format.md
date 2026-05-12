# MeshCore Protocol Specification

## Section 1: Wire Format

### Overview

A MeshCore packet is the fundamental transmission unit. It consists of a 1-byte
header, an optional 4-byte transport codes field, a 1-byte path length, a
variable-length path, and a variable-length payload. The maximum packet size on
the wire is 255 bytes (MAX_TRANS_UNIT).

### Packet Layout

```
 0                   1                   2
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 ...
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|    Header     | Transport Codes (opt, 4B) |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Path Length   |     Path (variable)      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|            Payload (variable)             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

The fields appear in this order on the wire:

```
[header(1)][transport_codes(4)?][path_len(1)][path(0-64)][payload(1-184)]
```

### Field Summary

| Field | Size | Required | Description |
|-------|------|----------|-------------|
| Header | 1 byte | Yes | Route type, payload type, protocol version (see [Section 2](02-header.md)) |
| Transport Codes | 4 bytes | Conditional | Two uint16_le values; present only when route type is `TRANSPORT_FLOOD` (0x00) or `TRANSPORT_DIRECT` (0x03) |
| Path Length | 1 byte | Yes | Encoded hash count and hash size (see [Section 3](03-path.md)) |
| Path | 0-64 bytes | Yes | Sequence of node hashes; length = hash_count × hash_size |
| Payload | 1-184 bytes | Yes | Packet data; structure depends on payload type |

### Transport Codes

Transport codes are present if and only if the route type (header bits 0-1) is
`TRANSPORT_FLOOD` (0x00) or `TRANSPORT_DIRECT` (0x03).

When present, transport codes consist of two little-endian 16-bit unsigned
integers, for a total of 4 bytes:

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|        Code 1 (uint16_le)     |        Code 2 (uint16_le)     |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

- **Code 1**: Calculated from regional scope parameters
- **Code 2**: Reserved (typically 0)

When transport codes are not present (route types `FLOOD` and `DIRECT`), the
implementation MUST set both transport code values to zero internally.

### Encoding Algorithm

To encode a packet to wire format:

1. Write the header byte.
2. If the route type is `TRANSPORT_FLOOD` or `TRANSPORT_DIRECT`:
   a. Write transport_codes[0] as uint16_le (2 bytes).
   b. Write transport_codes[1] as uint16_le (2 bytes).
3. Write the path_len byte.
4. Calculate path byte length as `hash_count × hash_size` (see [Section 3](03-path.md)).
5. Write `path_byte_length` bytes from the path array.
6. Write `payload_len` bytes from the payload array.

The total wire length is:
```
1 + (hasTransportCodes ? 4 : 0) + 1 + path_byte_length + payload_len
```

This MUST NOT exceed MAX_TRANS_UNIT (255) bytes.

### Decoding Algorithm

To decode a packet from wire format:

1. Read 1 byte as the header. Extract route type from bits 0-1.
2. If route type is `TRANSPORT_FLOOD` (0x00) or `TRANSPORT_DIRECT` (0x03):
   a. Read 2 bytes as transport_codes[0] (uint16_le).
   b. Read 2 bytes as transport_codes[1] (uint16_le).
   Otherwise, set both transport codes to zero.
3. Read 1 byte as path_len.
4. Validate path_len (see [Section 3](03-path.md)):
   a. Extract hash_size = (path_len >> 6) + 1. If hash_size is 4, the packet
      is INVALID.
   b. Extract hash_count = path_len & 63.
   c. If hash_count × hash_size > MAX_PATH_SIZE (64), the packet is INVALID.
5. Calculate path_byte_length = hash_count × hash_size.
6. Read path_byte_length bytes as the path.
7. Let `i` be the current read position. If `i >= total_length`, the packet is
   INVALID (payload MUST contain at least 1 byte).
8. Calculate payload_len = total_length - i.
9. If payload_len > MAX_PACKET_PAYLOAD (184), the packet is INVALID.
10. Read payload_len bytes as the payload.

### Size Constraints

| Constraint | Value | Enforcement |
|-----------|-------|-------------|
| Maximum wire length | 255 bytes | Encoder MUST NOT produce packets exceeding this |
| Maximum payload | 184 bytes | Decoder MUST reject payloads exceeding this |
| Maximum path | 64 bytes | Decoder MUST reject paths exceeding this |
| Minimum payload | 1 byte | Decoder MUST reject packets with zero-length payload |
| Minimum packet | 3 bytes | Header (1) + path_len (1) + payload (1 minimum) |

### Error Conditions

A conforming decoder MUST reject packets with any of the following:

1. Total wire length less than 3 bytes (no room for header + path_len + payload)
2. Total wire length less than minimum required for the route type:
   - 3 bytes for FLOOD or DIRECT
   - 7 bytes for TRANSPORT_FLOOD or TRANSPORT_DIRECT (adds 4 transport code bytes)
3. Invalid path_len encoding (see [Section 3](03-path.md))
4. Path byte length exceeds remaining bytes
5. Zero-length payload after header, transport codes, path_len, and path
6. Payload length exceeding MAX_PACKET_PAYLOAD (184)

### Cross-References

- [Section 2: Header](02-header.md) — Header byte encoding details
- [Section 3: Path](03-path.md) — Path length encoding and path field
- Test vectors: `corpus/wire-format/framing/`, `corpus/wire-format/invalid/`

### Reference Implementation

- `Packet::writeTo()` in `src/Packet.cpp` — Encoding
- `Packet::readFrom()` in `src/Packet.cpp` — Decoding
- `Packet::getRawLength()` in `src/Packet.cpp` — Wire length calculation

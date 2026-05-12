# MeshCore Protocol Specification

## Section 2: Header

### Overview

The header is the first byte of every MeshCore packet. It encodes three fields
using bit packing: the route type (2 bits), the payload type (4 bits), and the
protocol version (2 bits).

### Bit Layout

```
  Bit:  7   6   5   4   3   2   1   0
      +---+---+---+---+---+---+---+---+
      | V1  V0| P3  P2  P1  P0| R1  R0|
      +---+---+---+---+---+---+---+---+
             |         |           |
             |         |           +-- Route Type (bits 0-1)
             |         +-------------- Payload Type (bits 2-5)
             +------------------------ Protocol Version (bits 6-7)
```

The header byte value is computed as:

```
header = (version << 6) | (payload_type << 2) | route_type
```

And fields are extracted as:

```
route_type   = header & 0x03
payload_type = (header >> 2) & 0x0F
version      = (header >> 6) & 0x03
```

### Route Type (bits 0-1)

The route type determines how the packet is routed through the mesh and whether
transport codes are present.

| Value | Name | Transport Codes | Description |
|-------|------|----------------|-------------|
| 0x00 | TRANSPORT_FLOOD | Yes (4 bytes) | Flood routing with transport codes for regional scoping |
| 0x01 | FLOOD | No | Standard flood routing; path is built up by intermediate nodes |
| 0x02 | DIRECT | No | Direct routing; path is supplied by the sender |
| 0x03 | TRANSPORT_DIRECT | Yes (4 bytes) | Direct routing with transport codes |

Transport codes MUST be present in the wire format when route type is 0x00 or
0x03, and MUST NOT be present when route type is 0x01 or 0x02.

### Payload Type (bits 2-5)

The payload type identifies the structure of the payload data.

| Value | Name | Description |
|-------|------|-------------|
| 0x00 | REQUEST | Encrypted request (dest_hash + src_hash + MAC + ciphertext) |
| 0x01 | RESPONSE | Encrypted response to REQ or ANON_REQ |
| 0x02 | TXT_MSG | Encrypted text message |
| 0x03 | ACK | Simple acknowledgment (4-byte CRC) |
| 0x04 | ADVERT | Node identity advertisement |
| 0x05 | GRP_TXT | Encrypted group text message |
| 0x06 | GRP_DATA | Encrypted group datagram |
| 0x07 | ANON_REQ | Anonymous request (full public key instead of hash) |
| 0x08 | PATH | Encrypted returned path information |
| 0x09 | TRACE | Path trace with per-hop SNR collection |
| 0x0A | MULTIPART | One part of a multi-packet sequence |
| 0x0B | CONTROL | Control/discovery packet |
| 0x0C | (reserved) | Reserved for future use |
| 0x0D | (reserved) | Reserved for future use |
| 0x0E | (reserved) | Reserved for future use |
| 0x0F | RAW_CUSTOM | Custom raw bytes for application-defined payloads |

Implementations SHOULD silently discard packets with reserved payload type values
(0x0C-0x0E) unless they have explicit support for extended types.

### Protocol Version (bits 6-7)

| Value | Name | Description |
|-------|------|-------------|
| 0x00 | V1 | Current version: 1-byte src/dest hashes, 2-byte MAC |
| 0x01 | V2 | Reserved for future use |
| 0x02 | V3 | Reserved for future use |
| 0x03 | V4 | Reserved for future use |

Implementations MUST support version 0x00 (V1). Implementations SHOULD reject
packets with unrecognized version values.

### Special Header Values

The header value `0xFF` is used internally as a "do not retransmit" marker. This
is an in-memory sentinel only and MUST NOT appear on the wire. A header of
`0xFF` would decode as version=3, payload_type=0x0F (RAW_CUSTOM), route_type=3
(TRANSPORT_DIRECT).

### Encoding Examples

| Header Byte | Binary | Version | Payload Type | Route Type |
|-------------|--------|---------|-------------|------------|
| `0x01` | `00 000000 01` | V1 (0) | REQUEST (0) | FLOOD (1) |
| `0x05` | `00 000001 01` | V1 (0) | RESPONSE (1) | FLOOD (1) |
| `0x09` | `00 000010 01` | V1 (0) | TXT_MSG (2) | FLOOD (1) |
| `0x0D` | `00 000011 01` | V1 (0) | ACK (3) | FLOOD (1) |
| `0x11` | `00 000100 01` | V1 (0) | ADVERT (4) | FLOOD (1) |
| `0x0C` | `00 000011 00` | V1 (0) | ACK (3) | TRANSPORT_FLOOD (0) |
| `0x0E` | `00 000011 10` | V1 (0) | ACK (3) | DIRECT (2) |
| `0x0F` | `00 000011 11` | V1 (0) | ACK (3) | TRANSPORT_DIRECT (3) |
| `0x4D` | `01 000011 01` | V2 (1, reserved) | ACK (3) | FLOOD (1) |

### Cross-References

- [Section 1: Wire Format](01-wire-format.md) — Overall packet structure
- [Section 3: Path](03-path.md) — Path encoding
- Test vectors: [`corpus/wire-format/header/`](https://github.com/swaits/meshcore-spec/tree/main/corpus/wire-format/header/)

### Reference Implementation

- `Packet::getRouteType()` in `src/Packet.h` — `header & 0x03`
- `Packet::getPayloadType()` in `src/Packet.h` — `(header >> 2) & 0x0F`
- `Packet::getPayloadVer()` in `src/Packet.h` — `(header >> 6) & 0x03`
- `Packet::hasTransportCodes()` in `src/Packet.h` — route type 0x00 or 0x03
- Route type constants in `src/Packet.h`
- Payload type constants in `src/Packet.h`

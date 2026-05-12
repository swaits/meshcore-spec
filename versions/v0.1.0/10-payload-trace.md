# MeshCore Protocol Specification

## Section 10: Payload — Trace

### Overview

The TRACE payload enables path discovery with per-hop signal quality measurement.
A trace packet travels along a specified direct path, and each intermediate node
appends its received SNR value to the packet's path field. When the trace reaches
its final hop, the accumulated SNR values and node hashes are delivered.

### Payload Type

Header payload type field: `0x09` (TRACE)

### Wire Format

The trace payload has a fixed 9-byte header followed by an optional path hashes
section (appended when sent via direct routing):

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        Tag (uint32_le)                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                     Auth Code (uint32_le)                     |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|     Flags     |          Path Hashes (variable)               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### Fields

| Field | Offset | Size | Type | Description |
|-------|--------|------|------|-------------|
| tag | 0 | 4 bytes | uint32_le | Random tag set by the initiator for correlation |
| auth_code | 4 | 4 bytes | uint32_le | Authentication code |
| flags | 8 | 1 byte | uint8 | Flags (see below) |
| path_hashes | 9 | variable | raw | Node hashes for the path to trace (appended for direct send) |

### Flags Field

```
  Bit:  7   6   5   4   3   2   1   0
      +---+---+---+---+---+---+---+---+
      |      Reserved         | S1  S0|
      +---+---+---+---+---+---+---+---+
```

| Bits | Description |
|------|-------------|
| 0-1 | Path hash size for the trace path hashes (as a power of 2: 0=1 byte, 1=2 bytes, 2=4 bytes) |
| 2-7 | Reserved (must be zero) |

Note: The flags field path hash size encoding (`1 << (flags & 0x03)`) differs
from the packet path_len encoding (`(code >> 6) + 1`).

### Direct Sending

When a TRACE packet is sent via direct routing, the path hashes are appended
directly to the payload (after the 9-byte header), not placed in the packet's
path field. The packet's path field is instead used to accumulate SNR values
from intermediate nodes.

```
On creation:  payload = [tag(4)][auth_code(4)][flags(1)]  (9 bytes)
On sendDirect: payload += path_hashes                      (9 + N bytes)
               packet.path_len = 0                         (path used for SNR)
```

### SNR Accumulation

As each intermediate node forwards a TRACE packet, it appends its received SNR
value as a single signed byte to the packet's path field:

```
path[path_len++] = (int8_t)(SNR × 4)
```

The SNR value is stored as SNR × 4 for 0.25 dB precision, matching the format
used in RxMeta frames.

### Trace Completion

A TRACE is considered complete when the path_len counter (used as an offset into
the path hashes in the payload) reaches or exceeds the remaining path hashes.
At that point, `onTraceRecv` is called with:
- The accumulated SNR values (in packet.path)
- The path hashes (in packet.payload, after byte 9)
- The path length (number of hops traversed)

### Minimum Size

- Minimum payload: 9 bytes (tag + auth_code + flags, no path hashes)

### Cross-References

- [Section 16: Packet Hash](16-packet-hash.md) — TRACE packets include path_len in hash
- Test vectors: [`corpus/payloads/trace/`](https://github.com/swaits/meshcore-spec/tree/v0.1.0/corpus/payloads/trace/)

### Reference Implementation

- `Mesh::createTrace()` in `src/Mesh.cpp` — Creation (9-byte base)
- `Mesh::sendDirect()` — Path appended to payload for TRACE type
- `Mesh::onRecvPacket()`, TRACE handling — SNR accumulation and completion check

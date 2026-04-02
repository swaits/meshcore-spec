# MeshCore Protocol Specification

## Section 17: Routing

### Overview

MeshCore supports two routing modes: flood routing and direct routing. Flood
routing broadcasts packets to all neighbors, building up a path as the packet
propagates. Direct routing sends packets along a pre-determined path.

### Flood Routing

In flood routing, the sender emits a packet with an empty path. Each
intermediate node that forwards the packet appends its hash to the path before
retransmitting.

**Sending (flood)**:

1. Set route type to FLOOD (0x01) or TRANSPORT_FLOOD (0x00).
2. Set path to empty: `setPathHashSizeAndCount(hash_size, 0)`.
3. Transmit the packet.

**Forwarding (flood)**:

1. Receive a flood-routed packet.
2. Check the deduplication table. If already seen, discard.
3. Process the packet (decrypt if addressed to this node, etc.).
4. If the packet should be forwarded (node is a repeater):
   a. Verify `(hash_count + 1) × hash_size <= MAX_PATH_SIZE`.
   b. Append this node's hash at `path[hash_count × hash_size]`.
   c. Increment hash_count.
   d. Retransmit with a random delay.

**Path growth**: The path grows by one hash per hop. When the path reaches
MAX_PATH_SIZE (64 bytes), no more nodes can be appended and the packet stops
propagating.

### Direct Routing

In direct routing, the sender provides the complete path. Each intermediate
node checks whether it is the next hop, removes itself from the path, and
forwards to the next node.

**Sending (direct)**:

1. Set route type to DIRECT (0x02) or TRANSPORT_DIRECT (0x03).
2. Set the path to the destination's known route.
3. Transmit the packet.

**Forwarding (direct)**:

1. Receive a direct-routed packet.
2. Check if the first hash in the path matches this node.
3. If yes, and the node allows forwarding:
   a. Remove the first hash from the path (shift remaining hashes left).
   b. Decrement hash_count.
   c. Retransmit.
4. If no, discard (this node is not the next hop).

**Path removal** (`removeSelfFromPath`):

1. Decrement hash_count.
2. Shift the path array: for each index k from 0 to (hash_count × hash_size),
   copy `path[k + hash_size]` to `path[k]`.

### Zero-Hop Delivery

Zero-hop packets are direct-routed packets with hash_count = 0. They reach only
immediate neighbors (nodes within radio range). Used for:

- Control packets with bit 7 set in the control byte
- Discovery protocols
- Local-only operations

### Transport Codes

Transport codes (present in TRANSPORT_FLOOD and TRANSPORT_DIRECT) enable
regional scoping. Nodes can filter packets based on transport codes, accepting
only packets from their region.

### TRACE Routing

TRACE packets are a special case. They are sent via direct routing, but instead
of the normal path field, the path hashes are appended to the payload. The
packet's path field is repurposed to accumulate SNR values from each hop
(see [Section 10](10-payload-trace.md)).

### Retransmission Priority

Packets are prioritized for transmission:

| Priority | Packet Type | Description |
|----------|-------------|-------------|
| 0 (highest) | Direct routed | Routed traffic |
| 1 | Path return, standard | Most flood packets |
| 2 | Path return (flood) | Path packets |
| 3 | Advertisement | De-prioritized |
| 5 | Trace | Trace forwarding |
| N (hash_count) | Flood forwarded | Lower priority for more distant sources |

### Packet Deduplication

Before processing or forwarding any packet, nodes check if the packet has
already been seen using `hasSeen()` with the packet hash from
[Section 16](16-packet-hash.md). This prevents infinite loops in flood routing.

Once a packet is marked as seen, it is NOT forwarded again even if received via
a different route. This is a "first packet wins" approach.

### Cross-References

- [Section 1: Wire Format](01-wire-format.md) — Packet structure
- [Section 3: Path](03-path.md) — Path encoding
- [Section 10: Trace](10-payload-trace.md) — TRACE routing special case
- [Section 16: Packet Hash](16-packet-hash.md) — Deduplication

### Reference Implementation

- `Mesh::sendFlood()` in `src/Mesh.cpp` — Flood send
- `Mesh::sendDirect()` in `src/Mesh.cpp` — Direct send
- `Mesh::sendZeroHop()` in `src/Mesh.cpp` — Zero-hop send
- `Mesh::routeRecvPacket()` in `src/Mesh.cpp` — Flood forwarding
- `Mesh::removeSelfFromPath()` in `src/Mesh.cpp` — Path manipulation
- `Mesh::onRecvPacket()` in `src/Mesh.cpp` — Direct forwarding

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

### Sender Behavior (Informational)

This section documents sender-side behavior that is not fully constrained by
the wire protocol but is common across interoperating implementations. The
reference firmware establishes the baseline; client implementations SHOULD
follow these patterns to interoperate cleanly. Specific numeric tuning
parameters (timeouts, queue sizes, retry counts) are implementation-defined.

#### Path Learning

- When a node receives a flood-routed packet from a peer, the accumulated
  `path` field records the hops the packet traversed. The receiving node
  SHOULD cache the **reversed** path keyed by the peer's source hash and
  subsequently use that cached path to send direct-routed traffic back.
- When multiple paths are observed for the same peer, the **reference
  implementation unconditionally replaces** the cached path with the most
  recently observed one (`BaseChatMesh::onContactPathRecv()` in
  `src/helpers/BaseChatMesh.cpp` — its source comment explicitly flags
  hash-size or SNR-based selection as future work). Implementations MAY
  layer a quality heuristic on top (e.g., prefer larger hash sizes or
  better SNR margin) if they store and compare multiple candidate paths,
  but this is not part of the reference behavior and the exact policy is
  implementation-defined.
- Cached paths in the reference implementation do **not** expire on a
  timer; they live as long as the contact entry, and are overwritten
  whenever a fresher path is observed. Implementations MAY add a TTL or
  age-based eviction policy as an extension. The reference implementation
  does not persist paths across reboots.

#### PATH_RETURN

After receiving a flood-routed DM, a receiver MAY proactively emit a
PAYLOAD_TYPE_PATH packet ([Section 9](09-payload-path.md)) that embeds the
reversed path and optionally an ACK as extra data. This lets the original
sender learn a direct return path before its first reply, converting
subsequent traffic from flood to direct routing. See
`BaseChatMesh::onPeerDataRecv()` and `Mesh::createPathReturn()`.

The reference implementation schedules the PATH_RETURN transmission with a
small delay (`TXT_ACK_DELAY`, default 200 ms) to avoid colliding with other
packets the receiver is about to emit. Exact timing is
implementation-defined; the goal is to space PATH_RETURN, ACK, and any
application reply across distinct on-air slots.

#### Flood Fallback and Retries

- A sender SHOULD track outstanding DMs by their expected `ack_crc`
  (see [Section 4](04-payload-ack.md)) and retry transmissions that are not
  acknowledged within a timeout. Timeout values and backoff schedules are
  implementation-defined and typically depend on LoRa airtime parameters.
- On each retry, the sender MUST increment the `attempt` sub-field of
  `txt_type_attempt` (see
  [Section 6](06-payload-encrypted.md#plaintext-format-txt_msg)). The
  `timestamp` field MUST be held constant across retries of the same logical
  message. This changes the ACK CRC per attempt, letting the sender attribute
  a returned ACK to a specific transmission.
- After N unsuccessful direct-routed retries, the sender SHOULD discard the
  cached direct path and retry via flood routing, so that a stale cached path
  does not indefinitely block delivery. The value of N is
  implementation-defined (the reference is small — single-digit).
- On receipt of a matching ACK (plain or MULTIPART, per
  [Section 11](11-payload-multipart.md#multipart-ack-usage-constraints)),
  the sender MUST cancel any queued retries for that ACK CRC.

#### Transmission Priority (sender-originated)

Client implementations that maintain a TX queue SHOULD prioritize
sender-originated packets roughly as follows (highest first):

| Priority | Packet Type |
|----------|-------------|
| 0 | ACK (plain or MULTIPART) |
| 1 | PATH / PATH_RETURN |
| 2 | Direct-routed reply (DM) |
| 3 | Flood-routed reply (DM) |
| 4 | Request/response (e.g., login, keep-alive) |
| 5 | Group text / group data |
| 6 | Advertisement |

This ordering complements the forwarding-priority table above: ACKs and
PATH returns are time-sensitive and short; direct replies take precedence
over flood replies to reduce channel occupancy. Exact ordering and queue
depth are implementation-defined.

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

# MeshCore Protocol Specification

## Section 4: Payload — ACK

### Overview

The ACK (acknowledgment) payload is the simplest payload type. It consists of a
single 4-byte CRC value used to confirm receipt of a previously sent message.
The CRC is a truncated SHA-256 over the original TXT_MSG plaintext prefix
concatenated with the sender's public key.

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

### ACK CRC Computation

The 4-byte ACK CRC is computed as the first 4 bytes of a SHA-256 digest over
the acknowledged TXT_MSG's plaintext prefix followed by the **sender's**
Ed25519 public key:

```
ack_crc = SHA-256( plaintext_prefix || sender_pub_key )[0..3]
```

Where `plaintext_prefix` is the TXT_MSG plaintext up to and including the
message text, **excluding any trailing NUL terminator**:

```
plaintext_prefix = timestamp_le(4) || txt_type_attempt(1) || text
```

- `timestamp_le` and `txt_type_attempt` are defined in
  [Section 6](06-payload-encrypted.md#plaintext-format-txt_msg).
- `text` is the raw UTF-8 message bytes with no NUL terminator.
- `sender_pub_key` is the full 32-byte Ed25519 public key of the node that
  originated the TXT_MSG (i.e., the node expecting this ACK back).

For TXT_TYPE_SIGNED_PLAIN messages, the 4-byte signature prefix is included:

```
plaintext_prefix = timestamp_le(4) || txt_type_attempt(1) || signature(4) || text
ack_crc = SHA-256( plaintext_prefix || receiver_pub_key )[0..3]
```

Note the SIGNED_PLAIN variant hashes against the **receiver's** public key;
see `BaseChatMesh::onPeerDataRecv()`.

Because `txt_type_attempt` includes the 2-bit `attempt` counter, each retry
with an incremented `attempt` produces a different ACK CRC. This lets the
sender attribute each received ACK to a specific transmission attempt. See
[Section 6: Reliable DM Delivery](06-payload-encrypted.md#reliable-dm-delivery).

### Encoding

1. Compute the 4-byte CRC value for the message being acknowledged (above).
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
- Test vectors: [`corpus/payloads/ack/`](https://github.com/swaits/meshcore-spec/tree/main/corpus/payloads/ack/)

### Reference Implementation

- `Mesh::createAck()` in `src/Mesh.cpp` — Packet construction
- `BaseChatMesh::composeMsgPacket()` in `src/helpers/BaseChatMesh.cpp` —
  Sender-side expected-ACK computation (`expected_ack`)
- `BaseChatMesh::onPeerDataRecv()` in `src/helpers/BaseChatMesh.cpp` —
  Receiver-side ACK CRC computation (`ack_hash`)
- ACK reception in `Mesh::onRecvPacket()`, case `PAYLOAD_TYPE_ACK`

# MeshCore Protocol Specification

## Section 0: Overview

### Status

This document specifies the MeshCore mesh networking protocol as implemented in
the [reference firmware](https://github.com/meshcore-dev/MeshCore). It is
derived from the source code and official documentation, and serves as the
authoritative definition of the wire format for conformance testing.

### Scope

This specification covers:

- The packet wire format (framing, header, path, payload)
- All payload types and their binary encodings
- Cryptographic operations (encryption, signing, key exchange, hashing)
- The BLE/Serial companion protocol
- The KISS modem protocol
- The bridge protocol (RS232/ESP-NOW)

It does NOT cover:

- Application-level behavior (e.g., room server logic, repeater policies)
- Radio-layer parameters (LoRa spreading factor, bandwidth, frequency)
- Duty cycle management or transmission scheduling
- User interface or companion app behavior

### Terminology

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119).

Additional terms used throughout:

| Term | Definition |
|------|-----------|
| **Packet** | The fundamental transmission unit in MeshCore. |
| **Header** | The first byte of a packet, encoding route type, payload type, and protocol version. |
| **Path** | A sequence of node hashes representing the route a packet has taken or should follow. |
| **Hash** | A truncated prefix of a node's Ed25519 public key, used for routing. |
| **Payload** | The data portion of a packet, whose structure depends on the payload type. |
| **Transport Codes** | Optional 4-byte field present in transport-mode packets, used for regional scoping. |
| **MAC** | Message Authentication Code — a 2-byte truncated HMAC-SHA256 used for integrity verification. |
| **MTU** | Maximum Transmission Unit — 255 bytes for MeshCore. |
| **Flood Routing** | Routing mode where packets are broadcast and repeated by intermediate nodes, building up the path as they travel. |
| **Direct Routing** | Routing mode where the path is supplied by the sender and the packet follows a specific route. |

### Byte Order

All multi-byte integer fields in MeshCore are encoded in **little-endian** byte
order unless explicitly stated otherwise. The one exception is CayenneLPP sensor
data, which uses big-endian encoding.

### Notation

- Binary data is shown as hex bytes separated by spaces: `0D 00 EF BE AD DE`
- Bit fields are shown in binary with MSB first: `0bVVPPPPRR`
- Bit numbering is LSB = bit 0, MSB = bit 7
- Field sizes are in bytes unless noted as bits
- `[field(N)]` denotes a field of N bytes
- `[field(N)?]` denotes an optional field of N bytes

### Protocol Constants

These constants define the fundamental limits of the protocol:

| Constant | Value | Description |
|----------|-------|-------------|
| `MAX_TRANS_UNIT` | 255 | Maximum packet size on the wire (bytes) |
| `MAX_PACKET_PAYLOAD` | 184 | Maximum payload size (bytes) |
| `MAX_PATH_SIZE` | 64 | Maximum path size (bytes) |
| `PUB_KEY_SIZE` | 32 | Ed25519 public key size (bytes) |
| `PRV_KEY_SIZE` | 64 | Ed25519 private key size (bytes) |
| `SIGNATURE_SIZE` | 64 | Ed25519 signature size (bytes) |
| `CIPHER_KEY_SIZE` | 16 | AES-128 key size (bytes) |
| `CIPHER_BLOCK_SIZE` | 16 | AES-128 block size (bytes) |
| `CIPHER_MAC_SIZE` | 2 | Truncated HMAC-SHA256 MAC size (bytes) |
| `PATH_HASH_SIZE` | 1 | Default path hash size for v1 (bytes) |
| `MAX_HASH_SIZE` | 8 | Maximum hash size for deduplication (bytes) |
| `MAX_ADVERT_DATA_SIZE` | 32 | Maximum advertisement app data size (bytes) |

### Protocol Versions

The protocol version is encoded in bits 6-7 of the header byte:

| Version | Value | Status | Description |
|---------|-------|--------|-------------|
| V1 | `0x00` | Active | 1-byte src/dest hashes, 2-byte MAC |
| V2 | `0x01` | Reserved | Future (e.g., 2-byte hashes, 4-byte MAC) |
| V3 | `0x02` | Reserved | Future |
| V4 | `0x03` | Reserved | Future |

Currently only V1 is defined. Implementations MUST support V1.
Implementations SHOULD reject packets with unrecognized version values unless
they have explicit support for that version.

### Document Organization

| Section | Title | Description |
|---------|-------|-------------|
| 00 | Overview | This document |
| 01 | Wire Format | Packet framing and field layout |
| 02 | Header | Header byte encoding |
| 03 | Path | Path length encoding and path field |
| 04 | Payload: ACK | Acknowledgment payload |
| 05 | Payload: Advertisement | Node advertisement and app data |
| 06 | Payload: Encrypted | REQ/RESPONSE/TXT_MSG payloads |
| 07 | Payload: Anonymous Request | Anonymous request payload |
| 08 | Payload: Group | Group text and data payloads |
| 09 | Payload: Path Return | Encrypted path return payload |
| 10 | Payload: Trace | Path trace payload |
| 11 | Payload: Multipart | Multi-packet payload |
| 12 | Payload: Control | Control and discovery payloads |
| 13 | Payload: Raw Custom | Custom raw payload |
| 14 | Cryptography | AES-128, HMAC-SHA256, encrypt-then-MAC |
| 15 | Identity | Ed25519 keys, ECDH, key hashing |
| 16 | Packet Hash | SHA-256 deduplication hashing |
| 17 | Routing | Flood and direct routing behavior |
| 18 | Companion Protocol | BLE/Serial companion communication |
| 19 | KISS Protocol | KISS modem framing and extensions |
| 20 | Bridge Protocol | RS232/ESP-NOW bridge framing |

### References

- [MeshCore Firmware](https://github.com/meshcore-dev/MeshCore) — Reference C++ implementation
- [MeshCore Documentation](https://docs.meshcore.io) — Official protocol documentation
- [MeshCore.js](https://github.com/meshcore-dev/meshcore.js) — JavaScript implementation
- [meshcore-rs](https://github.com/Duncaen/meshcore-rs) — Rust implementation (community)
- [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) — Key words for requirement levels
- [RFC 8032](https://www.rfc-editor.org/rfc/rfc8032) — Ed25519 digital signatures
- [FIPS 197](https://csrc.nist.gov/publications/detail/fips/197/final) — AES specification
- [FIPS 180-4](https://csrc.nist.gov/publications/detail/fips/180/4/final) — SHA-256 specification

# MeshCore Protocol Specification

## Section 0: Overview

**Spec version:** `v0.1.0` &middot; see
[Spec Versions](#spec-versions) for the full list of frozen releases.

### Status and Provenance

> **This is an unofficial, independent specification.** It is **not** part of
> the upstream [MeshCore project](https://github.com/meshcore-dev/MeshCore),
> not affiliated with or endorsed by its maintainers, and not authored by
> them. Read this section before relying on the spec for anything
> load-bearing.

This document was primarily written by an AI (Claude, by Anthropic — mostly
the Opus 4.x family) under the direction of Stephen Waits, with human
proofreading and editing on top. Substantive edits — additions, audit passes,
errata fixes — are produced through model-driven analysis of the upstream
MeshCore C++ source and reviewed before commit.

The **upstream MeshCore C++ firmware is the source of truth** for all
protocol behavior. This spec is downstream and derivative. Whenever the spec
and the upstream C++ disagree, **upstream wins** — and a fix to this spec is
filed against this repo, not against MeshCore. Each substantive change in
[CHANGELOG.md](https://github.com/swaits/meshcore-spec/blob/main/CHANGELOG.md)
records the upstream commit hash it was validated against.

Refinements have also been driven in part by observations from building
DongLoRa firmware and apps against live MeshCore deployments. Where DongLoRa
behavior diverges from upstream, this spec follows upstream and treats the
DongLoRa side as a follow-up bug, not a spec change.

Conformance against the [test corpus](https://github.com/swaits/meshcore-spec/tree/main/corpus)
is a useful signal but **not a substitute** for cross-checking against
upstream firmware. If you find a divergence from upstream, please
[file an issue](https://github.com/swaits/meshcore-spec/issues) — that is
exactly the kind of report this project exists to catch.

### Spec Versions

The published site preserves prior spec versions alongside the rolling
`latest` build. The URL layout is:

- `https://swaits.github.io/meshcore-spec/latest/` — built from the tip of
  `main`. May change between any two visits.
- `https://swaits.github.io/meshcore-spec/v0.1.0/` (and likewise for any
  future `vX.Y.Z`) — a frozen content snapshot. Suitable for citing or for
  certifying an implementation against.

Frozen versions live as their own directory in the repo
(`versions/vX.Y.Z/`) — a literal copy of `src/` taken at release time.
This deliberately separates **content** (versioned, frozen) from **site
infrastructure** (theme, picker, build pipeline; lives at the repo root
and is unversioned). Every deploy rebuilds every published version using
today's infrastructure, so site improvements show up everywhere without
backporting.

The version-picker in the top-right of every page lists every published
version; switching keeps you on the same chapter where it exists in the
target version. Spec versions use semver and are **independent** of the
upstream MeshCore firmware's own versioning — each release records the
upstream commit hash it was validated against in
[CHANGELOG.md](https://github.com/swaits/meshcore-spec/blob/main/CHANGELOG.md).

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

# MeshCore Protocol Specification

## Section 20: Bridge Protocol

### Overview

The bridge protocol enables MeshCore packet forwarding over non-LoRa transports
such as RS232 serial links and ESP-NOW WiFi. It adds a simple framing layer
with a magic number and checksum around the raw MeshCore packet.

### Frame Format

```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│  Magic (2B)  │   Payload    │ Checksum (2B)│              │
│   0xC03E     │  (variable)  │ Fletcher-16  │              │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

### Fields

| Field | Size | Type | Description |
|-------|------|------|-------------|
| Magic | 2 bytes | uint16 | `0xC03E` — identifies the frame as a MeshCore bridge packet |
| Payload | variable | raw | Raw MeshCore packet (as produced by `Packet::writeTo()`) |
| Checksum | 2 bytes | Fletcher-16 | Fletcher-16 checksum over the payload |

### RS232 Variant

The RS232 variant adds a length field between the magic and payload:

```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│  Magic (2B)  │  Length (2B) │   Payload    │ Checksum (2B)│
│   0xC03E     │  uint16_le   │  (variable)  │ Fletcher-16  │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

| Field | Size | Type | Description |
|-------|------|------|-------------|
| Length | 2 bytes | uint16_le | Length of the payload in bytes |

### Fletcher-16 Checksum

The Fletcher-16 checksum is computed over the payload bytes:

```
function fletcher16(data):
    sum1 = 0
    sum2 = 0
    for byte in data:
        sum1 = (sum1 + byte) mod 255
        sum2 = (sum2 + sum1) mod 255
    return (sum2 << 8) | sum1
```

### ESP-NOW Variant

For ESP-NOW transport, the frame format is the same as the basic format (magic +
payload + checksum) without the length field, since ESP-NOW provides its own
length framing.

### Cross-References

- [Section 1: Wire Format](01-wire-format.md) — Packet format within payload

### Reference Implementation

- Bridge handling in MeshCore firmware (board-specific implementations)

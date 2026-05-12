# MeshCore Protocol Specification

## Section 19: KISS Modem Protocol

### Overview

The KISS (Keep It Simple, Stupid) modem protocol provides a serial interface to
MeshCore LoRa radios. It follows the KA9Q/K3MC KISS TNC specification with
MeshCore-specific SetHardware extensions for cryptographic operations, radio
control, and telemetry.

### Serial Configuration

- Baud rate: 115200
- Data bits: 8
- Parity: None
- Stop bits: 1
- Flow control: None

### Frame Format

```
┌──────┬───────────┬──────────────┬──────┐
│ FEND │ Type Byte │ Data (escaped)│ FEND │
│ 0xC0 │  1 byte   │ 0-510 bytes  │ 0xC0 │
└──────┴───────────┴──────────────┴──────┘
```

### Special Bytes

| Byte | Name | Value | Description |
|------|------|-------|-------------|
| FEND | Frame End | 0xC0 | Frame delimiter |
| FESC | Frame Escape | 0xDB | Escape character |
| TFEND | Transposed FEND | 0xDC | FESC + TFEND represents 0xC0 in data |
| TFESC | Transposed FESC | 0xDD | FESC + TFESC represents 0xDB in data |

### Byte Stuffing

To send a data byte of 0xC0 (FEND), emit: 0xDB 0xDC (FESC TFEND).
To send a data byte of 0xDB (FESC), emit: 0xDB 0xDD (FESC TFESC).

### Type Byte

```
  Bit:  7   6   5   4   3   2   1   0
      +---+---+---+---+---+---+---+---+
      |    Port (4)   |  Command (4)  |
      +---+---+---+---+---+---+---+---+
```

Port is 0 for single-port TNC (standard for MeshCore).

### Standard KISS Commands (Host to TNC)

| Command | Value | Data | Description |
|---------|-------|------|-------------|
| DataFrame | 0x00 | Raw packet | Queue packet for transmission |
| TXDELAY | 0x01 | 1 byte | Transmitter keyup delay (× 10ms) |
| Persistence | 0x02 | 1 byte | CSMA persistence (0-255) |
| SlotTime | 0x03 | 1 byte | CSMA slot interval (× 10ms) |
| TXtail | 0x04 | 1 byte | Post-TX hold time (× 10ms) |
| FullDuplex | 0x05 | 1 byte | 0=half, nonzero=full |
| SetHardware | 0x06 | Sub-cmd + data | MeshCore extensions |
| Return | 0xFF | — | Exit KISS mode (no-op) |

### TNC to Host

| Type | Value | Data | Description |
|------|-------|------|-------------|
| DataFrame | 0x00 | Raw packet | Received packet from radio |

Data frames carry raw MeshCore packets (up to 255 bytes, MAX_TRANS_UNIT).

### SetHardware Extensions (0x06)

MeshCore extends the KISS protocol via the SetHardware command. The first data
byte is a sub-command identifier.

**Request Sub-commands (Host to TNC):**

| Sub-cmd | Value | Data | Description |
|---------|-------|------|-------------|
| GetIdentity | 0x01 | — | Get node's Ed25519 public key |
| GetRandom | 0x02 | len(1) | Get random bytes (1-64) |
| VerifySignature | 0x03 | pubkey(32)+sig(64)+data | Verify Ed25519 signature |
| SignData | 0x04 | data | Ed25519 sign |
| EncryptData | 0x05 | key(32)+plaintext | AES-128 encrypt |
| DecryptData | 0x06 | key(32)+mac(2)+ciphertext | AES-128 decrypt with MAC |
| KeyExchange | 0x07 | remote_pub(32) | X25519 ECDH |
| Hash | 0x08 | data | SHA-256 hash |
| SetRadio | 0x09 | freq(4)+bw(4)+sf(1)+cr(1) | Set radio parameters |
| SetTxPower | 0x0A | power(1) | Set TX power (dBm) |
| GetRadio | 0x0B | — | Get radio parameters |
| GetTxPower | 0x0C | — | Get TX power |
| GetCurrentRssi | 0x0D | — | Get current RSSI |
| IsChannelBusy | 0x0E | — | Check if channel busy |
| GetAirtime | 0x0F | pkt_len(1) | Estimate air time |
| GetNoiseFloor | 0x10 | — | Get noise floor |
| GetVersion | 0x11 | — | Get firmware version |
| GetStats | 0x12 | — | Get RX/TX statistics |
| GetBattery | 0x13 | — | Get battery voltage |
| GetMCUTemp | 0x14 | — | Get MCU temperature |
| GetSensors | 0x15 | perms(1) | Get sensor data |
| GetDeviceName | 0x16 | — | Get device name |
| Ping | 0x17 | — | Ping |
| Reboot | 0x18 | — | Reboot device |
| SetSignalReport | 0x19 | enable(1) | Enable/disable RxMeta |
| GetSignalReport | 0x1A | — | Get signal report status |

**Response Sub-commands (TNC to Host):**

Response codes: `response = command | 0x80`

| Sub-cmd | Value | Data |
|---------|-------|------|
| Identity | 0x81 | pubkey(32) |
| Random | 0x82 | random_bytes(1-64) |
| Verify | 0x83 | result(1): 0=invalid, 1=valid |
| Signature | 0x84 | signature(64) |
| Encrypted | 0x85 | mac(2)+ciphertext |
| Decrypted | 0x86 | plaintext |
| SharedSecret | 0x87 | secret(32) |
| HashResult | 0x88 | hash(32) |
| Radio | 0x8B | freq(4)+bw(4)+sf(1)+cr(1) |
| TxPower | 0x8C | power(1) |
| CurrentRssi | 0x8D | rssi(1, signed) |
| ChannelBusy | 0x8E | busy(1): 0=clear, 1=busy |
| Airtime | 0x8F | millis(4) |
| NoiseFloor | 0x90 | dBm(2, signed) |
| Version | 0x91 | version(1)+reserved(1) |
| Stats | 0x92 | rx(4)+tx(4)+errors(4) |
| Battery | 0x93 | millivolts(2) |
| MCUTemp | 0x94 | temp(2, signed, tenths °C) |
| Sensors | 0x95 | CayenneLPP data |
| DeviceName | 0x96 | name(UTF-8) |
| Pong | 0x97 | — |
| SignalReport | 0x9A | status(1) |
| OK | 0xF0 | — |
| Error | 0xF1 | error_code(1) |
| TxDone | 0xF8 | result(1): 0=fail, 1=success |
| RxMeta | 0xF9 | snr(1)+rssi(1) |

### Error Codes

| Code | Value | Description |
|------|-------|-------------|
| InvalidLength | 0x01 | Request data too short |
| InvalidParam | 0x02 | Invalid parameter value |
| NoCallback | 0x03 | Feature not available |
| MacFailed | 0x04 | MAC verification failed |
| UnknownCmd | 0x05 | Unknown sub-command |
| EncryptFailed | 0x06 | Encryption failed |

### Unsolicited Events

**TxDone (0xF8)**: Sent after packet transmission. 0x01 = success, 0x00 = fail.

**RxMeta (0xF9)**: Sent after each received data frame. Contains:
- SNR: 1 byte, signed, × 4 for 0.25 dB precision
- RSSI: 1 byte, signed, dBm

### Data Format Notes

- Maximum payload per frame: 255 bytes (MAX_TRANS_UNIT)
- Frames larger than 255 unescaped bytes are silently dropped
- All multi-byte integers are little-endian
- Radio frequency is in Hz (e.g., 869618000)
- Battery voltage in millivolts
- MCU temperature in tenths of °C (e.g., 253 = 25.3°C)

### Cross-References

- [Section 1: Wire Format](01-wire-format.md) — Packet format within data frames
- [Section 14: Cryptography](14-crypto.md) — Crypto operations via SetHardware
- Test vectors: [`corpus/kiss/`](https://github.com/swaits/meshcore-spec/tree/main/versions/v0.1.0/corpus/kiss/)

### Reference Implementation

- `docs/kiss_modem_protocol.md` in the MeshCore repository

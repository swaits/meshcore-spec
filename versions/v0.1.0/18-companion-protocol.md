# MeshCore Protocol Specification

## Section 18: Companion Protocol

### Overview

The companion protocol enables BLE (Bluetooth Low Energy) and serial
communication between a MeshCore radio and a companion app (phone, tablet, or
computer). It uses a binary framing format over the Nordic UART Service (NUS)
BLE profile.

### BLE Service

| UUID | Description |
|------|-------------|
| `6E400001-B5A3-F393-E0A9-E50E24DCCA9E` | Nordic UART Service |
| `6E400002-...` | RX Characteristic (app writes to radio) |
| `6E400003-...` | TX Characteristic (radio notifies app) |

### Frame Format

Each companion protocol frame consists of a 1-byte type identifier followed by
variable-length data:

```
[type(1)][data(0-171)]
```

Maximum frame size is 172 bytes.

### Message Types (Radio to App)

| Type | Value | Description |
|------|-------|-------------|
| PACKET_CHANNEL_MSG_RECV | 0x01 | Channel message received |
| PACKET_CONTACT_MSG_RECV | 0x02 | Contact message received |
| PACKET_ADV_RECV | 0x03 | Advertisement received |
| PACKET_CONTACT_MSG_RECV_V3 | 0x04 | Contact message V3 (includes SNR) |
| PACKET_CHANNEL_MSG_RECV_V3 | 0x05 | Channel message V3 (includes SNR) |

### Command Types (App to Radio)

| Command | Value | Description |
|---------|-------|-------------|
| CMD_APP_START | 0x01 | Initialize connection |
| CMD_DEVICE_QUERY | 0x02 | Query device info |
| CMD_SET_CHANNEL | 0x03 | Set active channel |
| CMD_SEND_CHANNEL_MESSAGE | 0x04 | Send message to channel |
| CMD_SEND_CONTACT_MESSAGE | 0x05 | Send message to contact |
| CMD_GET_CONTACTS | 0x06 | Get contact list |
| CMD_GET_CHANNELS | 0x07 | Get channel list |
| CMD_SET_TIME | 0x08 | Set device time |
| CMD_ADD_CONTACT | 0x09 | Add a contact |
| CMD_ADD_CHANNEL | 0x0A | Add a channel |
| CMD_SEND_LOGIN | 0x0B | Login to room/repeater |
| CMD_GET_SETTINGS | 0x0C | Get device settings |
| CMD_SET_SETTINGS | 0x0D | Set device settings |
| CMD_REMOVE_CONTACT | 0x0E | Remove a contact |
| CMD_REMOVE_CHANNEL | 0x0F | Remove a channel |
| CMD_SHARE_CONTACT | 0x10 | Share contact info |
| CMD_SET_ADV_NAME | 0x11 | Set advertisement name |
| CMD_REBOOT | 0x12 | Reboot device |
| CMD_SEND_RAW | 0x13 | Send raw packet |

### Connection Sequence

1. Scan for BLE devices advertising the Nordic UART Service.
2. Connect and discover services.
3. Enable notifications on the TX characteristic.
4. Send `CMD_APP_START` to initialize.
5. Send `CMD_DEVICE_QUERY` to get device info.
6. Send `CMD_SET_TIME` to synchronize clock.
7. Send `CMD_GET_CONTACTS` and `CMD_GET_CHANNELS` to fetch state.

### Byte Order

All multi-byte integers in the companion protocol are **little-endian**, except
for CayenneLPP sensor data which uses **big-endian**.

### Message Length Limit

Text messages are limited to 133 characters.

### MTU Considerations

The default BLE MTU is 23 bytes (20 bytes of payload). For complex operations,
implementations SHOULD request a larger MTU (up to 512 bytes).

### Cross-References

- [Section 1: Wire Format](01-wire-format.md) — Underlying packet format
- Test vectors: [`corpus/companion/`](https://github.com/swaits/meshcore-spec/tree/v0.1.0/corpus/companion/)

### Reference Implementation

- `docs/companion_protocol.md` in the MeshCore repository

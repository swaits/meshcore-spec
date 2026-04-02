# pyMC_core Issues for GitHub

---

## Issue 1: `constants.py` — `CIPHER_MAC_SIZE` is 32, should be 2

### Summary

`CIPHER_MAC_SIZE` in `src/pymc_core/protocol/constants.py` is set to 32, but the
C++ firmware defines it as 2. This constant controls HMAC-SHA256 truncation
length for the encrypt-then-MAC scheme. The correct value of 2 is actually
used in `crypto.py`, creating an internal inconsistency.

### Evidence

**pyMC_core** (`src/pymc_core/protocol/constants.py`, line 52):
```python
CIPHER_MAC_SIZE = 32  # SHA‑256 HMAC
```

**pyMC_core** (`src/pymc_core/protocol/crypto.py`, line 12):
```python
CIPHER_MAC_SIZE = 2  # matches firmware
```

**C++ firmware** (`src/MeshCore.h`, line 16):
```cpp
#define CIPHER_MAC_SIZE      2
```

**C++ usage** (`src/Utils.cpp`, line 69):
```cpp
sha.finalizeHMAC(shared_secret, PUB_KEY_SIZE, dest, CIPHER_MAC_SIZE);
```
This truncates the HMAC-SHA256 output to 2 bytes.

### Impact

Any code importing `CIPHER_MAC_SIZE` from `constants.py` (rather than
`crypto.py`) will use 32 instead of 2. This would cause:
- Incorrect MAC length in packet construction/validation
- Interoperability failure with C++ firmware nodes
- `crypto.py` shadows this with its own correct definition, so the crypto
  module itself works, but any other module importing from `constants.py`
  will get the wrong value.

### Fix

Change `constants.py` line 52 to:
```python
CIPHER_MAC_SIZE = 2  # HMAC-SHA256 truncated to 2 bytes
```

---

## Issue 2: `constants.py` — `MAX_HASH_SIZE` is 32, should be 8

### Summary

`MAX_HASH_SIZE` in `constants.py` is set to 32, but the C++ firmware defines it
as 8. This constant controls the truncation length of SHA-256 packet hashes used
for deduplication.

### Evidence

**pyMC_core** (`src/pymc_core/protocol/constants.py`, line 58):
```python
MAX_HASH_SIZE = 32  # SHA-256 truncated
```

**C++ firmware** (`src/MeshCore.h`, line 6):
```cpp
#define MAX_HASH_SIZE        8
```

**C++ usage** (`src/Packet.cpp`, line 49):
```cpp
sha.finalize(hash, MAX_HASH_SIZE);  // Truncates SHA-256 to 8 bytes
```

**pyMC_core usage** (`src/pymc_core/protocol/packet_utils.py`, line 219):
```python
return sha.digest()[:MAX_HASH_SIZE]  # Will take 32 bytes instead of 8
```

### Impact

- `calculate_packet_hash()` returns 32 bytes instead of 8
- `calculate_crc()` (line 248) extracts the first 4 bytes of the hash, so CRC
  computation is accidentally correct (first 4 bytes of a 32-byte hash equal
  first 4 bytes of an 8-byte hash since both are prefixes of the same SHA-256)
- However, any code comparing full packet hashes for deduplication will fail to
  match against C++ firmware hashes (32 bytes vs 8 bytes)

### Fix

Change `constants.py` line 58 to:
```python
MAX_HASH_SIZE = 8  # SHA-256 truncated to 8 bytes for deduplication
```

---

## Issue 3: `constants.py` — `MAX_PACKET_PAYLOAD` is 256, should be 184

### Summary

`MAX_PACKET_PAYLOAD` is defined as 256 in `constants.py` (appears twice, lines
54 and 57), but the C++ firmware defines it as 184.

### Evidence

**pyMC_core** (`src/pymc_core/protocol/constants.py`, lines 54 and 57):
```python
MAX_PACKET_PAYLOAD = 256  # firmware's default
# ...
MAX_PACKET_PAYLOAD = 256
```

**C++ firmware** (`src/MeshCore.h`, line 19):
```cpp
#define MAX_PACKET_PAYLOAD  184
```

**C++ firmware** (`src/MeshCore.h`, line 20):
```cpp
#define MAX_TRANS_UNIT      255
```

Note: `MAX_TRANS_UNIT` (255) is the max *total packet* size on the wire.
`MAX_PACKET_PAYLOAD` (184) is the max *payload portion* within a packet. The
difference accounts for header (1), path_len (1), and up to 64 bytes of path
data plus optional 4-byte transport codes: `255 - 1 - 1 - 64 - 4 = 185`,
rounded down to 184.

### Impact

- `validate_payload_size()` in `packet_utils.py` (line 100) accepts payloads up
  to 256 bytes, which would overflow the C++ firmware's 184-byte payload buffer
- Packets constructed with payloads between 185-256 bytes will be silently
  accepted by pyMC_core but will be rejected or cause buffer overflows on
  firmware nodes

### Fix

Remove the duplicate definition and set correctly:
```python
MAX_PACKET_PAYLOAD = 184  # Maximum payload size in bytes
```

---

## Issue 4: `constants.py` — `MAX_ADVERT_DATA_SIZE` is 96, should be 32

### Summary

`MAX_ADVERT_DATA_SIZE` is set to 96 in `constants.py`, but the C++ firmware
defines it as 32.

### Evidence

**pyMC_core** (`src/pymc_core/protocol/constants.py`, line 48):
```python
MAX_ADVERT_DATA_SIZE = 96
```

**C++ firmware** (`src/MeshCore.h`, line 11):
```cpp
#define MAX_ADVERT_DATA_SIZE  32
```

**C++ usage** (`src/Mesh.cpp`, line 391):
```cpp
if (app_data_len > MAX_ADVERT_DATA_SIZE) return NULL;  // Reject adverts > 32 bytes app_data
```

**C++ usage** (`src/Mesh.cpp`, lines 254-255, receive side):
```cpp
if (app_data_len > MAX_ADVERT_DATA_SIZE) { app_data_len = MAX_ADVERT_DATA_SIZE; }
```
The receiver truncates app_data to 32 bytes even if more was somehow received.

### Impact

- pyMC_core could construct advertisement packets with up to 96 bytes of
  app_data
- C++ firmware will either reject these (on send) or silently truncate to 32
  bytes (on receive), losing data
- Signature verification will fail because the receiver computes the signature
  over truncated app_data while the sender signed over the full app_data

### Fix

Change `constants.py` line 48 to:
```python
MAX_ADVERT_DATA_SIZE = 32
```

---

## Issue 5: `packet.py` — `path_len` treated as raw byte count, ignoring hash_size/hash_count encoding

### Summary

The C++ firmware encodes `path_len` as a bitfield: the upper 2 bits encode the
hash size and the lower 6 bits encode the hash count. The actual number of path
bytes on the wire is `hash_count * hash_size`. pyMC_core treats `path_len` as a
raw byte count, which is only correct when hash_size == 1 (the current V1
default). This will break when multi-byte hashes are used.

### Evidence

**C++ firmware** (`src/Packet.h`, lines 79-83):
```cpp
uint8_t getPathHashSize() const { return (path_len >> 6) + 1; }
uint8_t getPathHashCount() const { return path_len & 63; }
uint8_t getPathByteLen() const { return getPathHashCount() * getPathHashSize(); }
void setPathHashCount(uint8_t n) { path_len &= ~63; path_len |= n; }
void setPathHashSizeAndCount(uint8_t sz, uint8_t n) { path_len = ((sz - 1) << 6) | (n & 63); }
```

**C++ wire read** (`src/Packet.cpp`, lines 74-78 in `readFrom()`):
```cpp
path_len = src[i++];
if (!isValidPathLen(path_len)) return false;
uint8_t bl = getPathByteLen();        // Computes hash_count * hash_size
memcpy(path, &src[i], bl); i += bl;   // Reads computed byte length, NOT raw path_len
```

**C++ validation** (`src/Packet.cpp`, lines 13-18):
```cpp
bool Packet::isValidPathLen(uint8_t path_len) {
  uint8_t hash_count = path_len & 63;
  uint8_t hash_size = (path_len >> 6) + 1;
  if (hash_size == 4) return false;  // Reserved for future
  return hash_count*hash_size <= MAX_PATH_SIZE;
}
```

**pyMC_core** (`src/pymc_core/protocol/packet.py`, lines 339-346 in `read_from()`):
```python
self.path_len = data[idx]
idx += 1
if self.path_len > MAX_PATH_SIZE:          # Wrong check: compares encoded byte, not computed length
    raise ValueError("path_len too large")
self._check_bounds(idx, self.path_len, data_len, "truncated path")  # Uses raw path_len as byte count
self.path = bytearray(data[idx : idx + self.path_len])              # Reads raw path_len bytes
idx += self.path_len
```

**pyMC_core** (`src/pymc_core/protocol/packet.py`, lines 428-429 in `get_raw_length()`):
```python
base_length = 2 + self.path_len + self.payload_len  # Uses raw path_len, not computed byte length
```

### Example of the bug

Consider a packet with 2-byte hashes and 3 hops. The wire `path_len` byte
would be `0x43` (hash_size code `01` in bits 7-6, hash_count `3` in bits 5-0):
- C++ decodes: hash_size = (0x43 >> 6) + 1 = 2, hash_count = 0x43 & 63 = 3,
  path bytes = 2 * 3 = 6 bytes
- pyMC_core reads: path_len = 0x43 = 67, tries to read 67 bytes of path data

This will either fail with a bounds error or read garbage data.

### Impact

- **Currently**: Works by accident because V1 uses 1-byte hashes, so the
  path_len byte equals the path byte count (upper 2 bits are 0)
- **With multi-byte hashes**: Completely broken — wrong number of bytes read
  from wire, wrong `get_raw_length()`, wrong path data
- **Validation is wrong**: `path_len > MAX_PATH_SIZE` compares the encoded byte
  (which can be at most 0xBF = 191 for valid packets) against 64. For 1-byte
  hashes this works, but for 2-byte hashes, a valid path_len of 0x41 (1 hop
  with 2-byte hash) would be rejected as > 64.

### Fix

Add methods to decode the path_len bitfield:
```python
def get_path_hash_size(self) -> int:
    return (self.path_len >> 6) + 1

def get_path_hash_count(self) -> int:
    return self.path_len & 63

def get_path_byte_len(self) -> int:
    return self.get_path_hash_count() * self.get_path_hash_size()
```

Then update `read_from()` to use `get_path_byte_len()` instead of `self.path_len`
for reading path data, and update `get_raw_length()` similarly.

Also add validation matching C++:
```python
@staticmethod
def is_valid_path_len(path_len: int) -> bool:
    hash_count = path_len & 63
    hash_size = (path_len >> 6) + 1
    if hash_size == 4:  # Reserved
        return False
    return hash_count * hash_size <= MAX_PATH_SIZE
```

---

## Issue 6: `packet_utils.py` — `calculate_packet_hash()` hashes TRACE `path_len` as 1 byte, should be 2

### Summary

For TRACE packets, the C++ firmware hashes `path_len` as a `uint16_t` (2 bytes)
via `sizeof(path_len)`. pyMC_core hashes it as 1 byte. This produces different
hashes, breaking deduplication interop for TRACE packets.

### Evidence

**C++ firmware** (`src/Packet.h`, line 47):
```cpp
uint16_t payload_len, path_len;  // path_len is uint16_t in the struct
```

**C++ firmware** (`src/Packet.cpp`, lines 41-49):
```cpp
void Packet::calculatePacketHash(uint8_t* hash) const {
  SHA256 sha;
  uint8_t t = getPayloadType();
  sha.update(&t, 1);
  if (t == PAYLOAD_TYPE_TRACE) {
    sha.update(&path_len, sizeof(path_len));   // sizeof(uint16_t) = 2 bytes
  }
  sha.update(payload, payload_len);
  sha.finalize(hash, MAX_HASH_SIZE);
}
```

`sizeof(path_len)` is `sizeof(uint16_t)` = **2 bytes**. On little-endian
platforms (ESP32, STM32, nRF52 — all LE), this hashes the path_len value as a
2-byte little-endian integer.

**pyMC_core** (`src/pymc_core/protocol/packet_utils.py`, lines 214-219):
```python
sha = hashlib.sha256()
sha.update(bytes([payload_type]))
if payload_type == PAYLOAD_TYPE_TRACE:
    sha.update(bytes([path_len]))    # Only 1 byte!
sha.update(payload)
return sha.digest()[:MAX_HASH_SIZE]
```

### Example

For a TRACE packet with `path_len = 3`:
- C++ hashes: `SHA256(0x09 | 0x03 0x00 | payload)` (path_len as uint16_t LE = `03 00`)
- pyMC_core hashes: `SHA256(0x09 | 0x03 | payload)` (path_len as single byte = `03`)

These produce completely different hashes.

### Impact

- TRACE packet deduplication will not interoperate between pyMC_core and C++
  firmware
- A pyMC_core node forwarding TRACE packets will compute different hashes than
  firmware nodes, potentially causing duplicate forwarding or dropped packets

### Fix

Change `packet_utils.py` line 217 from:
```python
sha.update(bytes([path_len]))
```
to:
```python
sha.update(path_len.to_bytes(2, 'little'))  # uint16_t, matching C++ sizeof(path_len)
```

---

## Issue 7: `packet_utils.py` — `calculate_snr_db()` returns raw value, should divide by 4

### Summary

The C++ firmware stores SNR as `int8_t` scaled by 4x (0.25 dB precision) and
divides by 4.0 when returning the dB value. pyMC_core returns the raw integer
without dividing.

### Evidence

**C++ firmware** (`src/Packet.h`, line 92):
```cpp
float getSNR() const { return ((float)_snr) / 4.0f; }
```

**C++ firmware** — SNR is stored scaled (`src/Mesh.cpp`, line 58, during TRACE forwarding):
```cpp
pkt->path[pkt->path_len++] = (int8_t) (pkt->getSNR()*4);  // Store as SNR × 4
```

**C++ firmware** — SNR is received scaled (`src/Dispatcher.cpp`, line 205):
```cpp
pkt->_snr = _radio->getLastSNR() * 4.0f;  // Scale by 4 on receive
```

**pyMC_core** (`src/pymc_core/protocol/packet_utils.py`, lines 149-151):
```python
@staticmethod
def calculate_snr_db(raw_snr: int) -> float:
    """Convert raw SNR value to decibels."""
    return raw_snr if raw_snr is not None else 0.0  # Returns raw value, no /4.0
```

### Impact

- `packet.get_snr()` and `packet.snr` return values 4x too large
- An SNR of 8.0 dB from firmware (stored as raw 32) will be reported as 32.0 dB
  by pyMC_core
- Any signal quality decisions based on SNR will be wrong

### Fix

Change `packet_utils.py` lines 149-151 to:
```python
@staticmethod
def calculate_snr_db(raw_snr: int) -> float:
    """Convert raw SNR value to decibels (raw value is SNR × 4)."""
    return (raw_snr / 4.0) if raw_snr is not None else 0.0
```

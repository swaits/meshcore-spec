# MeshCore Protocol Specification

## Section 14: Cryptography

### Overview

MeshCore uses a combination of symmetric and asymmetric cryptography. Data
confidentiality is provided by AES-128 in ECB mode with zero padding. Data
integrity is provided by HMAC-SHA256 truncated to 2 bytes. These are combined
in an encrypt-then-MAC scheme.

### Algorithms

| Operation | Algorithm | Key Size | Output |
|-----------|-----------|----------|--------|
| Symmetric Encryption | AES-128-ECB | 16 bytes | Multiple of 16 bytes |
| Message Authentication | HMAC-SHA256 | 32 bytes | 2 bytes (truncated) |
| Digital Signature | Ed25519 | 32/64 bytes | 64 bytes |
| Key Exchange | X25519 (ECDH) | 32 bytes | 32 bytes |
| Hashing | SHA-256 | — | Up to 32 bytes |

### AES-128-ECB Encryption

MeshCore uses AES-128 in Electronic Codebook (ECB) mode with zero-byte padding.

**Key**: The first 16 bytes (CIPHER_KEY_SIZE) of the shared secret.

**Encryption**:

1. Set the AES-128 key to `shared_secret[0..15]`.
2. Process the plaintext in 16-byte blocks:
   a. For each complete 16-byte block, encrypt in place.
   b. For the final partial block (< 16 bytes):
      - Copy the remaining bytes to a 16-byte buffer.
      - Fill remaining bytes with zeros.
      - Encrypt the padded block.
3. If the plaintext is empty, encrypt a 16-byte all-zero block.
4. The output is always a multiple of 16 bytes.

**Decryption**:

1. Set the AES-128 key to `shared_secret[0..15]`.
2. Process the ciphertext in 16-byte blocks, decrypting each.
3. The output length equals the ciphertext length.
4. The final block MAY contain trailing zero bytes from padding.
   The application must know the original plaintext length or use
   a length-prefixed format to determine where meaningful data ends.

### HMAC-SHA256 (Truncated to 2 Bytes)

MeshCore computes HMAC-SHA256 over the ciphertext and truncates the result to
CIPHER_MAC_SIZE (2) bytes.

**Key**: The full 32 bytes (PUB_KEY_SIZE) of the shared secret.

Note: The HMAC key uses the full 32-byte shared secret, while the AES key uses
only the first 16 bytes. This is an important distinction.

**Computation**:

```
mac = HMAC-SHA256(key=shared_secret[0..31], message=ciphertext)[0..1]
```

The first 2 bytes of the HMAC-SHA256 output are used as the MAC.

### Encrypt-then-MAC

The encrypt-then-MAC scheme combines AES-128-ECB encryption with HMAC-SHA256
authentication:

**Encoding** (`encryptThenMAC`):

1. Encrypt the plaintext using AES-128-ECB (see above).
   Store ciphertext at `dest[2..]` (offset by MAC size).
2. Compute HMAC-SHA256 over the ciphertext using the full 32-byte shared
   secret. Truncate to 2 bytes.
3. Store the 2-byte MAC at `dest[0..1]`.
4. Return total length: 2 + ciphertext_length.

Output format:
```
[MAC (2 bytes)][Ciphertext (N × 16 bytes)]
```

**Decoding** (`MACThenDecrypt`):

1. If input length ≤ 2 (CIPHER_MAC_SIZE), return failure (invalid).
2. Recompute HMAC-SHA256 over `src[2..]` (the ciphertext portion) using the
   full 32-byte shared secret. Truncate to 2 bytes.
3. Compare the computed MAC with `src[0..1]`.
4. If MACs do not match, return failure (0 = invalid HMAC).
5. If MACs match, decrypt `src[2..]` using AES-128-ECB.
6. Return the decrypted plaintext length.

### Security Notes

- **ECB mode**: AES-ECB encrypts each 16-byte block independently. Identical
  plaintext blocks produce identical ciphertext blocks. This is a known
  weakness of ECB mode, but MeshCore's short payloads and mesh-network context
  make this acceptable for its use case.
- **2-byte MAC**: The truncated HMAC provides only 16 bits of authentication.
  This means there is approximately a 1-in-65536 chance of a forged MAC being
  accepted. This trade-off prioritizes bandwidth over authentication strength.
- **Key derivation**: The shared secret is used directly as both AES key
  (first 16 bytes) and HMAC key (full 32 bytes). No key derivation function
  (KDF) is applied.

### Cross-References

- [Section 6: Encrypted Payloads](06-payload-encrypted.md) — Usage in packet payloads
- [Section 15: Identity](15-identity.md) — Shared secret computation via ECDH
- Test vectors: [`corpus/crypto/`](https://github.com/swaits/meshcore-spec/tree/main/versions/v0.1.0/corpus/crypto/)

### Reference Implementation

- `Utils::encrypt()` in `src/Utils.cpp` — AES-128-ECB encryption
- `Utils::decrypt()` in `src/Utils.cpp` — AES-128-ECB decryption
- `Utils::encryptThenMAC()` in `src/Utils.cpp` — Encrypt-then-MAC
- `Utils::MACThenDecrypt()` in `src/Utils.cpp` — MAC-then-Decrypt

# MeshCore Protocol Specification

## Section 15: Identity

### Overview

Every MeshCore node has an Ed25519 key pair. The 32-byte public key serves as
the node's identity. Hashes used in routing are truncated prefixes of the public
key. Shared secrets for encryption are computed via ECDH key exchange using
X25519 (Ed25519 keys transposed to Curve25519).

### Key Types

| Type | Size | Description |
|------|------|-------------|
| Public Key | 32 bytes (PUB_KEY_SIZE) | Ed25519 public key |
| Private Key | 64 bytes (PRV_KEY_SIZE) | Ed25519 private key (seed + public) |
| Signature | 64 bytes (SIGNATURE_SIZE) | Ed25519 signature |
| Shared Secret | 32 bytes (PUB_KEY_SIZE) | ECDH shared secret |

### Hash Derivation

A node's routing hash is simply a prefix of its public key:

```
hash = pub_key[0..hash_size-1]
```

Where `hash_size` is 1, 2, or 3 bytes depending on the protocol version and
path encoding (see [Section 3](03-path.md)).

For V1, `PATH_HASH_SIZE` is 1, meaning a node's hash is the first byte of its
public key. This gives only 256 unique hash values, so hash collisions are
common and expected. The protocol handles this by attempting decryption with all
peers matching a given hash.

### Hash Matching

To check if a hash matches a node's identity:

```
match = memcmp(hash, pub_key, hash_size) == 0
```

### Ed25519 Signing

Used for advertisement signatures (see [Section 5](05-payload-advert.md)):

1. Construct the message to sign (e.g., pub_key || timestamp || app_data).
2. Sign using the Ed25519 private key.
3. The 64-byte signature is included in the advertisement payload.

Verification:

1. Extract the public key and signature from the payload.
2. Reconstruct the message.
3. Verify the signature using Ed25519 verification.
4. Receivers MUST discard the packet if verification fails.

### ECDH Key Exchange (X25519)

To compute a shared secret between two nodes:

1. Convert the Ed25519 keys to X25519 (Curve25519) format.
2. Perform X25519 Diffie-Hellman: `shared_secret = X25519(my_private, their_public)`.
3. The resulting 32-byte shared secret is used for:
   - AES-128 key: `shared_secret[0..15]`
   - HMAC-SHA256 key: `shared_secret[0..31]`

### Identity Serialization

Identities can be serialized for storage:

- **Public Identity**: 32 bytes (public key only)
- **Local Identity**: 64 bytes (private key) + 32 bytes (public key) = 96 bytes

Hex representation uses uppercase characters with 2 hex digits per byte.

### Cross-References

- [Section 3: Path](03-path.md) — Hash size in path encoding
- [Section 5: Advertisement](05-payload-advert.md) — Signature usage
- [Section 14: Cryptography](14-crypto.md) — Shared secret usage
- Test vectors: [`corpus/crypto/ed25519/`](https://github.com/swaits/meshcore-spec/tree/main/corpus/crypto/ed25519/), [`corpus/crypto/ecdh/`](https://github.com/swaits/meshcore-spec/tree/main/corpus/crypto/ecdh/)

### Reference Implementation

- `Identity` class in `src/Identity.h` — Public key and verification
- `LocalIdentity` class in `src/Identity.h` — Key pair, signing, ECDH
- `Identity::copyHashTo()` — Hash derivation (prefix copy)
- `Identity::isHashMatch()` — Hash comparison
- `LocalIdentity::calcSharedSecret()` — ECDH key exchange

# MeshCore Spec — Project Guide

## What This Project Is

A specification and conformance test suite for the MeshCore mesh networking
protocol. It contains:

1. RFC-style spec documents in `src/` (Markdown, using RFC 2119 language; this
   is also the mdbook source root)
2. JSON test vector corpus in `corpus/`
3. Validation tooling in `tools/`

## Conventions

- All binary data in JSON is uppercase hex (e.g., `"0D00EFBEADDE"`).
  Whitespace in hex strings is allowed and stripped on parse.
- All multi-byte integers are little-endian unless explicitly noted otherwise.
- Test vector IDs use the format `{category}-{NNN}` (e.g., `ack-001`, `kiss-hw-003`).
- Spec sections are numbered `00-` through `20-` and use RFC 2119 keywords.
- The C++ reference implementation at github.com/meshcore-dev/MeshCore is the
  source of truth for protocol behavior.

## Key Protocol Constants

- MAX_PACKET_PAYLOAD: 184 bytes
- MAX_PATH_SIZE: 64 bytes
- CIPHER_MAC_SIZE: 2 bytes
- PATH_HASH_SIZE: 1 byte (default)
- PUB_KEY_SIZE: 32 bytes
- SIGNATURE_SIZE: 64 bytes
- MAX_TRANS_UNIT: 255 bytes

## File Organization

- `src/NN-topic.md` — Spec sections, numbered for reading order (mdbook root)
- `src/SUMMARY.md` — mdbook table of contents; new chapters MUST be added here
- `corpus/schema/` — JSON Schema for test vector validation
- `corpus/{layer}/{type}/` — Test vectors organized by protocol layer
- `tools/` — Python validation and generation scripts

## Working With Test Vectors

Each JSON file validates against `corpus/schema/test-vector.schema.json`.
Vector types: `encode_decode`, `decode_only`, `invalid`.

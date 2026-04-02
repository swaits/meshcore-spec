# MeshCore Spec

A comprehensive specification and conformance test suite for the
[MeshCore](https://github.com/meshcore-dev/MeshCore) mesh networking protocol.

MeshCore Spec aims to be the authoritative, machine-readable definition of the
MeshCore wire format — much like [RubySpec](https://github.com/ruby/spec) became
the definitive specification of the Ruby language. Any implementation that passes
the full test corpus can claim bit-perfect MeshCore compatibility.

## What's Here

- **`spec/`** — RFC-style protocol specification in Markdown, covering every
  layer from packet framing to cryptographic operations.
- **`corpus/`** — JSON test vectors organized by protocol layer.
  Each vector pairs a structured representation with its exact binary encoding,
  enabling any implementation to verify encode and decode correctness.
- **`tools/`** — Validation and generation utilities.

## Test Vector Format

Test vectors are JSON files. Binary data is represented as uppercase hex strings
(whitespace allowed for readability). Each file contains an array of vectors in
one of three modes:

- **`encode_decode`** — Structured input paired with expected binary output.
  Implementations MUST produce the given binary when encoding, and MUST recover
  the given structure when decoding.
- **`decode_only`** — Binary input with expected structured output. Used for
  alternate valid encodings that an encoder need not produce but a decoder MUST
  accept.
- **`invalid`** — Binary input that MUST be rejected by a conforming decoder.

See `corpus/schema/test-vector.schema.json` for the full schema.

## Using the Corpus

1. Parse each JSON file in `corpus/`.
2. For `encode_decode` vectors: encode the `structured` form and compare to
   `binary`; decode `binary` and compare to `structured`.
3. For `invalid` vectors: attempt to decode `binary` and verify failure.

No special tooling is required — just a JSON parser and your MeshCore
implementation.

## Project Status

This project is under active development. The specification and corpus are being
built from the [official MeshCore firmware](https://github.com/meshcore-dev/MeshCore)
source code.

## Protocol Versions

The corpus covers all known MeshCore protocol versions. Each test vector file
includes a `protocol_version` field. Version 1 (the current production version)
has the most comprehensive coverage.

## License

MIT — see [LICENSE](LICENSE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Acknowledgments

Based on the [MeshCore firmware](https://github.com/meshcore-dev/MeshCore) by
the MeshCore developers. Protocol documentation derived from the official
[MeshCore docs](https://docs.meshcore.io).

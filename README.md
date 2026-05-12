# MeshCore Spec

A comprehensive specification and conformance test suite for the
[MeshCore](https://github.com/meshcore-dev/MeshCore) mesh networking protocol.

**📖 Read the spec online:** <https://swaits.github.io/meshcore-spec/>
(rolling `latest` from `main`, plus a frozen snapshot per release —
current: [v0.1.0](https://swaits.github.io/meshcore-spec/v0.1.0/). Use
the version-picker in the top-right of any page to switch.)

MeshCore Spec aims to be the authoritative, machine-readable definition of the
MeshCore wire format — much like [RubySpec](https://github.com/ruby/spec) became
the definitive specification of the Ruby language. Any implementation that passes
the full test corpus can claim bit-perfect MeshCore compatibility.

## Provenance

This is an **independent, AI-authored project**. It is not affiliated with,
endorsed by, or maintained by the upstream MeshCore project. Read this section
before relying on the spec for anything load-bearing.

- **Authorship.** The spec, the corpus, and the tooling were written by Claude
  (Anthropic, primarily Opus 4.x) under the direction of
  [SWaits](https://swaits.com/). Substantive edits — additions, clarifications,
  audit passes — are produced through model-driven analysis of the official
  MeshCore source and reviewed before commit.
- **Source of truth.** The official MeshCore firmware at
  [meshcore-dev/MeshCore](https://github.com/meshcore-dev/MeshCore) is the
  **golden source of truth** for all protocol behavior. Whenever this spec and
  the upstream C++ disagree, **upstream wins** — this spec is downstream and
  the canonical text is the C++. Each substantive change in `CHANGELOG.md`
  records the upstream commit hash it was validated against.
- **Refined through DongLoRa.** Clarifications and edge-case detail in this
  spec have been driven in part by observations from building DongLoRa
  firmware and apps against live MeshCore deployments. Where DongLoRa
  behavior diverges from upstream, this spec follows upstream and treats the
  DongLoRa side as a follow-up bug, not a spec change.
- **Use it carefully.** Conformance against this corpus is a useful signal
  but not a substitute for cross-checking against upstream firmware for any
  behavior that affects interoperability. If you find a divergence from
  upstream, please file an issue — that is exactly the kind of report this
  project exists to catch.

## What's Here

- **`src/`** — RFC-style protocol specification in Markdown, covering every
  layer from packet framing to cryptographic operations. Also the source root
  for the [mdBook](https://rust-lang.github.io/mdBook/) build published to
  GitHub Pages.
- **`corpus/`** — JSON test vectors organized by protocol layer.
  Each vector pairs a structured representation with its exact binary encoding,
  enabling any implementation to verify encode and decode correctness.
- **`tools/`** — Validation and generation utilities.
- **`book.toml`** + **`.github/workflows/mdbook.yml`** — mdBook configuration
  and the GitHub Actions workflow that builds and deploys the spec on every
  push to `main`.

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

This project is under active development. See [Provenance](#provenance) above
for how the spec is produced and what to verify against.

## Protocol Versions

The corpus covers all known MeshCore protocol versions. Each test vector file
includes a `protocol_version` field. Version 1 (the current production version)
has the most comprehensive coverage.

## License

MIT — see [LICENSE](LICENSE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Acknowledgments

This spec would not exist without the [MeshCore firmware](https://github.com/meshcore-dev/MeshCore)
by the MeshCore developers and the official [MeshCore docs](https://docs.meshcore.io),
which together are the authoritative reference this spec derives from.

## Author

[SWaits](https://swaits.com/)

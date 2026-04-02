# Contributing to MeshCore Spec

## Adding Test Vectors

1. Choose the appropriate directory under `corpus/` based on protocol layer and
   packet type.
2. Add vectors to an existing JSON file, or create a new file if testing a
   distinct aspect.
3. Every JSON file must validate against `corpus/schema/test-vector.schema.json`.
4. Use uppercase hex for binary data. Whitespace is allowed for readability.
5. Each vector needs a unique `id` within its file and a clear `description`.
6. For `encode_decode` vectors, verify both directions: encoding the structured
   form produces the binary, and decoding the binary recovers the structure.

## Editing the Specification

1. Spec documents live in `spec/` and are numbered for reading order.
2. Use RFC 2119 language (MUST, SHOULD, MAY) for normative requirements.
3. Include ASCII wire format diagrams where applicable.
4. Cross-reference related spec sections and test vector files.
5. The C++ reference implementation is the source of truth — if the spec
   disagrees with the firmware, the spec needs updating.

## Generating Vectors from Reference Implementation

See `tools/generate/README.md` for instructions on building and running the
corpus generation harness against the C++ MeshCore library.

## Validating the Corpus

```bash
python tools/validate.py
```

This checks all JSON files against the schema and verifies internal consistency.

#!/usr/bin/env python3
"""
MeshCore Spec Corpus Validator

Validates all test vector JSON files against the schema and checks internal
consistency of test vectors (hex encoding, field relationships, etc.).

Usage:
    python tools/validate.py [--verbose] [path...]

If no paths given, validates all JSON files under corpus/.
"""

import argparse
import json
import re
import struct
import sys
from pathlib import Path

# Schema validation is optional (requires jsonschema)
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


REPO_ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = REPO_ROOT / "corpus"
SCHEMA_PATH = CORPUS_DIR / "schema" / "test-vector.schema.json"

# Maps payload type names to their numeric values
PAYLOAD_TYPE_MAP = {
    "request": 0x00, "response": 0x01, "txt_msg": 0x02, "ack": 0x03,
    "advert": 0x04, "grp_txt": 0x05, "grp_data": 0x06, "anon_req": 0x07,
    "path": 0x08, "trace": 0x09, "multipart": 0x0A, "control": 0x0B,
    "raw_custom": 0x0F,
}

ROUTE_TYPE_MAP = {
    "transport_flood": 0x00, "flood": 0x01, "direct": 0x02,
    "transport_direct": 0x03,
}

# Wire format sizes (bytes)
HEADER_SIZE = 1
TRANSPORT_CODES_SIZE = 4
PATH_LEN_SIZE = 1


def strip_hex(s):
    """Remove whitespace from hex string and return uppercase."""
    return re.sub(r'\s+', '', s).upper()


def hex_to_bytes(s):
    """Convert hex string (with optional whitespace) to bytes."""
    return bytes.fromhex(strip_hex(s))


def compute_header(version, payload_type, route_type):
    """Compute the header byte from structured fields."""
    pt = PAYLOAD_TYPE_MAP.get(payload_type)
    rt = ROUTE_TYPE_MAP.get(route_type)
    if pt is None or rt is None:
        return None
    return (version << 6) | (pt << 2) | rt


def compute_path_len_byte(hash_size, hash_count):
    """Compute the path_len byte from hash_size and hash_count."""
    return ((hash_size - 1) << 6) | (hash_count & 0x3F)


class ValidationError:
    """A single validation error with file location and optional vector context."""

    def __init__(self, file_path, vector_id, message):
        self.file_path = file_path
        self.vector_id = vector_id
        self.message = message

    def __str__(self):
        loc = str(self.file_path)
        if self.vector_id:
            loc += f" [{self.vector_id}]"
        return f"  ERROR: {loc}: {self.message}"


def validate_json_syntax(file_path):
    """Validate that the file is valid JSON."""
    try:
        with open(file_path, encoding="utf-8") as f:
            return json.load(f), []
    except FileNotFoundError:
        return None, [ValidationError(file_path, None, f"File not found: {file_path}")]
    except json.JSONDecodeError as e:
        return None, [ValidationError(file_path, None, f"Invalid JSON: {e}")]


def validate_schema(data, file_path, schema):
    """Validate against JSON Schema."""
    errors = []
    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        errors.append(ValidationError(file_path, None, f"Schema: {e.message}"))
    return errors


def validate_hex_string(hex_str, field_name, file_path, vector_id):
    """Validate a hex string is well-formed."""
    errors = []
    stripped = strip_hex(hex_str)
    if len(stripped) % 2 != 0:
        errors.append(ValidationError(file_path, vector_id,
            f"Odd-length hex in {field_name}: '{stripped}'"))
    if not re.match(r'^[0-9A-F]*$', stripped):
        errors.append(ValidationError(file_path, vector_id,
            f"Invalid or lowercase hex chars in {field_name} (must be uppercase)"))
    return errors


def validate_vector_consistency(vector, file_path):
    """Validate internal consistency of a single test vector."""
    errors = []
    vid = vector.get("id", "?")
    vtype = vector.get("type")

    # Validate binary hex
    if "binary" in vector:
        errors.extend(validate_hex_string(vector["binary"], "binary", file_path, vid))

    # For encode_decode vectors, verify header byte matches structured form
    if vtype in ("encode_decode", "decode_only") and "structured" in vector and "binary" in vector:
        structured = vector["structured"]
        binary = hex_to_bytes(vector["binary"])

        if len(binary) < 1:
            errors.append(ValidationError(file_path, vid, "Binary too short for header"))
            return errors

        # Check header byte
        hdr = structured.get("header", {})
        expected_header = compute_header(
            hdr.get("version", 0),
            hdr.get("payload_type", ""),
            hdr.get("route_type", "")
        )
        if expected_header is not None and binary[0] != expected_header:
            errors.append(ValidationError(file_path, vid,
                f"Header mismatch: binary[0]=0x{binary[0]:02X}, "
                f"expected=0x{expected_header:02X}"))

        # Check transport codes presence and values
        rt = hdr.get("route_type", "")
        has_tc = rt in ("transport_flood", "transport_direct")
        offset = HEADER_SIZE
        if has_tc:
            if "transport_codes" not in structured:
                errors.append(ValidationError(file_path, vid,
                    "Route type requires transport_codes but none in structured"))
            elif len(binary) >= HEADER_SIZE + TRANSPORT_CODES_SIZE:
                # Verify transport code LE values
                tc = structured["transport_codes"]
                tc0 = struct.unpack_from('<H', binary, HEADER_SIZE)[0]
                tc1 = struct.unpack_from('<H', binary, HEADER_SIZE + 2)[0]
                if tc0 != tc[0]:
                    errors.append(ValidationError(file_path, vid,
                        f"transport_code[0] mismatch: binary={tc0}, structured={tc[0]}"))
                if tc1 != tc[1]:
                    errors.append(ValidationError(file_path, vid,
                        f"transport_code[1] mismatch: binary={tc1}, structured={tc[1]}"))
            offset += TRANSPORT_CODES_SIZE
        else:
            if "transport_codes" in structured:
                errors.append(ValidationError(file_path, vid,
                    "Route type forbids transport_codes but present in structured"))

        # Check path_len byte
        path_info = structured.get("path", {})
        if offset < len(binary):
            expected_pl = compute_path_len_byte(
                path_info.get("hash_size", 1),
                path_info.get("hash_count", 0)
            )
            if binary[offset] != expected_pl:
                errors.append(ValidationError(file_path, vid,
                    f"path_len mismatch: binary[{offset}]=0x{binary[offset]:02X}, "
                    f"expected=0x{expected_pl:02X}"))

        # Verify total binary length
        path_bytes = path_info.get("hash_count", 0) * path_info.get("hash_size", 1)
        min_expected = (HEADER_SIZE + (TRANSPORT_CODES_SIZE if has_tc else 0)
                        + PATH_LEN_SIZE + path_bytes + 1)
        if len(binary) < min_expected:
            errors.append(ValidationError(file_path, vid,
                f"Binary too short: {len(binary)} bytes, minimum expected {min_expected}"))

        # Check hash array length matches hash_count
        hashes = path_info.get("hashes", [])
        if len(hashes) != path_info.get("hash_count", 0):
            errors.append(ValidationError(file_path, vid,
                f"hashes array length ({len(hashes)}) != hash_count ({path_info.get('hash_count', 0)})"))

        # Check each hash is the right size
        hs = path_info.get("hash_size", 1)
        for i, h in enumerate(hashes):
            h_bytes = len(strip_hex(h)) // 2
            if h_bytes != hs:
                errors.append(ValidationError(file_path, vid,
                    f"hash[{i}] is {h_bytes} bytes, expected {hs}"))

    # Validate crypto_context hex fields
    if "crypto_context" in vector:
        ctx = vector["crypto_context"]
        for field in ("shared_secret", "encryption_key", "plaintext",
                      "sender_private_key", "sender_public_key",
                      "recipient_private_key", "recipient_public_key"):
            if field in ctx:
                errors.extend(validate_hex_string(
                    ctx[field], f"crypto_context.{field}", file_path, vid))

    return errors


def validate_file(file_path, schema=None, verbose=False):
    """Validate a single test vector file."""
    errors = []

    # JSON syntax
    data, parse_errors = validate_json_syntax(file_path)
    errors.extend(parse_errors)
    if data is None:
        return errors, 0

    # Schema validation
    if schema and HAS_JSONSCHEMA:
        errors.extend(validate_schema(data, file_path, schema))

    # Required fields
    if "vectors" not in data:
        errors.append(ValidationError(file_path, None, "Missing 'vectors' array"))
        return errors, 0

    # Check for duplicate IDs
    ids = [v.get("id") for v in data["vectors"] if "id" in v]
    seen = set()
    for vid in ids:
        if vid in seen:
            errors.append(ValidationError(file_path, vid, f"Duplicate vector ID: {vid}"))
        seen.add(vid)

    # Validate each vector
    for vector in data["vectors"]:
        errors.extend(validate_vector_consistency(vector, file_path))

    n = len(data["vectors"])
    if verbose and not errors:
        print(f"  OK: {file_path} ({n} vectors)")

    return errors, n


def main():
    """Entry point: parse arguments, discover test vector files, validate, and report results."""
    parser = argparse.ArgumentParser(description="Validate MeshCore Spec corpus")
    parser.add_argument("paths", nargs="*", help="Specific files/dirs to validate")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    # Load schema
    schema = None
    if HAS_JSONSCHEMA and SCHEMA_PATH.exists():
        with open(SCHEMA_PATH, encoding="utf-8") as f:
            schema = json.load(f)

    # Find files to validate
    if args.paths:
        files = []
        for p in args.paths:
            p = Path(p)
            if p.is_dir():
                files.extend(p.rglob("*.json"))
            elif p.is_file():
                files.append(p)
    else:
        files = sorted(CORPUS_DIR.rglob("*.json"))
        # Exclude schema files
        files = [f for f in files if "schema" not in str(f)]

    if not files:
        print("No files to validate.")
        return 0

    print(f"Validating {len(files)} files...")
    if not HAS_JSONSCHEMA:
        print("  (jsonschema not installed - skipping schema validation)")
        print("  Install with: pip install jsonschema")

    all_errors = []
    total_vectors = 0

    for f in sorted(files):
        errors, n = validate_file(f, schema, args.verbose)
        all_errors.extend(errors)
        total_vectors += n

    # Report
    print()
    if all_errors:
        print(f"FAILED: {len(all_errors)} error(s) in {len(files)} files "
              f"({total_vectors} vectors)")
        for e in all_errors:
            print(e)
        return 1
    else:
        print(f"PASSED: {len(files)} files, {total_vectors} vectors, 0 errors")
        return 0


if __name__ == "__main__":
    sys.exit(main())

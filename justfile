# meshcore-spec — task runner.
#
# Every recipe runs under `mise exec sh -c …`, so mise-pinned tools
# (see mise.toml) are on PATH and we never accidentally use a system
# mdbook of the wrong version. `sh` is intentional — keep recipes
# POSIX-compatible.

set shell := ["mise", "exec", "--", "sh", "-c"]

# Show the available recipes.
_default:
    @just --list

# Install / refresh tools pinned in mise.toml.
setup:
    mise install

# Build the spec into ./book/ (single-version; for local dev).
build:
    mdbook build

# Build the full multi-version site into ./_site/ (latest + every v* tag).
# This is exactly what CI runs.
build-site:
    sh scripts/build-site.sh

# Live-preview the spec at http://localhost:3000 with auto-reload.
serve:
    mdbook serve --open --port 3000

# Remove all build outputs (single-version and multi-version).
clean:
    rm -rf book _site

# Run the corpus validator.
validate:
    python3 tools/validate.py corpus/

# Cut a frozen spec version: copy ./src/ to ./versions/<VERSION>/.
# Usage: just cut-version v0.2.0
cut-version VERSION:
    #!/usr/bin/env sh
    set -eu
    case "{{VERSION}}" in
        v[0-9]*.[0-9]*.[0-9]*) ;;
        *) echo "Version must look like vX.Y.Z (got '{{VERSION}}')" >&2; exit 1 ;;
    esac
    if [ -e "versions/{{VERSION}}" ]; then
        echo "versions/{{VERSION}} already exists; not overwriting." >&2
        exit 1
    fi
    mkdir -p versions
    cp -R src "versions/{{VERSION}}"
    # Freeze the version marker in the snapshot. src/ keeps the literal
    # `latest (main)` so the rolling /latest/ build stays accurate.
    sed -i 's|`latest (main)`|`{{VERSION}}`|' "versions/{{VERSION}}/00-overview.md"
    if ! grep -q '`{{VERSION}}`' "versions/{{VERSION}}/00-overview.md"; then
        echo "warning: expected version marker not found in 00-overview.md; the" >&2
        echo "snapshot still says 'latest (main)'. Check that src/00-overview.md" >&2
        echo "contains the marker line ('**Spec version:** \`latest (main)\`')." >&2
    fi
    echo "Snapshotted src/ -> versions/{{VERSION}}"
    echo
    echo "Next steps:"
    echo "  - git add versions/{{VERSION}} && commit (e.g. \"release {{VERSION}}\")"
    echo "  - optionally tag the commit: git tag {{VERSION}}"

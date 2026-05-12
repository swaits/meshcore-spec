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

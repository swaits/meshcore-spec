#!/usr/bin/env sh
# Build the full multi-version site into ./_site/:
#   - "latest" from ./src/
#   - one subtree per ./versions/vX.Y.Z/ directory
#
# Each per-version build uses today's repo-root build infrastructure
# (book.toml, theme/, picker JS, scripts/), only swapping in the
# frozen content directory via MDBOOK_BOOK__SRC. This means every
# deploy gives every published version the current theme — site
# improvements never need backporting to old snapshots.
#
# Emits _site/versions.json (newest first; consumed by
# theme/version-picker.js) and _site/index.html (redirect to /latest/).
#
# Cut a new frozen version with `just cut-version vX.Y.Z`, which
# snapshots ./src/ into ./versions/vX.Y.Z/.

set -eu

SITE_BASE="${SITE_BASE:-/meshcore-spec}"
WORKSPACE="$(pwd)"
SITE_DIR="$WORKSPACE/_site"

group() { printf '::group::%s\n' "$1"; }
endgroup() { printf '::endgroup::\n'; }
warn() { printf '::warning::%s\n' "$1"; }

rm -rf "$SITE_DIR"
mkdir -p "$SITE_DIR"

# ---- latest (from src/) ----
group "build latest"
MDBOOK_OUTPUT__HTML__SITE_URL="${SITE_BASE}/latest/" \
    mdbook build "$WORKSPACE" -d "$SITE_DIR/latest"
endgroup

# ---- frozen versions (./versions/v*) ----
# Discover and sort by semver (newest first). The list is captured
# into a variable so we can iterate it twice — once to build, once to
# emit versions.json — without re-scanning.
list_versions() {
    for d in versions/v*; do
        [ -d "$d" ] || continue
        basename "$d"
    done | sort -V -r
}
VERSION_DIRS="$(list_versions)"

for version in $VERSION_DIRS; do
    vdir="versions/$version"
    [ -d "$vdir" ] || continue
    group "build $version"
    if ! MDBOOK_BOOK__SRC="$vdir" \
         MDBOOK_OUTPUT__HTML__SITE_URL="${SITE_BASE}/${version}/" \
         mdbook build "$WORKSPACE" -d "$SITE_DIR/${version}"; then
        warn "mdbook build failed for ${version}; skipping"
        rm -rf "${SITE_DIR:?}/${version:?}"
    fi
    endgroup
done

# ---- versions.json (consumed by theme/version-picker.js) ----
# "latest" always first; then each successfully-built frozen version.
{
    printf '['
    printf '"latest"'
    for version in $VERSION_DIRS; do
        [ -d "$SITE_DIR/$version" ] || continue
        printf ',"%s"' "$version"
    done
    printf ']\n'
} > "$SITE_DIR/versions.json"
echo "versions.json:"
cat "$SITE_DIR/versions.json"

# ---- root redirect to /latest/ ----
cat > "$SITE_DIR/index.html" <<'HTML'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="0; url=./latest/">
  <link rel="canonical" href="./latest/">
  <title>MeshCore Protocol Specification</title>
</head>
<body>
  <p>Redirecting to the <a href="./latest/">latest version</a>&hellip;</p>
</body>
</html>
HTML

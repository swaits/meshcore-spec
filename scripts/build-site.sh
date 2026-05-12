#!/usr/bin/env sh
# Build the full multi-version site into ./_site/:
#   - "latest" from the current HEAD
#   - one subtree per v* git tag
#
# Each per-version build gets MDBOOK_OUTPUT__HTML__SITE_URL set so its
# canonical URL and sitemap are correct for the deployed location.
# Emits _site/versions.json (newest first; consumed by
# theme/version-picker.js) and a root index.html that redirects to
# /latest/.
#
# Intended to be called via `just build-site`. SITE_BASE can be
# overridden to deploy under a different URL prefix; the default
# targets https://swaits.github.io/meshcore-spec/.

set -eu

SITE_BASE="${SITE_BASE:-/meshcore-spec}"
WORKSPACE="$(pwd)"
SITE_DIR="$WORKSPACE/_site"

# Section grouping for GitHub Actions logs; noop locally.
group() { printf '::group::%s\n' "$1"; }
endgroup() { printf '::endgroup::\n'; }
warn() { printf '::warning::%s\n' "$1"; }

rm -rf "$SITE_DIR"
mkdir -p "$SITE_DIR"

# ---- latest (current HEAD) ----
group "build latest"
MDBOOK_OUTPUT__HTML__SITE_URL="${SITE_BASE}/latest/" \
    mdbook build "$WORKSPACE" -d "$SITE_DIR/latest"
endgroup

# ---- each v* tag ----
# Each tag is built from its own git worktree so today's mdbook config
# / theme files don't bleed into older builds.
TAGS="$(git tag --list 'v*' --sort=-v:refname 2>/dev/null || true)"
for tag in $TAGS; do
    [ -z "$tag" ] && continue
    group "build $tag"
    wt="$(mktemp -d -t mdbook-tag-XXXXXX)"
    git worktree add --detach "$wt" "$tag"
    if [ -f "$wt/book.toml" ]; then
        if ! MDBOOK_OUTPUT__HTML__SITE_URL="${SITE_BASE}/${tag}/" \
             mdbook build "$wt" -d "$SITE_DIR/${tag}"; then
            warn "mdbook build failed for ${tag}; skipping"
            rm -rf "${SITE_DIR:?}/${tag:?}"
        fi
    else
        warn "${tag} has no book.toml; skipping"
    fi
    git worktree remove --force "$wt"
    endgroup
done

# ---- versions.json (consumed by theme/version-picker.js) ----
# Newest first; "latest" always at the top.
{
    printf '['
    printf '"latest"'
    for tag in $TAGS; do
        [ -z "$tag" ] && continue
        [ -d "$SITE_DIR/$tag" ] || continue
        printf ',"%s"' "$tag"
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

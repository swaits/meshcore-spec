// version-picker.js
//
// Renders a version dropdown in the mdBook menu bar for multi-version
// deployments. Reads /<base>/versions.json at page load and lets the
// reader switch to the same page in a different version.
//
// The deployed URL layout is <base>/<version>/<page>, where <version>
// is "latest" or a semver-like tag (e.g., "v0.1.0"). When the reader
// chooses a different version, the picker navigates to the matching
// page under the new version subtree; if that page doesn't exist in
// the target version, the browser will show a 404, which is fine for
// a v0.1 deployment.

(function () {
  'use strict';

  // Match the version segment in a path. Accepts "latest" or "vX[.Y[.Z]][-pre]".
  var VERSION_RE = /\/(latest|v\d+(?:\.\d+){0,2}(?:-[A-Za-z0-9.]+)?)(\/|$)/;

  function parseLocation() {
    var path = window.location.pathname;
    var m = path.match(VERSION_RE);
    if (!m) return null;
    var version = m[1];
    var versionStart = m.index;
    var basePath = path.substring(0, versionStart + 1);
    var pagePath = path.substring(versionStart + 1 + version.length);
    return { version: version, basePath: basePath, pagePath: pagePath };
  }

  function buildPicker(versions, current, basePath, pagePath) {
    var wrap = document.createElement('div');
    wrap.className = 'version-picker';
    wrap.setAttribute('role', 'group');
    wrap.setAttribute('aria-label', 'Spec version');

    var label = document.createElement('span');
    label.className = 'version-picker-label';
    label.textContent = 'version:';
    wrap.appendChild(label);

    var select = document.createElement('select');
    select.className = 'version-picker-select';
    select.setAttribute('aria-label', 'Choose spec version');

    for (var i = 0; i < versions.length; i++) {
      var v = versions[i];
      var opt = document.createElement('option');
      opt.value = v;
      opt.textContent = (v === 'latest') ? 'latest (main)' : v;
      if (v === current) opt.selected = true;
      select.appendChild(opt);
    }

    select.addEventListener('change', function (e) {
      var next = e.target.value;
      if (!next || next === current) return;
      window.location.pathname = basePath + next + pagePath;
    });

    wrap.appendChild(select);
    return wrap;
  }

  function install() {
    var loc = parseLocation();
    if (!loc) return;

    fetch(loc.basePath + 'versions.json', { cache: 'no-cache' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        if (!data) return;
        // Accepted shapes:
        //   ["latest", "v0.1.0"]
        //   { "versions": ["latest", "v0.1.0"] }
        var versions = Array.isArray(data) ? data : (data && data.versions);
        if (!versions || !versions.length) return;

        var picker = buildPicker(versions, loc.version, loc.basePath, loc.pagePath);

        // Prefer slotting into mdBook's menu bar; fall back to floating.
        var slot = document.querySelector('.right-buttons');
        if (slot) {
          slot.insertBefore(picker, slot.firstChild);
        } else {
          picker.classList.add('version-picker-floating');
          document.body.appendChild(picker);
        }
      })
      .catch(function (err) {
        // Non-fatal: dev / file:// / pre-deploy will all land here.
        if (window.console) console.warn('version-picker:', err);
      });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', install);
  } else {
    install();
  }
})();

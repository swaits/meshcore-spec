// version-picker.js
//
// Shows the current spec version in the mdBook menu bar. On a deployed
// multi-version site (path like <base>/<version>/<page>) it upgrades
// into a dropdown that switches between versions. On a single-version
// or local build (file:// or no versions.json reachable) it just
// renders a static "version: <name>" label so the reader can always
// see which version they're reading.

(function () {
  'use strict';

  // Match the version segment in a path. Accepts "latest" or "vX[.Y[.Z]][-pre]".
  var VERSION_RE = /\/(latest|v\d+(?:\.\d+){0,2}(?:-[A-Za-z0-9.]+)?)(\/|$)/;

  function labelFor(version) {
    return (version === 'latest') ? 'latest (main)' : version;
  }

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

  function buildLabel(version) {
    var wrap = document.createElement('div');
    wrap.className = 'version-picker version-picker-label-only';
    wrap.setAttribute('role', 'group');
    wrap.setAttribute('aria-label', 'Spec version');

    var prefix = document.createElement('span');
    prefix.className = 'version-picker-label';
    prefix.textContent = 'version:';
    wrap.appendChild(prefix);

    var name = document.createElement('span');
    name.className = 'version-picker-name';
    name.textContent = labelFor(version);
    wrap.appendChild(name);

    return wrap;
  }

  function buildDropdown(versions, current, basePath, pagePath) {
    var wrap = document.createElement('div');
    wrap.className = 'version-picker';
    wrap.setAttribute('role', 'group');
    wrap.setAttribute('aria-label', 'Spec version');

    var prefix = document.createElement('span');
    prefix.className = 'version-picker-label';
    prefix.textContent = 'version:';
    wrap.appendChild(prefix);

    var select = document.createElement('select');
    select.className = 'version-picker-select';
    select.setAttribute('aria-label', 'Choose spec version');

    for (var i = 0; i < versions.length; i++) {
      var v = versions[i];
      var opt = document.createElement('option');
      opt.value = v;
      opt.textContent = labelFor(v);
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

  function mount(picker) {
    var slot = document.querySelector('.right-buttons');
    if (slot) {
      slot.insertBefore(picker, slot.firstChild);
    } else {
      picker.classList.add('version-picker-floating');
      document.body.appendChild(picker);
    }
  }

  function install() {
    var loc = parseLocation();
    var current = loc ? loc.version : 'latest';

    // Always mount the label first — visible immediately, even before
    // (or without) a versions.json fetch.
    var picker = buildLabel(current);
    mount(picker);

    // Only attempt the upgrade-to-dropdown path when we have a real
    // version segment in the URL. Without one (e.g., file:// or local
    // `just build` opened directly), we can't compute navigation
    // targets, so leave the label as-is.
    if (!loc) return;

    fetch(loc.basePath + 'versions.json', { cache: 'no-cache' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        if (!data) return;
        // Accepted shapes:
        //   ["latest", "v0.1.0"]
        //   { "versions": ["latest", "v0.1.0"] }
        var versions = Array.isArray(data) ? data : (data && data.versions);
        if (!versions || versions.length < 2) return;

        var dropdown = buildDropdown(versions, current, loc.basePath, loc.pagePath);
        picker.replaceWith(dropdown);
      })
      .catch(function (err) {
        // Non-fatal: keep the label-only widget mounted.
        if (window.console) console.warn('version-picker:', err);
      });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', install);
  } else {
    install();
  }
})();

/**
 * MiniNAS UI Widgets
 * Zentrale JS-Komponenten: Panel-Toggle, Testparm-Check, Permission-Matrix
 * Vanilla JS, keine Abhängigkeiten
 */

// ── Panel Toggle ─────────────────────────────────────────────────
function mnTogglePanel(id) {
  document.querySelectorAll('.mn-panel').forEach(function(p) {
    if (p.id !== id) p.style.display = 'none';
  });
  var el = document.getElementById(id);
  el.style.display = (el.style.display === 'none') ? 'block' : 'none';
  if (el.style.display === 'block') {
    el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
}

// ── Testparm AJAX ────────────────────────────────────────────────
function mnRunTestparm() {
  var icon   = document.getElementById('testparm-icon');
  var result = document.getElementById('testparm-result');
  icon.innerHTML = '<i class="ti ti-loader-2" style="animation:mn-spin 0.8s linear infinite;"></i>';
  result.textContent = 'Checking...';
  result.style.color = '';

  fetch('testparm.cgi')
    .then(function(r) { return r.json(); })
    .then(function(data) {
      if (data.ok) {
        icon.className = 'mn-qa-icon qa-green';
        icon.innerHTML = '<i class="ti ti-circle-check"></i>';
        result.textContent = 'Config OK';
        result.style.color = 'var(--mn-green)';
      } else {
        icon.className = 'mn-qa-icon qa-amber';
        icon.style.background = '#3a1a1a';
        icon.style.color = 'var(--mn-red)';
        icon.innerHTML = '<i class="ti ti-alert-circle"></i>';
        result.textContent = 'Syntax error!';
        result.style.color = 'var(--mn-red)';
      }
    })
    .catch(function() {
      icon.innerHTML = '<i class="ti ti-alert-circle"></i>';
      result.textContent = 'Check failed';
      result.style.color = 'var(--mn-red)';
    });
}

// ── Permission Matrix Widget ──────────────────────────────────────
var MnPerm = {
  section: '',

  // Oktal-String → Checkboxen setzen + Mode-Feld aktualisieren
  fromMode: function(modeStr) {
    var digits = modeStr.replace(/^0+/, '');
    while (digits.length < 3) digits = '0' + digits;
    var u = parseInt(digits[0], 10);
    var g = parseInt(digits[1], 10);
    var o = parseInt(digits[2], 10);
    var map = { u: u, g: g, o: o };
    ['u','g','o'].forEach(function(who) {
      var v = map[who];
      document.getElementById('perm-' + who + '-r').checked = !!(v & 4);
      document.getElementById('perm-' + who + '-w').checked = !!(v & 2);
      document.getElementById('perm-' + who + '-x').checked = !!(v & 1);
    });
    MnPerm.updateModeField();
  },

  // Checkboxen → Oktal-String berechnen und in Mode-Feld schreiben
  updateModeField: function() {
    function bits(who) {
      return (document.getElementById('perm-' + who + '-r').checked ? 4 : 0) +
             (document.getElementById('perm-' + who + '-w').checked ? 2 : 0) +
             (document.getElementById('perm-' + who + '-x').checked ? 1 : 0);
    }
    var mode = '0' + bits('u') + bits('g') + bits('o');
    var field = document.getElementById('perm-mode-display');
    if (field) field.value = mode;
    return mode;
  },

  // Dropdowns mit Users/Groups füllen und vorbelegen
  loadUsersGroups: function(currentOwner, currentGroup, callback) {
    fetch('get_users_groups.cgi')
      .then(function(r) { return r.json(); })
      .then(function(data) {
        var uSel = document.getElementById('perm-owner');
        var gSel = document.getElementById('perm-group');
        if (!uSel || !gSel) return;

        uSel.innerHTML = data.users.map(function(u) {
          var sel = (u === currentOwner) ? ' selected' : '';
          return '<option' + sel + '>' + u + '</option>';
        }).join('');

        gSel.innerHTML = data.groups.map(function(g) {
          var sel = (g === currentGroup) ? ' selected' : '';
          return '<option' + sel + '>' + g + '</option>';
        }).join('');

        if (callback) callback();
      })
      .catch(function() {
        var status = document.getElementById('perm-status');
        if (status) {
          status.textContent = 'Error loading users/groups';
          status.style.color = 'var(--mn-red)';
        }
      });
  },

  // Apply: POST an set_permissions.cgi, Ergebnis anzeigen
  apply: function(onSuccess) {
    var section = MnPerm.section;
    var owner   = document.getElementById('perm-owner').value;
    var group   = document.getElementById('perm-group').value;
    var mode    = document.getElementById('perm-mode-display').value;
    var status  = document.getElementById('perm-status');

    if (!mode.match(/^[0-7]{4}$/)) {
      status.textContent = 'Invalid mode';
      status.style.color = 'var(--mn-red)';
      return;
    }

    status.textContent = 'Applying...';
    status.style.color = 'var(--mn-muted)';

    fetch('set_permissions.cgi', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: 'section=' + encodeURIComponent(section) +
            '&owner='   + encodeURIComponent(owner)   +
            '&group='   + encodeURIComponent(group)   +
            '&mode='    + encodeURIComponent(mode)
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
      if (data.ok) {
        status.textContent = 'Applied: ' + data.msg;
        status.style.color = 'var(--mn-green)';
        if (onSuccess) onSuccess(data.msg);
      } else {
        status.textContent = 'Error: ' + data.msg;
        status.style.color = 'var(--mn-red)';
      }
    })
    .catch(function() {
      status.textContent = 'Request failed';
      status.style.color = 'var(--mn-red)';
    });
  }
};

// ── Dashboard: Permission-Panel inline ───────────────────────────
function mnPermPanel(section) {
  var panel = document.getElementById('perm-panel');
  if (!panel) return;

  // Gleiche Zeile nochmal → schliessen
  if (MnPerm.section === section && panel.style.display !== 'none') {
    panel.style.display = 'none';
    MnPerm.section = '';
    return;
  }

  MnPerm.section = section;
  var titleEl = document.getElementById('perm-panel-title');
  if (titleEl) titleEl.textContent = 'Permissions: ' + section;

  var status = document.getElementById('perm-status');
  if (status) { status.textContent = 'Loading...'; status.style.color = 'var(--mn-muted)'; }

  // Panel hinter die angeklickte Zeile verschieben
  var targetRow = document.querySelector('#shares-table tr[data-section="' + section + '"]');
  if (targetRow && targetRow.parentNode) {
    targetRow.parentNode.insertBefore(
      panel.parentNode.removeChild(panel),
      targetRow.nextSibling
    );
  }
  panel.style.display = 'block';
  panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

  // Aktuelle Werte aus Tabellenzelle lesen
  var permCell = targetRow ? targetRow.querySelector('.mn-perm-cell') : null;
  var modeStr = '0770', currentOwner = '', currentGroup = '';
  if (permCell) {
    var parts = permCell.textContent.trim().split(' ');
    modeStr = parts[0] || '0770';
    var og = (parts[1] || ':').split(':');
    currentOwner = og[0] || '';
    currentGroup = og[1] || '';
  }

  MnPerm.loadUsersGroups(currentOwner, currentGroup, function() {
    MnPerm.fromMode(modeStr);
    if (status) status.textContent = '';
  });
}

function mnApplyPerms() {
  MnPerm.apply(function(newPerm) {
    // Permissions-Zelle im Dashboard aktualisieren
    var row = document.querySelector('#shares-table tr[data-section="' + MnPerm.section + '"]');
    if (row) {
      var cell = row.querySelector('.mn-perm-cell');
      if (cell) cell.textContent = newPerm;
    }
  });
}

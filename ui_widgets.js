/**
 * MiniNAS UI Widgets
 * Zentrale JS-Komponenten: Panel-Toggle, Testparm-Check, Permission-Matrix
 * Vanilla JS, keine Abhängigkeiten
 */

// ── Panel Toggle wurde entfernt: New Share/New User sind jetzt eigene
// Seiten (provision_user.cgi) statt Inline-Panels. Die Permission-Panel
// im Dashboard nutzt ihre eigene mnPermPanel()-Logik weiter unten.

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

// ── Sidebar (Hamburger-Menü, rechts) ─────────────────────────────
// Öffnet sich von rechts über das Dashboard. Immer geschlossen beim Laden.
// Beim Klick auf eine Aktion navigiert der Browser normal weg; bei
// Rücksprung zum Dashboard ist die Sidebar wieder zu, da der Zustand
// nicht persistiert wird (bewusst - kein localStorage).
function mnSidebarOpen() {
  var sb = document.getElementById('mn-sidebar');
  var ov = document.getElementById('mn-sidebar-overlay');
  var hb = document.querySelector('.mn-hamburger');
  if (sb) sb.classList.add('mn-open');
  if (ov) ov.classList.add('mn-open');
  if (hb) hb.classList.add('mn-hidden');
}

function mnSidebarClose() {
  var sb = document.getElementById('mn-sidebar');
  var ov = document.getElementById('mn-sidebar-overlay');
  var hb = document.querySelector('.mn-hamburger');
  if (sb) sb.classList.remove('mn-open');
  if (ov) ov.classList.remove('mn-open');
  if (hb) hb.classList.remove('mn-hidden');
}

// ── Wake & measure (Disk-Kachel) ──────────────────────────────────
function mnWakeAndMeasure() {
  var btn = document.getElementById('wake-measure-btn');
  var status = document.getElementById('wake-measure-status');
  if (btn) { btn.disabled = true; }
  if (status) { status.textContent = 'Waking disks...'; status.style.color = 'var(--mn-muted)'; }

  fetch('update_cache.cgi')
    .then(function(r) { return r.json(); })
    .then(function(data) {
      if (data.ok) {
        if (status) { status.textContent = 'Updated ' + data.timestamp; status.style.color = 'var(--mn-green)'; }
        // Dashboard neu laden, damit die frisch gemessenen Werte erscheinen.
        setTimeout(function() { window.location.reload(); }, 600);
      } else {
        if (status) { status.textContent = 'Update failed'; status.style.color = 'var(--mn-red)'; }
        if (btn) { btn.disabled = false; }
      }
    })
    .catch(function() {
      if (status) { status.textContent = 'Request failed'; status.style.color = 'var(--mn-red)'; }
      if (btn) { btn.disabled = false; }
    });
}

// ── Share editor: Storage location dropdown ──────────────────────
// Setzt das Path-Feld auf <mount>/<share name> wenn eine Disk gewählt wird.
// Jede <option> trägt ihren Basis-Pfad in data-mount (auch "Local" hat einen
// echten Wert, /srv) - so bleibt die Logik hier einfach und ohne Sonderfall.
// ── Share editor: Storage location + Path (Präfix fest, Rest editierbar) ──
// Der Pfad-Präfix (Disk-Mountpoint bzw. /srv) wird durch das Dropdown
// bestimmt und ist nicht editierbar - verhindert, dass Dropdown-Auswahl und
// tatsächlicher Pfad auseinanderlaufen. Nur der Teil dahinter (Suffix,
// i.d.R. der Share-Name) ist frei editierbar. Beide Teile werden bei jeder
// Änderung zum vollen Pfad zusammengesetzt und ins Hidden-Field f_path
// geschrieben, das tatsächlich abgeschickt wird.
function mnApplyStorageLocation(sel) {
  var opt = sel.options[sel.selectedIndex];
  var mount = (opt.getAttribute('data-mount') || '/srv').replace(/\/+$/, '');
  var prefixLabel = document.getElementById('path_prefix_label');
  if (prefixLabel) prefixLabel.textContent = mount + '/';
  mnUpdateFullPath();
}

function mnUpdateFullPath() {
  var prefixLabel = document.getElementById('path_prefix_label');
  var suffixInput = document.getElementById('share_path_suffix');
  var pathInput = document.getElementById('share_path_input');
  if (!prefixLabel || !suffixInput || !pathInput) return;
  // Präfix-Label enthält den abschliessenden Slash schon (siehe oben),
  // daher hier nur direkt aneinanderhängen.
  pathInput.value = prefixLabel.textContent + suffixInput.value.trim();
}

// ── Share editor: Tab-Taste im Raw-Parameter-Textfeld -> 4 Spaces ──
// (statt Fokus-Wechsel zum nächsten Formularelement, wie es Tab normalerweise tut)
function mnHandleRawTab(e) {
  if (e.key !== 'Tab') return;
  e.preventDefault();
  var ta = e.target;
  var start = ta.selectionStart, end = ta.selectionEnd, val = ta.value;
  ta.value = val.substring(0, start) + '    ' + val.substring(end);
  ta.selectionStart = ta.selectionEnd = start + 4;
}
(function() {
  var ta = document.getElementById('raw_ta');
  if (ta) ta.addEventListener('keydown', mnHandleRawTab);
})();

// ── Permissions page: Checkbox-Matrix aus dem aktuellen Mode initialisieren ──
// Section-Name und Mode kommen aus dem #mn-perm-init data-Element (siehe
// edit_permissions.cgi) statt in JS-Code interpoliert zu werden - hält CGI
// (Daten/Struktur) und JS (Verhalten) sauber getrennt.
function mnInitPermissions() {
  var initEl = document.getElementById('mn-perm-init');
  if (!initEl) return;
  var section = initEl.getAttribute('data-section');
  var mode = initEl.getAttribute('data-mode') || '0770';

  var digits = mode.replace(/^0+/, '');
  while (digits.length < 3) digits = '0' + digits;
  var vals = { u: parseInt(digits[0], 10), g: parseInt(digits[1], 10), o: parseInt(digits[2], 10) };
  ['u', 'g', 'o'].forEach(function(who) {
    var v = vals[who];
    var r = document.getElementById('perm-' + who + '-r');
    var w = document.getElementById('perm-' + who + '-w');
    var x = document.getElementById('perm-' + who + '-x');
    if (r) r.checked = !!(v & 4);
    if (w) w.checked = !!(v & 2);
    if (x) x.checked = !!(v & 1);
  });
  if (typeof MnPerm !== 'undefined') {
    MnPerm.section = section;
    MnPerm.updateModeField();
  }
}

// Mehrfach-Fallback: sofort, DOMContentLoaded, und window.onload,
// damit die Initialisierung unabhängig vom Browser-Render-Timing greift.
if (document.getElementById('mn-perm-init')) {
  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(mnInitPermissions, 0);
  } else {
    document.addEventListener('DOMContentLoaded', mnInitPermissions);
  }
  window.addEventListener('load', mnInitPermissions);
}

function mnApplyAndRedirect() {
  var initEl = document.getElementById('mn-perm-init');
  if (typeof MnPerm !== 'undefined' && initEl) {
    MnPerm.section = initEl.getAttribute('data-section');
    MnPerm.apply(function(newPerm) {
      // Webmin-konformer Redirect: normaler Link-Click statt location-Manipulation,
      // verhindert dass Webmin den Frame-Kontext verliert.
      setTimeout(function() {
        var backLink = document.getElementById('mn-back-link');
        if (backLink) backLink.click();
      }, 600);
    });
  }
}

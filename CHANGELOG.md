# Changelog

## v0.9.3.3

Bugfix: Checkboxen auf "Share permissions: [User]" (`edit_user_shares.cgi`)
blieben nach dem Speichern optisch leer, obwohl die Zuweisung korrekt
gespeichert wurde (Dashboard zeigte es richtig an).

- Ursache: eigene, veraltete Regex zur Checkbox-Vorbelegung
  (`valid users\s*=\s*\b\Q$u\E\b`) matchte nur, wenn der User als **erster**
  Eintrag direkt nach dem `=` steht. Neu hinzugefügte User werden von
  `save_user_shares.cgi` aber ans Ende der Liste angehängt - die Checkbox
  erkannte die eigene, gerade gespeicherte Zuweisung dadurch nicht wieder.
- Fix: `edit_user_shares.cgi` nutzt jetzt `mn_get_share_path()` und
  `mn_get_share_users()` wie der Rest des Moduls, statt eine eigene,
  unvollständige Regex zu pflegen. Per Test verifiziert: User an beliebiger
  Position in der Liste wird korrekt erkannt.

## v0.9.3.2

Etappe 4b (Rest) + Punkte 1-5 aus der Vereinfachungs-Liste.

### 1. `index.cgi` aufgeteilt (Collect vs. Render)
- Neue `mn_collect_dashboard_data()` in `mininas-lib.pl`: sammelt Samba-Status,
  `/proc/mounts`-Abgleich, Share-Status, User-Liste, Storage-Cache-Update
  an einer Stelle. `index.cgi` selbst ruft nur noch auf und rendert.
- Neue `mn_render_disk_tile()` in `ui_components.pl` (aus `index.cgi`
  herausgelöst, Verhalten 1:1 übernommen).
- Verhalten unverändert: "Samba Status"-Kachel wertet weiterhin nur Shares
  mit konfiguriertem Pfad; Storage-Cache-Update weiterhin nur wenn laut
  `/proc/diskstats` ohnehin schon eine Disk aktiv ist.

### 2. Weitere Share-Accessor-Funktionen
- Neue `mn_get_share_comment()` und `mn_get_share_browseable()` in
  `mininas-lib.pl`, analog zu `mn_get_share_path()`/`mn_get_share_users()`
  (aktuell noch ungenutzt, für kommende Erweiterungen vorbereitet).

### 3+4. `mn_run()`-Wrapper, letzte direkte `system()`-Aufrufe zentralisiert
- Neue `mn_run(@cmd)` in `mininas-lib.pl`: Listen-Form-Ausführung mit
  eingefangenem stderr, liefert `(erfolg, fehlerausgabe)` zurück statt dass
  jeder Aufrufer `$?` selbst auswertet und sich eine kontextlose
  Fehlermeldung ausdenkt. Per Test verifiziert: Erfolgsfall, Fehlerfall mit
  stderr-Capture, und Shell-Metazeichen in Argumenten werden nicht
  interpretiert (Listen-Form bleibt erhalten).
- Neue `mn_remove_directory_tree()` und `mn_close_smb_connections()` in
  der Lib - die letzten beiden direkten `system()`-Aufrufe in `.cgi`-Dateien
  (`confirm_delete.cgi`, `delete_user_exec.cgi`) laufen jetzt darüber.
  Damit sitzt jeder Shell-Aufruf im ganzen Modul in `mininas-lib.pl`.

### 5. Fonts/Icons lokal gehostet
- Tabler Icons 3.19.0 (nur "outline"-Set, `ti-*`) und Noto Sans 400/500
  (latin, deckt deutsche Umlaute ab) liegen jetzt unter `assets/` im Modul
  statt von Google Fonts/jsDelivr geladen zu werden - keine externe
  Abhängigkeit mehr, funktioniert auch ohne Internetzugang.
- Nur `woff2` statt `woff2`+`woff`+`ttf` (ausreichend für jeden Browser der
  letzten ~7 Jahre) - 1.2 MB gesamt statt 14 MB+ an vollständigen
  Font-Paketen.
- **Bitte beim ersten Deploy kurz die Browser-Konsole/Netzwerk-Tab prüfen**,
  ob `assets/fonts/*.css` und `assets/icons/*.css` sauber geladen werden -
  konnte in der Sandbox nicht gegen einen echten Webmin-Server getestet
  werden, nur die Dateistruktur und Pfade verifiziert.

## v0.9.3.1

Etappe 4b: wiederkehrende UI-Bausteine zentralisiert (keine funktionalen
Änderungen, per Test verifiziert byte-identisches HTML).

- Neue `mn_page_header($title, %opts)` in `ui_components.pl`: ersetzt das
  8-10x wiederholte "Zurück-Link + Seitentitel"-Muster. Unterstützt
  optionales Titel-Icon (`icon`, `icon_color`).
- Neue `mn_form_title($text, %opts)`: ersetzt das 6x wiederholte
  Formular-Titelzeilen-Muster. Unterstützt `icon`, `icon_color` (nur Icon
  gefärbt) und `color` (ganzer Titel gefärbt, für Lösch-/Warnhinweise).
- Umgestellt: `change_password.cgi`, `delete_share.cgi`,
  `delete_user_form.cgi`, `edit_section.cgi` (3 Formular-Titel),
  `edit_user_shares.cgi`, `manage_disks.cgi`, `manage_home.cgi`,
  `provision_user.cgi`, `edit_permissions.cgi`.
- `confirm_delete.cgi` bewusst NICHT umgestellt (einziger Seiten-Header ohne
  Zurück-Link, eigenes Muster - Funktion dafür verbiegen wäre
  Über-Engineering für einen einzigen Anwendungsfall).
- Button- und Formularfeld-Zeilen bewusst NICHT extrahiert: bereits
  Ein-Zeiler mit stark variierendem Text/Icon/Verhalten pro Aufruf: eine
  Wrapper-Funktion dafür wäre am Ende so lang wie die aktuelle print-Zeile,
  nur mit einer Abstraktionsebene mehr - kein echter Gewinn.
- Nebenbei: `delete_user_form.cgi` nutzte noch die alte inline
  valid-users/read-list-Regex statt `mn_get_share_users()` (in Etappe 3a.5
  übersehen) - beim Anfassen der Datei gleich mit dedupliziert.

## v0.9.3

Etappe 4a: CGI-Boilerplate zentralisiert (keine funktionalen Änderungen).

- Neues `mininas-init.pl` als zentraler Einstiegspunkt: bündelt
  `use WebminCore;`-Folgeschritte (`$main::default_charset`, `&init_config()`,
  `&ReadParse()`, `require mininas-lib.pl`, `require ui_components.pl`), die
  vorher in allen 21 `.cgi`-Dateien einzeln (und uneinheitlich - z.B. Charset
  nur zufällig in manchen Dateien gesetzt) wiederholt wurden.
- Jede `.cgi`-Datei hat jetzt denselben minimalen Kopf:
  ```perl
  use strict;
  use warnings;
  BEGIN { push(@INC, ".."); }
  use WebminCore;
  require 'mininas/mininas-init.pl';
  ```
  `use strict`/`use warnings`/`use WebminCore` bleiben bewusst pro Datei
  bestehen - beides sind in Perl compile-zeit-lokale Effekte (Pragma bzw.
  Symbol-Import), die sich nicht über `require` an den Aufrufer weiterreichen
  lassen. Nur das, was tatsächlich reine Laufzeit-Wirkung hat, wandert in
  `mininas-init.pl`.
- Seiten-spezifische `use`-Zeilen (`JSON::PP`, `Encode`) bleiben unverändert
  in der jeweiligen Datei.
- Alle 21 `.cgi`-Dateien + `mininas-lib.pl` + `mininas-init.pl` +
  `ui_components.pl` gegen einen WebminCore-Stub kompiliert, keine Fehler.

## v0.9.2.1

Security-Hardening-Durchgang (5 Etappen) plus zwei Live-Bugfixes, in
Zusammenarbeit mit Claude erarbeitet und gegenreviewt (ChatGPT- und
Gemini-Reviews mit eingeflossen, wo zutreffend).

### Security

- **Path-Whitelist-Bypass geschlossen**: `mn_validate_path()` griff bisher nur,
  wenn `path_action` ungleich `none` war. Bei `path_action=none` konnte ein
  beliebiger Pfad (auch ausserhalb `/mnt`/`/srv`) ungeprüft in die `smb.conf`
  geschrieben werden. Validierung greift jetzt immer, sobald ein Pfad gesetzt ist.
- **Share-Namen-Validierung**: neue `mn_validate_section_name()`; verhindert
  Config-Injection und gespeichertes XSS über den Share-Namen.
- **User-Listen-Validierung**: `valid users`/`read list`-Freitextfelder in
  `save_section.cgi` laufen jetzt durch dieselbe Prüfung wie bei der
  User-Anlage.
- Fehlende `html_escape()`-Stellen in `edit_section.cgi` und
  `edit_permissions.cgi` nachgezogen (Share-Name, Pfad).
- **Full-Cleanup-Schutz**: `confirm_delete.cgi` verweigert `rm -rf`, wenn der
  Share-Pfad exakt die Wurzel einer konfigurierten Disk ist (neue
  `mn_path_is_disk_root()`).
- **Backup-Fehler bricht jetzt ab**: schlägt das `cp`-Backup vor dem Schreiben
  der `smb.conf` fehl, wird abgebrochen statt ungeschützt weiterzuschreiben.
- **Denylist für Disk-Pfade**: `manage_disks.cgi` verweigert offensichtliche
  Systempfade (`/etc`, `/root`, `/proc`, `/sys`, `/`, ...) als Disk-Mountpoint.
- Mindestlänge für initiales Passwort bei User-Anlage vereinheitlicht
  (6 Zeichen, wie beim Passwort-Ändern).
- Log-Injection-Schutz: Newlines in Log-Nachrichten werden gefiltert.
- **Symlink-Schutz** vor `rm -rf`/`mv`/`rsync` in `mn_remove_home_dir`,
  `mn_rename_share_dir`, `mn_copy_share_dir`/`mn_move_share_dir` sowie im
  direkten `rm -rf` in `confirm_delete.cgi`.
- `ui_widgets.js`: Dropdown-Befüllung für Owner/Group auf `createElement`/
  `textContent` statt `innerHTML` umgestellt (DOM-XSS-Härtung).
- `set_permissions.cgi` + `mn_set_ownership()`: natives `chown()`/`chmod()`
  statt `system('chown', ...)`/`system('chmod', ...)` — kein Fork/Exec mehr,
  Sicherheit hängt nicht mehr allein an der Username-Validierungs-Regex.

### Bugfixes (Datenintegrität)

- **Samba "last-line-wins"-Bug behoben**: Samba übernimmt bei mehrfach
  vorkommenden Parametern innerhalb derselben Section nur die *letzte*
  Instanz. `save_section.cgi`, `create_user.cgi` (Modus "group") und
  `save_user_shares.cgi` schrieben bisher für jeden User eine eigene
  `valid users =`-Zeile bzw. hängten neue Zeilen an bestehende an — dadurch
  verloren bei Multi-User-Shares alle bis auf den zuletzt geschriebenen User
  beim nächsten Speichern stillschweigend den Zugriff. Alle drei Stellen
  schreiben jetzt genau eine konsolidierte, deduplizierte Zeile pro Section.
- **Permissions-Checkboxen initialisierten nicht zuverlässig**: hingen bisher
  an `DOMContentLoaded`/`load`, die bei Webmins Authentic-Theme-Soft-Navigation
  nicht zwingend erneut feuern (nur ein vollständiger Reload triggert sie
  sicher). `edit_permissions.cgi` ruft `mnInitPermissions()` jetzt direkt
  inline am Ende des bei jedem Aufruf frisch generierten Seiten-HTML auf.
- **Share-Usage zeigte immer "1 GB"**: `mn_get_share_usage()` nutzte
  `du -sBG`, was jeden Wert zwischen 1 Byte und 1 GB aufrundet. Umgestellt
  auf `du -sh` (human-readable, z. B. "4.0K" für einen leeren Share).
  *Hinweis: bestehender Storage-Cache enthält bis zum nächsten "Wake &
  measure" noch alte Werte im alten Format.*

### Code-Qualität

- `use strict; use warnings;` in allen 21 `.cgi`-Dateien ergänzt (vorher:
  keine einzige hatte es).
- `$main::default_charset = 'utf-8'` konsistent auf allen 9 HTML-rendernden
  Seiten gesetzt (vorher nur zufällig in `edit_section.cgi`).
- Neue `mn_get_share_users()` in der Lib, ersetzt duplizierte Inline-Regex zur
  User-Extraktion in `index.cgi`, `edit_permissions.cgi`, `confirm_delete.cgi`.
- `edit_permissions.cgi` nutzt jetzt `mn_get_share_path()` statt eigenem
  Inline-Regex.

### Dokumentation

- README: kaputten Bildverweis auf `docs/dashboard-disk-badge.png` entfernt
  (Datei existiert nicht im Repo; `dashboard-full-overview.png` weiter oben
  in der README zeigt den Sachverhalt bereits ausreichend).

## v0.9.1

- Etappe 1 (Storage Cache System): `/var/lib/mininas/storage.cache` +
  `disks.conf`, sechs neue Lib-Funktionen, `update_cache.cgi`,
  `manage_disks.cgi`, Cache in vier bestehende CGIs eingebunden.
- Etappe 2 (Dashboard Layout Rebuild): rechtsseitiges Hamburger-Menü,
  Disk-Usage-Kacheln mit Fortschrittsbalken, Share-Usage-Anzeige.
- `mn_validate_path()` erlaubt beliebige Tiefe unter `/mnt`/`/srv` mit
  `..`-Traversal-Schutz.
- `save_section.cgi` "Create directory" triggert jetzt zuverlässig bei
  Pfadänderung.
- `mn_get_disk_usage`/`mn_disk_is_sleeping` akzeptieren auch Mountpoint-Pfade,
  nicht nur Block-Devices.
- Share-Usage "0B GB"-Anzeigefehler behoben.
- JS-Escaping-Bug behoben: JS aus Perl-`print`-Strings raus, in
  `ui_widgets.js`; CGI→JS-Daten laufen ausschliesslich über `data-*`-Attribute.
- Hamburger-Menü z-index/Positionierung gegen Authentic-Theme-Header korrigiert.

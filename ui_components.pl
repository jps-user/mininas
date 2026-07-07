# /usr/share/webmin/mininas/ui_components.pl
# Zentrale HTML-Bausteine für MiniNAS – Noto Sans + Tabler Icons (MIT)

package main;
use strict;
use warnings;

# ── Globales CSS + Fonts + Icons ────────────────────────────────
sub mn_head {
    return <<'HTML';
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;500&display=swap">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.19.0/dist/tabler-icons.min.css">
<style>
:root {
    --mn-bg:       #141414;
    --mn-surface:  #1e1e1e;
    --mn-surface2: #252525;
    --mn-border:   #2d2d2d;
    --mn-border2:  #3a3a3a;
    --mn-text:     #e8e8e8;
    --mn-muted:    #888;
    --mn-accent:   #4a9eed;
    --mn-green:    #3dba6f;
    --mn-amber:    #e6a817;
    --mn-red:      #e05454;
    --mn-purple:   #9b72d8;
    --mn-radius:   6px;
    --mn-font:     'Noto Sans', sans-serif;
    --mn-mono:     'Courier New', monospace;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body, .mn-wrap { font-family: var(--mn-font) !important; color: var(--mn-text); font-size: 17px; line-height: 1.5; }
.mn-wrap table { border-spacing: 0 !important; }
.mn-wrap { max-width: 1100px; padding: 0 4px; }

/* Kacheln */
.mn-tiles { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 14px; }
.mn-tile { background: var(--mn-surface); border: 0.5px solid var(--mn-border2); border-radius: var(--mn-radius); padding: 14px 16px; }
.mn-tile-label { font-size: 13px; color: var(--mn-muted); margin-bottom: 4px; }
.mn-tile-val { font-size: 24px; font-weight: 500; line-height: 1.2; }
.mn-tile-sub { font-size: 13px; color: var(--mn-muted); margin-top: 3px; }
.mn-tile-icon { font-size: 20px; float: right; opacity: 0.3; margin-top: -2px; }
.mn-tile-action { display: inline-flex; align-items: center; gap: 5px; font-size: 12px;
    color: var(--mn-accent); text-decoration: none; margin-top: 8px; }
.mn-tile-action:hover { text-decoration: underline; }

/* Quick Action Panels (ausklappbar) */
/* New Share/New User sind jetzt eigene Seiten statt Inline-Panels;
   die Permission-Panel im Dashboard stylt sich direkt inline. */

/* Status Bar */
.mn-statusbar { display: flex; flex-wrap: wrap; gap: 10px; align-items: center;
    background: var(--mn-surface); border: 0.5px solid var(--mn-border2);
    border-radius: var(--mn-radius); padding: 10px 14px; margin-bottom: 14px; font-size: 14px; }
.mn-sep { color: var(--mn-border2); }
.mn-dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; margin-right: 4px; vertical-align: middle; }
.dot-ok   { background: var(--mn-green); }
.dot-warn { background: var(--mn-amber); }
.dot-err  { background: var(--mn-red); }

/* Badges */
.badge { display: inline-block; padding: 1px 7px; border-radius: 3px; font-size: 12px; font-weight: 500; }
.badge-ok   { background: #1a3a2a; color: #5dcc8a; }
.badge-warn { background: #3a2d1a; color: #e6a817; }
.badge-err  { background: #3a1a1a; color: #e05454; }
.badge-rw   { background: #1a3a2a; color: #5dcc8a; }
.badge-ro   { background: #3a3a1a; color: #d9d96c; }
.badge-tm   { background: #2a1a3a; color: #b08ae0; }

/* Toolbar */
.mn-toolbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.mn-toolbar-title { font-size: 19px; font-weight: 500; }
.mn-toolbar-btns { display: flex; gap: 8px; }
.mn-btn { display: inline-flex; align-items: center; gap: 6px; font-size: 14px; font-family: var(--mn-font);
    padding: 7px 14px; border-radius: var(--mn-radius);
    border: 0.5px solid var(--mn-border2); background: var(--mn-surface2);
    color: var(--mn-text); cursor: pointer; text-decoration: none; }
.mn-btn:hover { border-color: #555; background: #2d2d2d; }
.mn-btn-primary { background: #1d3d5c; border-color: var(--mn-accent); color: var(--mn-accent); }
.mn-btn-primary:hover { background: #234870; }
.mn-btn-danger  { background: #3a1a1a; border-color: var(--mn-red); color: var(--mn-red); }
.mn-btn-danger:hover  { background: #4a2020; }

/* Quick Actions */
.mn-qa-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.mn-qa-btn { display: flex; align-items: center; gap: 10px; padding: 10px 12px;
    background: var(--mn-surface2); border: 0.5px solid var(--mn-border2);
    border-radius: var(--mn-radius); cursor: pointer; text-align: left;
    width: 100%; color: var(--mn-text); font-family: var(--mn-font); text-decoration: none; }
.mn-qa-btn:hover { border-color: #555; background: #2d2d2d; }
button.mn-qa-btn { font-size: inherit; }
@keyframes mn-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.mn-qa-icon { width: 34px; height: 34px; border-radius: var(--mn-radius);
    display: flex; align-items: center; justify-content: center; font-size: 19px; flex-shrink: 0; }
.qa-green  { background: #1a3a2a; color: var(--mn-green); }
.qa-blue   { background: #1a2a3a; color: var(--mn-accent); }
.qa-purple { background: #2a1a3a; color: var(--mn-purple); }
.qa-amber  { background: #3a2d1a; color: var(--mn-amber); }
.mn-qa-label { font-size: 14px; font-weight: 500; }
.mn-qa-sub   { font-size: 13px; color: var(--mn-muted); }

/* Tabellen */
.mn-section { background: var(--mn-surface); border: 0.5px solid var(--mn-border2);
    border-radius: var(--mn-radius); margin-bottom: 12px; overflow: hidden; }
.mn-section-head { font-size: 12px; font-weight: 500; color: var(--mn-muted); text-transform: uppercase;
    letter-spacing: 0.07em; padding: 10px 16px !important; border-bottom: 0.5px solid var(--mn-border); }

/* Tabellen-Wrapper: alleiniger Ort für horizontalen Innenabstand der Tabelle.
   !important ist hier notwendig, weil Webmin's Authentic Theme eine hochspezifische
   Regel "table td { padding: 0 }" mit !important mitbringt, die sonst gewinnt. */
.mn-table-wrap { padding: 0 16px !important; }

.mn-table { width: 100%; border-collapse: collapse !important; font-size: 14px; }
.mn-table th { text-align: left; color: var(--mn-muted); font-weight: 400 !important;
    padding: 10px 12px !important; border-bottom: 0.5px solid var(--mn-border); font-size: 13px; }
.mn-table td { padding: 10px 12px !important; border-bottom: 0.5px solid var(--mn-border) !important; vertical-align: middle; }
.mn-table tr:last-child td { border-bottom: none !important; }
.mn-table tr:hover td { background: var(--mn-surface2); }
.mn-table th:first-child, .mn-table td:first-child { padding-left: 0 !important; }
.mn-table th:last-child,  .mn-table td:last-child  { padding-right: 0 !important; text-align: center; }
.mn-mono { font-family: var(--mn-font); font-size: 13px; color: var(--mn-muted); }

/* Share-Zeile */
.mn-share-name { display: block; font-weight: 500; }
.mn-share-path { display: block; font-size: 12px; color: var(--mn-muted); margin-top: 2px; }


/* Icon-Buttons */
.mn-icon-btn { display: inline-flex; align-items: center; justify-content: center;
    width: 28px; height: 28px; border-radius: var(--mn-radius);
    border: 0.5px solid var(--mn-border2); background: none; cursor: pointer;
    color: var(--mn-muted); font-size: 17px; margin-left: 2px; text-decoration: none; }
.mn-icon-btn:hover { background: var(--mn-surface2); border-color: #555; color: var(--mn-text); }
.mn-icon-btn-del:hover { background: #3a1a1a; border-color: var(--mn-red); color: var(--mn-red); }

/* Grid Layout */
.mn-grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px; }

/* Activity Log */
.mn-log-row { display: flex; align-items: flex-start; gap: 10px;
    padding: 7px 14px; border-bottom: 0.5px solid var(--mn-border); font-size: 14px; }
.mn-log-row:last-child { border-bottom: none; }
.mn-log-time { color: var(--mn-muted); font-family: var(--mn-font); font-size: 13px; min-width: 50px; flex-shrink: 0; }
.mn-log-icon { font-size: 16px; color: var(--mn-muted); margin-top: 1px; flex-shrink: 0; }
.mn-log-msg { color: var(--mn-muted); }
.mn-log-who { color: var(--mn-text); font-weight: 500; }

/* Formulare */
.mn-form-wrap { background: var(--mn-surface); border: 0.5px solid var(--mn-border2);
    border-radius: var(--mn-radius); padding: 20px; margin-bottom: 12px; }
.mn-form-title { font-size: 15px; font-weight: 500; margin-bottom: 14px;
    padding-bottom: 10px; border-bottom: 0.5px solid var(--mn-border); }
.mn-form-row { display: flex; gap: 16px; margin-bottom: 12px; }
.mn-form-col { flex: 1; }
.mn-label { display: block; font-size: 13px; color: var(--mn-muted); margin-bottom: 5px; }
.mn-input { width: 100%; padding: 8px 10px; background: #2a2a2a; border: 0.5px solid var(--mn-border2);
    color: var(--mn-text); border-radius: var(--mn-radius); font-family: var(--mn-font); font-size: 14px; }
.mn-input:focus { outline: none; border-color: var(--mn-accent); }
.mn-select { width: 100%; padding: 8px 10px; background: #2a2a2a; border: 0.5px solid var(--mn-border2);
    color: var(--mn-text); border-radius: var(--mn-radius); font-family: var(--mn-font); font-size: 14px; }
.mn-textarea { width: 100%; padding: 8px 10px; background: #2a2a2a; border: 0.5px solid var(--mn-border2);
    color: var(--mn-text); border-radius: var(--mn-radius); font-family: var(--mn-mono);
    font-size: 14px; resize: vertical; }
.mn-textarea:focus, .mn-select:focus { outline: none; border-color: var(--mn-accent); }
.mn-hint { font-size: 12px; color: var(--mn-muted); margin-top: 4px; }
.mn-check-row { display: flex; gap: 20px; margin-bottom: 12px; }
.mn-check-label { display: flex; align-items: center; gap: 7px; font-size: 14px; cursor: pointer; }

/* Card-Auswahl (Radio) */
.mn-card-radio { display: none; }
.mn-card-label { display: block; border: 0.5px solid var(--mn-border2); border-radius: var(--mn-radius);
    padding: 16px; background: var(--mn-surface2); cursor: pointer; }
.mn-card-label:hover { border-color: #555; }
.mn-card-radio:checked + .mn-card-label { border: 1.5px solid var(--mn-accent); background: #1a2535; }
.mn-card-title { font-size: 15px; font-weight: 500; margin-bottom: 6px; color: var(--mn-text); }
.mn-card-desc  { font-size: 13px; color: var(--mn-muted); line-height: 1.4; }

/* Subpage Header */
.mn-page-header { display: flex; align-items: center; gap: 10px; margin-bottom: 18px; }
.mn-page-title  { font-size: 17px; font-weight: 500; }
.mn-page-back   { display: inline-flex; align-items: center; gap: 5px; font-size: 14px;
    color: var(--mn-muted); text-decoration: none; }
.mn-page-back:hover { color: var(--mn-text); }

/* Delete / Warn Cards */
.mn-del-card { display: block; padding: 14px 16px; background: var(--mn-surface2);
    border: 1.5px solid var(--mn-border2); border-radius: var(--mn-radius); cursor: pointer; margin-bottom: 8px; }
.mn-del-card:hover { border-color: #555; }
.mn-del-card input[type=radio] { display: none; }
.mn-del-card:has(input[value=share_only]:checked)  { border-color: var(--mn-accent); background: #1a2535; }
.mn-del-card:has(input[value=config_only]:checked) { border-color: var(--mn-accent); background: #1a2535; }
.mn-del-card:has(input[value=full_cleanup]:checked){ border-color: var(--mn-red);    background: #2a1a1a; }
.mn-del-card-title { font-size: 15px; font-weight: 500; margin-bottom: 3px; }
.mn-del-card-desc  { font-size: 13px; color: var(--mn-muted); }
</style>
<script src="ui_widgets.js"></script>
HTML
}

# mn_read_log und mn_log_icon sind in mininas-lib.pl definiert

1;

#!/usr/bin/perl
# manage_home.cgi - Home-Verzeichnis eines bestehenden Users nachträglich
# hinzufügen oder entfernen.

package main;
BEGIN { push(@INC, '..') }
use WebminCore;
&init_config();
&ReadParse();
require 'mininas/mininas-lib.pl';
require 'mininas/ui_components.pl';

my $u = $in{'user'};
&WebminCore::error('No user specified.') unless $u;
&WebminCore::error('Invalid username format.') unless mn_validate_username($u, 1);

# ── Aktion verarbeiten (POST) ─────────────────────────────────────
if ($in{'action'} eq 'add') {
    mn_add_home_dir($u)
        or &WebminCore::error("Failed to create home directory for '$u'.");
    write_mininas_log('HOME_ADD', "Created home directory for user $u.");
    &WebminCore::redirect('index.cgi');
    exit;
}

if ($in{'action'} eq 'remove') {
    mn_remove_home_dir($u)
        or &WebminCore::error("Failed to remove home directory for '$u'.");
    write_mininas_log('HOME_REMOVE', "Removed home directory for user $u.");
    &WebminCore::redirect('index.cgi');
    exit;
}

# ── Anzeige (GET) ──────────────────────────────────────────────────
my $home = mn_get_home_dir($u);

&WebminCore::ui_print_header(undef, 'Home Directory', '', undef, 0, 0);
print mn_head();
print "<div class='mn-wrap'>";
print "<div class='mn-page-header'>";
print "<a class='mn-page-back' href='index.cgi'><i class='ti ti-arrow-left'></i> Dashboard</a>";
print "<span class='mn-page-title'>Home Directory: ".&WebminCore::html_escape($u)."</span>";
print "</div>";

print "<div class='mn-form-wrap' style='max-width:600px;'>";

if ($home) {
    print "<div class='mn-form-title'><i class='ti ti-folder' style='margin-right:6px; color:var(--mn-green);'></i>Home directory exists</div>";
    print "<p class='mn-hint' style='margin-bottom:16px;'>Path: <span style='font-family:monospace; color:var(--mn-text);'>".&WebminCore::html_escape($home)."</span></p>";
    print "<form action='manage_home.cgi' method='post'>";
    print &WebminCore::ui_hidden('user', $u);
    print &WebminCore::ui_hidden('action', 'remove');
    print "<div style='display:flex; align-items:center; gap:10px;'>";
    # $home in einem JS-String (onclick/confirm): HTML-Escaping allein reicht hier
    # nicht, ein Apostroph im Pfad könnte sonst aus dem confirm()-String ausbrechen.
    my $home_js = $home; $home_js =~ s/(['\\])/\\$1/g;
    print "<button type='submit' class='mn-btn mn-btn-danger' onclick=\"return confirm('Permanently delete ".&WebminCore::html_escape($home_js)." and all its contents?');\"><i class='ti ti-trash'></i> Remove home directory</button>";
    print "<a href='index.cgi' class='mn-btn'><i class='ti ti-x'></i> Cancel</a>";
    print "</div>";
    print "</form>";
} else {
    print "<div class='mn-form-title'><i class='ti ti-folder-off' style='margin-right:6px; color:var(--mn-muted);'></i>No home directory</div>";
    print "<p class='mn-hint' style='margin-bottom:16px;'>This user currently has no home directory. Most Samba-only service accounts do not need one.</p>";
    print "<form action='manage_home.cgi' method='post'>";
    print &WebminCore::ui_hidden('user', $u);
    print &WebminCore::ui_hidden('action', 'add');
    print "<div style='display:flex; align-items:center; gap:10px;'>";
    print "<button type='submit' class='mn-btn mn-btn-primary'><i class='ti ti-folder-plus'></i> Create /home/".&WebminCore::html_escape($u)."</button>";
    print "<a href='index.cgi' class='mn-btn'><i class='ti ti-x'></i> Cancel</a>";
    print "</div>";
    print "</form>";
}

print "</div></div>";
&WebminCore::ui_print_footer('index.cgi', 'Back to Dashboard');

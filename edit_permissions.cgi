#!/usr/bin/perl
# edit_permissions.cgi - Eigene Seite für Owner, Group und Mode eines Shares

package main;
BEGIN { push(@INC, ".."); };
use WebminCore;
&init_config();
&ReadParse();
require 'mininas/mininas-lib.pl';
require 'mininas/ui_components.pl';

my $sec = $in{'section'};
if (!$sec) { &WebminCore::error("No section specified."); }

my ($lines_ref, $sections_ref) = parse_smb_sections_v2();
my ($target) = grep { $_->{name} eq $sec } @$sections_ref;
if (!$target) { &WebminCore::error("Section '$sec' not found."); }

my ($path) = ($target->{raw} =~ /path\s*=\s*([^\n]+)/i);
$path =~ s/^\s+|\s+$//g if $path;

# Aktuelle Permissions lesen
my ($cur_mode, $cur_owner, $cur_group) = ('0770', '', '');
if ($path && -d $path) {
    my @st = stat($path);
    if (@st) {
        $cur_mode  = sprintf("%04o", $st[2] & 07777);
        $cur_owner = (getpwuid($st[4]))[0] || $st[4];
        $cur_group = (getgrgid($st[5]))[0] || $st[5];
    }
}

# User und Gruppen für Dropdowns
my (@sys_users, @sys_groups);
if (open(my $fh, '<', '/etc/passwd')) {
    while (<$fh>) { my ($u) = split(':'); push(@sys_users, $u) if $u; }
    close($fh);
}
if (open(my $fh, '<', '/etc/group')) {
    while (<$fh>) { my ($g) = split(':'); push(@sys_groups, $g) if $g; }
    close($fh);
}

&WebminCore::ui_print_header(undef, "Permissions", "", undef, 0, 0);
print mn_head();
print "<div class='mn-wrap'>";
print "<div class='mn-page-header'>";
print "<a class='mn-page-back' href='index.cgi'><i class='ti ti-arrow-left'></i> Dashboard</a>";
print "<span class='mn-page-title'>Permissions: $sec</span>";
print "</div>";

print "<div class='mn-form-wrap' style='max-width:600px;'>";
print "<div class='mn-form-title'><i class='ti ti-shield' style='margin-right:6px; color:var(--mn-muted);'></i>Directory: <span style='font-family:monospace; color:var(--mn-muted);'>$path</span></div>";

# Owner + Group + Mode Zeile
print "<div class='mn-form-row'>";
print "<div class='mn-form-col'><label class='mn-label'>Owner</label><select class='mn-select' id='perm-owner'>";
foreach my $u (@sys_users) {
    my $sel = ($u eq $cur_owner) ? " selected" : "";
    print "<option$sel>$u</option>";
}
print "</select></div>";

print "<div class='mn-form-col'><label class='mn-label'>Group</label><select class='mn-select' id='perm-group'>";
foreach my $g (@sys_groups) {
    my $sel = ($g eq $cur_group) ? " selected" : "";
    print "<option$sel>$g</option>";
}
print "</select></div>";

print "<div class='mn-form-col'><label class='mn-label'>Mode</label>";
print "<input type='text' id='perm-mode-display' class='mn-input' style='font-family:monospace; letter-spacing:3px;' maxlength='4' value='$cur_mode' readonly>";
print "</div></div>";

# Checkbox-Matrix
print "<table style='width:100%; border-collapse:collapse; margin:16px 0; font-size:15px;'>";
print "<tr>";
print "<th style='text-align:left; color:var(--mn-muted); font-weight:400; padding:6px 0; width:100px;'></th>";
print "<th style='text-align:center; color:var(--mn-muted); font-weight:400; padding:6px 20px;'>Owner</th>";
print "<th style='text-align:center; color:var(--mn-muted); font-weight:400; padding:6px 20px;'>Group</th>";
print "<th style='text-align:center; color:var(--mn-muted); font-weight:400; padding:6px 20px;'>Others</th>";
print "</tr>";

foreach my $row (['Read','r'], ['Write','w'], ['Execute','x']) {
    print "<tr>";
    print "<td style='padding:10px 0; color:var(--mn-text);'>$row->[0]</td>";
    foreach my $who (qw(u g o)) {
        print "<td style='text-align:center;'>";
        print "<input type='checkbox' id='perm-$who-$row->[1]' onchange='MnPerm.updateModeField()'";
        print " style='width:18px; height:18px; accent-color:var(--mn-accent); cursor:pointer;'>";
        print "</td>";
    }
    print "</tr>";
}
print "</table>";

# Status + Buttons
print "<div style='display:flex; align-items:center; gap:10px; margin-top:4px;'>";
print "<button class='mn-btn mn-btn-primary' onclick='mnApplyAndRedirect()'><i class='ti ti-check'></i> Apply</button>";
print "<a href='index.cgi' class='mn-btn'><i class='ti ti-x'></i> Cancel</a>";
print "<span id='perm-status' style='font-size:13px; color:var(--mn-muted);'></span>";
print "</div>";
print "</div>";

# Hidden field mit Section für JS
print "<input type='hidden' id='perm-section-name' value='$sec'>";

print "<script>
// Section setzen + Checkboxen aus aktuellem Mode vorbelegen
MnPerm.section = document.getElementById('perm-section-name').value;
MnPerm.fromMode('$cur_mode');

function mnApplyAndRedirect() {
  MnPerm.apply(function() {
    setTimeout(function() {
      // Webmin-konformer Redirect: top.location statt window.location
      // damit der äussere Webmin-Frame neu lädt und die Sidebar erhalten bleibt
      if (window.top && window.top !== window) {
        window.top.location.href = window.location.href.replace('edit_permissions.cgi', 'index.cgi').replace(/\?.*$/, '');
      } else {
        window.location.href = 'index.cgi';
      }
    }, 800);
  });
}
</script>";

print "</div>";
&WebminCore::ui_print_footer("index.cgi", "Back to Dashboard");

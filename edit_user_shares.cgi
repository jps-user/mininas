#!/usr/bin/perl
package main;
BEGIN { push(@INC, ".."); };
use WebminCore;
&init_config();
&ReadParse();
require 'mininas/mininas-lib.pl';
require 'mininas/ui_components.pl';

my $u = $in{'user'};
if (!$u) { &WebminCore::error("No user specified."); }

&WebminCore::ui_print_header(undef, "Edit Share Permissions", "", undef, 0, 0);
print mn_head();
print "<div class='mn-wrap'>";
print "<div class='mn-page-header'><a class='mn-page-back' href='index.cgi'><i class='ti ti-arrow-left'></i> Dashboard</a><span class='mn-page-title'>Share permissions: $u</span></div>";

my ($lines_ref, $sections_ref) = parse_smb_sections_v2();

print "<div class='mn-section'>";
print "<div class='mn-section-head'><i class='ti ti-share' style='font-size:12px;'></i> Manage access for <b>$u</b></div>";
print "<form action='save_user_shares.cgi' method='post'>";
print &WebminCore::ui_hidden("user", $u);
print "<table class='mn-table'>";
print "<tr><th style='width:40px; text-align:center;'>Access</th><th>Share</th><th>Path</th><th>Permission</th></tr>";

foreach my $s (@$sections_ref) {
    next if $s->{name} eq "global";
    my $path = ($s->{raw} =~ /path\s*=\s*(.*)/i) ? $1 : "—";
    $path =~ s/^\s+|\s+$//g;
    my $has_rw = ($s->{raw} =~ /valid users\s*=\s*\b\Q$u\E\b/i) ? 1 : 0;
    my $has_ro = ($s->{raw} =~ /read list\s*=\s*\b\Q$u\E\b/i)   ? 1 : 0;
    my $checked = ($has_rw || $has_ro) ? 'checked' : '';
    my $mode    = $has_ro ? 'ro' : 'rw';

    print "<tr><td style='text-align:center;'>";
    print "<input type='checkbox' name='share_active_$s->{name}' value='1' $checked style='accent-color:var(--mn-accent); transform:scale(1.2);'>";
    print "</td><td><b>$s->{name}</b></td>";
    print "<td class='mn-mono'>$path</td>";
    print "<td><div style='display:flex; gap:16px;'>";
    my $rw_c = ($mode eq 'rw') ? 'checked' : '';
    my $ro_c = ($mode eq 'ro') ? 'checked' : '';
    print "<label style='display:flex; align-items:center; gap:6px; font-size:12px; cursor:pointer;'><input type='radio' name='perm_mode_$s->{name}' value='rw' $rw_c style='accent-color:var(--mn-green);'> <span style='color:var(--mn-green);'>Read/Write</span></label>";
    print "<label style='display:flex; align-items:center; gap:6px; font-size:12px; cursor:pointer;'><input type='radio' name='perm_mode_$s->{name}' value='ro' $ro_c style='accent-color:var(--mn-amber);'> <span style='color:var(--mn-amber);'>Read-only</span></label>";
    print "</div></td></tr>";
}
print "</table>";
print "<div style='padding:12px; display:flex; gap:10px;'>";
print "<button type='submit' name='save' class='mn-btn mn-btn-primary'><i class='ti ti-device-floppy'></i> Save permissions</button>";
print "<a href='index.cgi' class='mn-btn'><i class='ti ti-x'></i> Cancel</a>";
print "</div>";
print "</form></div></div>";
&WebminCore::ui_print_footer("index.cgi", "Back to Dashboard");

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

&WebminCore::ui_print_header(undef, "Delete User", "", undef, 0, 0);
print mn_head();
print "<div class='mn-wrap'>";
print "<div class='mn-page-header'><a class='mn-page-back' href='index.cgi'><i class='ti ti-arrow-left'></i> Dashboard</a><span class='mn-page-title'>Delete user: ".&WebminCore::html_escape($u)."</span></div>";

my ($lines_ref, $sections_ref) = parse_smb_sections_v2();
my @affected;
foreach my $s (@$sections_ref) {
    next if $s->{name} eq "global";
    push(@affected, $s->{name}) if $s->{raw} =~ /(valid users|read list)\s*=\s*\b\Q$u\E\b/i;
}
my $shares_str = @affected ? join(", ", @affected) : "none";

print "<div class='mn-form-wrap' style='max-width:600px;'>";
print "<div class='mn-form-title' style='color:var(--mn-red);'><i class='ti ti-alert-triangle' style='margin-right:6px;'></i>Delete user <b>".&WebminCore::html_escape($u)."</b>?</div>";
print "<p style='color:var(--mn-muted); font-size:12px; margin-bottom:16px;'>Currently assigned to: <b>$shares_str</b></p>";

print "<form action='delete_user_exec.cgi' method='post'>";
print &WebminCore::ui_hidden("user", $u);

print "<label class='mn-del-card'><input type='radio' name='delete_mode' value='config_only' checked>";
print "<div class='mn-del-card-title'><i class='ti ti-shield' style='color:var(--mn-accent); margin-right:6px;'></i>Remove from shares only</div>";
print "<div class='mn-del-card-desc'>Removes user from all Samba shares. Linux system user and home directory are kept.</div></label>";

print "<label class='mn-del-card'><input type='radio' name='delete_mode' value='full_cleanup'>";
print "<div class='mn-del-card-title'><i class='ti ti-trash' style='color:var(--mn-red); margin-right:6px;'></i>Full cleanup (destructive)</div>";
print "<div class='mn-del-card-desc'>Removes from all shares AND permanently deletes the Linux/Samba system user.</div></label>";

print "<div style='display:flex; gap:10px; margin-top:16px;'>";
print "<button type='submit' class='mn-btn mn-btn-danger'><i class='ti ti-trash'></i> Yes, process deletion</button>";
print "<a href='index.cgi' class='mn-btn'><i class='ti ti-x'></i> Cancel</a>";
print "</div></form></div></div>";
&WebminCore::ui_print_footer("index.cgi", "Back to Dashboard");

#!/usr/bin/perl
package main;
use strict;
use warnings;
BEGIN { push(@INC, ".."); }
use WebminCore;
require 'mininas/mininas-init.pl';

my $u = $in{'user'};
if (!$u) { &WebminCore::error("No user specified."); }

&WebminCore::ui_print_header(undef, "Delete User", "", undef, 0, 0);
print mn_head();
print "<div class='mn-wrap'>";
print mn_page_header("Delete user: ".&WebminCore::html_escape($u));

my ($lines_ref, $sections_ref) = parse_smb_sections_v2();
my @affected;
foreach my $s (@$sections_ref) {
    next if $s->{name} eq "global";
    my ($rw_ref, $ro_ref) = mn_get_share_users($s);
    push(@affected, $s->{name}) if grep { $_ eq $u } (@$rw_ref, @$ro_ref);
}
my $shares_str = @affected ? join(", ", @affected) : "none";

print "<div class='mn-form-wrap' style='max-width:600px;'>";
print mn_form_title("Delete user <b>".&WebminCore::html_escape($u)."</b>?", icon => 'alert-triangle', color => 'var(--mn-red)');
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

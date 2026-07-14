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
if ($u !~ /^[a-zA-Z_][a-zA-Z0-9_-]*$/) { &WebminCore::error("Invalid username format."); }

if ($in{'new_password'}) {
    my ($pw,$pw2) = ($in{'new_password'},$in{'confirm_password'});
    &WebminCore::error("Passwords do not match.") if $pw ne $pw2;
    &WebminCore::error("Password must be at least 6 characters.") if length($pw) < 6;
    if (open(my $smb, "|-", "smbpasswd", "-s", $u)) {
        print $smb "$pw\n$pw\n"; close($smb);
        &WebminCore::error("smbpasswd failed. Does the Samba user exist?") if $? != 0;
    }
    write_mininas_log("PASSWD_CHANGE", "Password changed for user $u.");
    &WebminCore::redirect("index.cgi"); exit;
}

&WebminCore::ui_print_header(undef, "Change Password", "", undef, 0, 0);
print mn_head();
print "<div class='mn-wrap'>";
print "<div class='mn-page-header'><a class='mn-page-back' href='index.cgi'><i class='ti ti-arrow-left'></i> Dashboard</a><span class='mn-page-title'>Change password: $u</span></div>";
print "<div class='mn-form-wrap' style='max-width:500px;'>";
print "<div class='mn-form-title'><i class='ti ti-key' style='margin-right:6px; color:var(--mn-muted);'></i>Change Samba password for <b>$u</b></div>";
print "<p class='mn-hint' style='margin-bottom:16px;'>Only the Samba password is changed. The Linux system user password is not affected.</p>";
print "<form action='change_password.cgi' method='post'>";
print &WebminCore::ui_hidden("user", $u);
print "<div class='mn-form-row'>";
print "<div class='mn-form-col'><label class='mn-label'>New password</label><input class='mn-input' type='password' name='new_password' required></div>";
print "<div class='mn-form-col'><label class='mn-label'>Confirm password</label><input class='mn-input' type='password' name='confirm_password' required></div>";
print "</div>";
print "<div style='display:flex; gap:10px; margin-top:4px;'>";
print "<button type='submit' class='mn-btn mn-btn-primary'><i class='ti ti-check'></i> Set new password</button>";
print "<a href='index.cgi' class='mn-btn'><i class='ti ti-x'></i> Cancel</a>";
print "</div></form></div></div>";
&WebminCore::ui_print_footer("index.cgi", "Back to Dashboard");

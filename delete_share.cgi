#!/usr/bin/perl
package main;
use strict;
use warnings;
BEGIN { push(@INC, ".."); }
use WebminCore;
require 'mininas/mininas-init.pl';

my $sec_name = $in{'section'};
if (!$sec_name) { &WebminCore::error("Missing section name."); }

&WebminCore::ui_print_header(undef, "Delete Share", "", undef, 0, 0);
print mn_head();
print "<div class='mn-wrap'>";
print mn_page_header("Delete share: ".&WebminCore::html_escape($sec_name));

print "<div class='mn-form-wrap' style='max-width:600px;'>";
print mn_form_title("Are you sure you want to delete <b>[".&WebminCore::html_escape($sec_name)."]</b>?", icon => 'alert-triangle', color => 'var(--mn-red)');
print "<p style='color:var(--mn-muted); font-size:12px; margin-bottom:16px;'>Choose a deletion mode:</p>";

print "<form action='confirm_delete.cgi' method='post'>";
print &WebminCore::ui_hidden("section", $sec_name);

print "<label class='mn-del-card'><input type='radio' name='delete_mode' value='share_only' checked>";
print "<div class='mn-del-card-title'><i class='ti ti-shield' style='color:var(--mn-accent); margin-right:6px;'></i>Remove config only</div>";
print "<div class='mn-del-card-desc'>Keeps all files and the Linux user untouched. Only removes the share from smb.conf.</div></label>";

print "<label class='mn-del-card'><input type='radio' name='delete_mode' value='full_cleanup'>";
print "<div class='mn-del-card-title'><i class='ti ti-trash' style='color:var(--mn-red); margin-right:6px;'></i>Full cleanup (destructive)</div>";
print "<div class='mn-del-card-desc'>Removes config, Linux system user, and permanently wipes the directory.</div></label>";

print "<div style='display:flex; gap:10px; margin-top:16px;'>";
print "<button type='submit' name='confirm' class='mn-btn mn-btn-danger'><i class='ti ti-trash'></i> Yes, delete now</button>";
print "<a href='index.cgi' class='mn-btn'><i class='ti ti-x'></i> Cancel</a>";
print "</div></form></div></div>";
&WebminCore::ui_print_footer("index.cgi", "Back to Dashboard");

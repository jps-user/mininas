#!/usr/bin/perl
package main;
BEGIN { push(@INC, ".."); };
use WebminCore;
&init_config();
&ReadParse();
require 'mininas/mininas-lib.pl';
require 'mininas/ui_components.pl';

my $sec_name = $in{'section'};
if (!$sec_name) { &WebminCore::error("Missing section name."); }

&WebminCore::ui_print_header(undef, "Delete Share", "", undef, 0, 0);
print mn_head();
print "<div class='mn-wrap'>";
print "<div class='mn-page-header'><a class='mn-page-back' href='index.cgi'><i class='ti ti-arrow-left'></i> Dashboard</a><span class='mn-page-title'>Delete share: $sec_name</span></div>";

print "<div class='mn-form-wrap' style='max-width:600px;'>";
print "<div class='mn-form-title' style='color:var(--mn-red);'><i class='ti ti-alert-triangle' style='margin-right:6px;'></i>Are you sure you want to delete <b>[$sec_name]</b>?</div>";
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

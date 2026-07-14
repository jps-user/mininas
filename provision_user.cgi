#!/usr/bin/perl
# provision_user.cgi - Neuen User anlegen (isolierter Share oder bestehender Share).
# Aufgerufen von den Dashboard Quick Actions "New share" und "New user",
# jeweils mit ?mode=isolated bzw. ?mode=group um die passende Karte vorzuwählen.

package main;
BEGIN { push(@INC, '..') }
use WebminCore;
&init_config();
&ReadParse();
require 'mininas/mininas-lib.pl';
require 'mininas/ui_components.pl';

my ($lines_ref, $sections_ref) = parse_smb_sections_v2();
my @share_names = map { $_->{name} } grep { $_->{name} ne 'global' } @$sections_ref;

my $preselect = ($in{'mode'} eq 'group') ? 'group' : 'isolated';

&WebminCore::ui_print_header(undef, 'New User', '', undef, 0, 0);
print mn_head();
print "<div class='mn-wrap'>";
print "<div class='mn-page-header'>";
print "<a class='mn-page-back' href='index.cgi'><i class='ti ti-arrow-left'></i> Dashboard</a>";
print "<span class='mn-page-title'>New User &amp; Provisioning</span>";
print "</div>";

print "<div class='mn-form-wrap'>";
print "<form action='create_user.cgi' method='post'>";

print "<div class='mn-form-row'>";
print "<div class='mn-form-col'><label class='mn-label'>Username</label><input class='mn-input' type='text' name='username' required placeholder='lowercase, no spaces' autofocus></div>";
print "<div class='mn-form-col'><label class='mn-label'>Password</label><input class='mn-input' type='password' name='password' required></div>";
print "</div>";

print "<div class='mn-check-row'>";
print "<label class='mn-check-label'><input type='checkbox' name='create_home' value='1'> Create home directory (/home/username)</label>";
print "</div>";

print "<div class='mn-form-row'>";

my $isolated_checked = ($preselect eq 'isolated') ? 'checked' : '';
my $group_checked    = ($preselect eq 'group')    ? 'checked' : '';

print "<div class='mn-form-col'>";
print "<input type='radio' name='creation_mode' value='isolated' id='mode_a' $isolated_checked class='mn-card-radio'>";
print "<label for='mode_a' class='mn-card-label'>";
print "<div class='mn-card-title'><i class='ti ti-folder-plus' style='color:var(--mn-green); margin-right:6px;'></i>Isolated personal share</div>";
print "<div class='mn-card-desc' style='margin-bottom:12px;'>Creates a new directory and exclusive Samba share for this user.</div>";
print "<label class='mn-label'>Base path</label><select class='mn-select' name='base_path' style='margin-bottom:8px;'><option value='/mnt'>/mnt/</option><option value='/srv'>/srv/</option></select>";
print "<label class='mn-label'>Folder name</label><input class='mn-input' type='text' name='folder_name' placeholder='leave blank = username' style='margin-bottom:8px;'>";
print "<label class='mn-label'>Share type</label><select class='mn-select' name='share_type'><option value='standard'>Standard Samba share</option><option value='timemachine'>TimeMachine backup target</option></select>";
print "</label></div>";

print "<div class='mn-form-col'>";
print "<input type='radio' name='creation_mode' value='group' id='mode_b' $group_checked class='mn-card-radio'>";
print "<label for='mode_b' class='mn-card-label'>";
print "<div class='mn-card-title'><i class='ti ti-users' style='color:var(--mn-accent); margin-right:6px;'></i>Add to existing share</div>";
print "<div class='mn-card-desc' style='margin-bottom:12px;'>Creates the system user and adds them to an existing share.</div>";
print "<label class='mn-label'>Target share</label><select class='mn-select' name='target_group_share' style='margin-bottom:8px;'>";
foreach my $sn (@share_names) { print "<option value='$sn'>$sn</option>"; }
print "</select>";
print "<label class='mn-label'>Access level</label><select class='mn-select' name='group_perms'><option value='rw'>Read/Write</option><option value='ro'>Read-only</option></select>";
print "</label></div>";

print "</div>"; # form-row

print "<div style='display:flex; gap:10px; margin-top:4px;'>";
print "<button type='submit' class='mn-btn mn-btn-primary'><i class='ti ti-check'></i> Create user</button>";
print "<a href='index.cgi' class='mn-btn'><i class='ti ti-x'></i> Cancel</a>";
print "</div>";

print "</form></div>";
print "</div>";
&WebminCore::ui_print_footer('index.cgi', 'Back to Dashboard');

#!/usr/bin/perl
package main;
BEGIN { push(@INC, ".."); };
use WebminCore;
&init_config();
require 'mininas/mininas-lib.pl';
require 'mininas/ui_components.pl';

&WebminCore::ui_print_header(undef, "MiniNAS", "", undef, 0, 0);
print mn_head();
print "<div class='mn-wrap'>";

# ── Daten sammeln ────────────────────────────────────────────────
my $smbd_active = `systemctl is-active smbd 2>/dev/null`; chomp $smbd_active;
my $nmbd_active = `systemctl is-active nmbd 2>/dev/null`; chomp $nmbd_active;
my $smbd_ok = ($smbd_active eq 'active');
my $nmbd_ok = ($nmbd_active eq 'active');

# /proc/mounts
my %mounted;
if (open(my $mf, '<', '/proc/mounts')) {
    while (<$mf>) { my (undef, $mp) = split(' '); $mounted{$mp} = 1; }
    close($mf);
}

my ($lines_ref, $sections_ref) = parse_smb_sections_v2();

# Share-Status (HDD-neutral: stat() + /proc/mounts)
my @share_status;
foreach my $s (@$sections_ref) {
    next if $s->{name} eq 'global';
    my ($path) = ($s->{raw} =~ /path\s*=\s*([^\n]+)/i);
    $path =~ s/^\s+|\s+$//g if $path;
    next unless $path;
    my $dir_ok     = (-d $path) ? 1 : 0;
    my $is_mounted = 0;
    if ($mounted{$path}) { $is_mounted = 1; }
    else {
        foreach my $mp (sort { length($b) <=> length($a) } keys %mounted) {
            next if $mp eq '/';
            if (substr($path, 0, length($mp)) eq $mp) { $is_mounted = 1; last; }
        }
    }
    push @share_status, { name => $s->{name}, path => $path, dir_ok => $dir_ok, mounted => $is_mounted };
}

my %share_ok_lookup = map { $_->{name} => $_->{dir_ok} } @share_status;
my $shares_all_ok = !grep { !$_->{dir_ok} } @share_status;
my $global_ok     = ($smbd_ok && $nmbd_ok && $shares_all_ok);

# Users zählen
my %users;
if (open(my $pw, '<', '/etc/passwd')) {
    while (<$pw>) { my ($u, undef, $uid) = split(':'); $users{$u} = $uid if $uid >= 1000 && $uid < 65534; }
    close($pw);
}
my $share_count = scalar(grep { $_->{name} ne 'global' } @$sections_ref);
my $user_count  = scalar(keys %users);
my $tm_count    = scalar(grep { $_->{raw} =~ /fruit:time machine\s*=\s*yes/i } @$sections_ref);

my @share_names = map { $_->{name} } grep { $_->{name} ne 'global' } @$sections_ref;

# ── Kacheln: Samba Status (+ Reload) und Shares (+ Global Settings) ──
print "<div class='mn-tiles'>";

my $status_color = $global_ok ? 'var(--mn-green)' : 'var(--mn-red)';
my $status_label = $global_ok ? 'Active' : 'Issues';
print "<div class='mn-tile'>";
print "<div class='mn-tile-label'><i class='ti ti-server'></i> Samba status</div>";
print "<div class='mn-tile-val' style='color:$status_color;'>$status_label</div>";
print "<a class='mn-tile-action' href='reload_samba.cgi'><i class='ti ti-refresh'></i> Reload Samba</a>";
print "</div>";

print "<div class='mn-tile'>";
print "<div class='mn-tile-label'><i class='ti ti-folder'></i> Shares</div>";
print "<div class='mn-tile-val'>$share_count</div>";
print "<a class='mn-tile-action' href='edit_section.cgi?section=global'><i class='ti ti-settings'></i> Global Settings</a>";
print "</div>";

print "<div class='mn-tile'>";
print "<div class='mn-tile-label'><i class='ti ti-users'></i> Users</div>";
print "<div class='mn-tile-val'>$user_count</div>";
print "<div class='mn-tile-sub'>local system users</div>";
print "</div>";

print "</div>"; # mn-tiles

# ── Quick Actions (direkt unter den Kacheln) ──────────────────────
print "<div class='mn-section'>";
print "<div class='mn-section-head'><i class='ti ti-bolt' style='font-size:13px;'></i> Quick actions</div>";
print "<div style='padding:12px;'><div class='mn-qa-grid'>";
print "<button type='button' class='mn-qa-btn' onclick=\"mnTogglePanel('panel-newshare')\"><div class='mn-qa-icon qa-green'><i class='ti ti-folder-plus'></i></div><div><div class='mn-qa-label'>New share</div><div class='mn-qa-sub'>Create + provision</div></div></button>";
print "<button type='button' class='mn-qa-btn' onclick=\"mnTogglePanel('panel-newuser')\"><div class='mn-qa-icon qa-blue'><i class='ti ti-user-plus'></i></div><div><div class='mn-qa-label'>New user</div><div class='mn-qa-sub'>OS + Samba</div></div></button>";
print "<button type='button' class='mn-qa-btn' id='testparm-btn' onclick='mnRunTestparm()'><div class='mn-qa-icon qa-amber' id='testparm-icon'><i class='ti ti-file-check'></i></div><div><div class='mn-qa-label'>Test config</div><div class='mn-qa-sub' id='testparm-result'>Run testparm</div></div></button>";
print "</div></div></div>";

# ── Shares-Tabelle (volle Breite) ────────────────────────────────
print "<div class='mn-section'>";
print "<div class='mn-section-head'><i class='ti ti-folder' style='font-size:13px;'></i> Shares</div>";
print "<div class='mn-table-wrap'>";
print "<table class='mn-table' id='shares-table'>";
print "<tr><th>Share</th><th>Owner</th><th>Permissions</th><th>Actions</th></tr>";

foreach my $s (@$sections_ref) {
    next if $s->{name} eq 'global';
    my ($path) = ($s->{raw} =~ /path\s*=\s*([^\n]+)/i);
    $path =~ s/^\s+|\s+$//g if $path; $path ||= "—";
    my $owner = "—";
    if ($s->{raw} =~ /valid users\s*=\s*([^\n]+)/i) {
        my @t = split(/[\s,]+/, $1); $owner = shift(@t)||"—"; $owner =~ s/^\s+|\s+$//g;
    }
    my $is_tm = ($s->{raw} =~ /fruit:time machine\s*=\s*yes/i);
    my ($perm_str, $perm_owner) = ("—","—");
    if ($path ne "—" && -d $path) {
        my @st = stat($path);
        if (@st) {
            $perm_str   = sprintf("%04o", $st[2] & 07777);
            $perm_owner = ((getpwuid($st[4]))[0]||$st[4]).":".((getgrgid($st[5]))[0]||$st[5]);
        }
    } elsif ($path ne "—") { $perm_str = "missing"; }

    # Share-Name einfärben wenn der Pfad fehlt (Attention)
    my $share_ok = $share_ok_lookup{$s->{name}};
    my $name_style = $share_ok ? "" : " style='color:var(--mn-red);'";

    my $edit_url = "edit_section.cgi?section=".&WebminCore::urlize($s->{name});
    my $del_url  = "delete_share.cgi?section=".&WebminCore::urlize($s->{name});

    my $perm_url = "edit_permissions.cgi?section=".&WebminCore::urlize($s->{name});
    print "<tr data-section='$s->{name}'>";
    print "<td><span class='mn-share-name'$name_style>$s->{name}</span><span class='mn-share-path'>$path</span></td>";
    print "<td>$owner</td>";
    print "<td class='mn-perm-cell'>$perm_str $perm_owner</td>";
    print "<td style='text-align:center; white-space:nowrap;'>";
    print "<a class='mn-icon-btn' href='$edit_url' title='Edit share'><i class='ti ti-edit'></i></a>";
    print "<a class='mn-icon-btn' href='$perm_url' title='Change permissions'><i class='ti ti-folder-cog'></i></a>";
    print "<a class='mn-icon-btn mn-icon-btn-del' href='$del_url' title='Delete share'><i class='ti ti-trash'></i></a>";
    print "</td></tr>";
}
print "</table>";
print "</div>"; # mn-table-wrap

# Permission-Panel Container (versteckt, wird pro Share befüllt)
print "<div id='perm-panel' style='display:none; border-top:1px solid var(--mn-border);'>";
print "<div style='padding:18px 20px;'>";
print "<div style='display:flex; align-items:center; justify-content:space-between; margin-bottom:14px;'>";
print "<span style='font-weight:500; font-size:15px;'><i class='ti ti-shield' style='margin-right:7px; color:var(--mn-muted);'></i><span id='perm-panel-title'>Permissions</span></span>";
print "<button onclick=\"document.getElementById('perm-panel').style.display='none'\" style='background:none; border:none; color:var(--mn-muted); cursor:pointer; font-size:18px;'><i class='ti ti-x'></i></button>";
print "</div>";

# Owner + Group Dropdowns
print "<div style='display:flex; gap:16px; margin-bottom:16px;'>";
print "<div style='flex:1;'><label class='mn-label'>Owner</label><select class='mn-select' id='perm-owner'></select></div>";
print "<div style='flex:1;'><label class='mn-label'>Group</label><select class='mn-select' id='perm-group'></select></div>";
print "<div style='flex:1;'>";
print "<label class='mn-label'>Mode</label>";
print "<input type='text' id='perm-mode-display' class='mn-input' style='font-family:monospace; letter-spacing:2px;' maxlength='4' placeholder='0770' readonly>";
print "</div>";
print "</div>";

# Checkbox-Matrix
print "<table style='width:100%; border-collapse:collapse; margin-bottom:16px; font-size:14px;'>";
print "<tr><th style='text-align:left; color:var(--mn-muted); font-weight:400; padding:4px 0; width:90px;'></th>";
print "<th style='text-align:center; color:var(--mn-muted); font-weight:400; padding:4px 12px;'>Owner</th>";
print "<th style='text-align:center; color:var(--mn-muted); font-weight:400; padding:4px 12px;'>Group</th>";
print "<th style='text-align:center; color:var(--mn-muted); font-weight:400; padding:4px 12px;'>Others</th></tr>";

foreach my $bit (['Read','r',4], ['Write','w',2], ['Execute','x',1]) {
    print "<tr>";
    print "<td style='padding:6px 0; color:var(--mn-text);'>$bit->[0]</td>";
    foreach my $who (qw(u g o)) {
        print "<td style='text-align:center;'>";
        print "<input type='checkbox' id='perm-$who-$bit->[1]' onchange='mnModeFromCheckboxes()'";
        print " style='width:16px; height:16px; accent-color:var(--mn-accent); cursor:pointer;'>";
        print "</td>";
    }
    print "</tr>";
}

print "</table>";

# Status + Buttons
print "<div style='display:flex; align-items:center; gap:10px;'>";
print "<button class='mn-btn mn-btn-primary' onclick='mnApplyPerms()'><i class='ti ti-check'></i> Apply</button>";
print "<button class='mn-btn' onclick=\"document.getElementById('perm-panel').style.display='none'\"><i class='ti ti-x'></i> Cancel</button>";
print "<span id='perm-status' style='font-size:13px; color:var(--mn-muted);'></span>";
print "</div>";
print "</div></div>";

print "</div>"; # mn-section

# ── Users Tabelle ────────────────────────────────────────────────
print "<div class='mn-section'>";
print "<div class='mn-section-head'><i class='ti ti-users' style='font-size:13px;'></i> System & Samba users</div>";
print "<div class='mn-table-wrap'>";
print "<table class='mn-table'>";
print "<tr><th>Username</th><th>UID</th><th>Assigned shares</th><th>Actions</th></tr>";

foreach my $s (@$sections_ref) {
    my @finds = ($s->{raw} =~ /(?:valid users|read list)\s*=\s*([^\n]+)/gi);
    foreach my $line (@finds) {
        foreach my $u (split(/[\s,]+/, $line)) {
            $u =~ s/^\s+|\s+$//g;
            if ($u && $u !~ /^@/) { $users{$u} ||= "Ghost"; }
        }
    }
}

foreach my $u (sort keys %users) {
    my $uid = $users{$u};
    my @assigned;
    foreach my $s (@$sections_ref) {
        push(@assigned, $s->{name}) if $s->{raw} =~ /(?:valid users|read list)\s*=\s*[^\n]*\b\Q$u\E\b/i;
    }
    my $shares_str = @assigned ? join(", ", @assigned) : "<span style='color:var(--mn-muted); font-style:italic;'>None</span>";
    print "<tr>";
    if ($uid eq "Ghost") {
        print "<td><b style='color:var(--mn-red);'>$u</b></td><td style='color:var(--mn-red); font-size:13px;'>Missing in OS</td><td>$shares_str</td>";
        print "<td style='text-align:center;'><a class='mn-icon-btn mn-icon-btn-del' href='cleanup_ghost_user.cgi?user=".&WebminCore::urlize($u)."' title='Clean from config'><i class='ti ti-ghost'></i></a></td>";
    } else {
        print "<td><b>$u</b></td><td class='mn-mono'>$uid</td><td>$shares_str</td>";
        print "<td style='text-align:center; white-space:nowrap;'>";
        print "<a class='mn-icon-btn' href='change_password.cgi?user=".&WebminCore::urlize($u)."' title='Change password'><i class='ti ti-key'></i></a>";
        print "<a class='mn-icon-btn' href='edit_user_shares.cgi?user=".&WebminCore::urlize($u)."' title='Edit shares'><i class='ti ti-share'></i></a>";
        print "<a class='mn-icon-btn mn-icon-btn-del' href='delete_user_form.cgi?user=".&WebminCore::urlize($u)."' title='Delete user'><i class='ti ti-trash'></i></a>";
        print "</td>";
    }
    print "</tr>";
}
print "</table>";
print "</div>"; # mn-table-wrap
print "</div>"; # mn-section

# ── Quick Action Panels (versteckt, werden per JS eingeblendet) ──

# Panel: New User & Provisioning (zusammengefasst für "New share" und "New user")
print "<div id='panel-newshare' class='mn-panel' style='display:none;'>";
print "<div class='mn-section'>";
print "<div class='mn-section-head'><i class='ti ti-folder-plus' style='font-size:13px;'></i> New share &amp; user provisioning <button type='button' class='mn-panel-close' onclick=\"mnTogglePanel('panel-newshare')\"><i class='ti ti-x'></i></button></div>";
print "<div style='padding:16px;'>";
print &mn_provisioning_form(\@share_names, 'standard');
print "</div></div></div>";

print "<div id='panel-newuser' class='mn-panel' style='display:none;'>";
print "<div class='mn-section'>";
print "<div class='mn-section-head'><i class='ti ti-user-plus' style='font-size:13px;'></i> New user <button type='button' class='mn-panel-close' onclick=\"mnTogglePanel('panel-newuser')\"><i class='ti ti-x'></i></button></div>";
print "<div style='padding:16px;'>";
print &mn_provisioning_form(\@share_names, 'standard');
print "</div></div></div>";

# ui_widgets.js wird via mn_head() geladen - kein inline JS nötig

print "</div>"; # mn-wrap
&WebminCore::ui_print_footer("/", "Return to Webmin");

# ── Helper: Provisioning Formular bauen ──────────────────────────
sub mn_provisioning_form {
    my ($share_names_ref, $default_type) = @_;
    my $tm_selected  = ($default_type eq 'timemachine') ? 'selected' : '';
    my $std_selected = ($default_type eq 'standard')    ? 'selected' : '';

    my $html = "<form action='create_user.cgi' method='post'>";
    $html .= "<div class='mn-form-row'>";
    $html .= "<div class='mn-form-col'><label class='mn-label'>Username</label><input class='mn-input' type='text' name='username' required placeholder='lowercase, no spaces'></div>";
    $html .= "<div class='mn-form-col'><label class='mn-label'>Password</label><input class='mn-input' type='password' name='password' required></div>";
    $html .= "</div>";

    $html .= "<div class='mn-form-row'>";

    $html .= "<div class='mn-form-col'>";
    $html .= "<input type='radio' name='creation_mode' value='isolated' id='mode_a_$default_type' checked class='mn-card-radio'>";
    $html .= "<label for='mode_a_$default_type' class='mn-card-label'>";
    $html .= "<div class='mn-card-title'><i class='ti ti-folder-plus' style='color:var(--mn-green); margin-right:6px;'></i>Isolated personal share</div>";
    $html .= "<div class='mn-card-desc' style='margin-bottom:12px;'>Creates a new directory and exclusive Samba share for this user.</div>";
    $html .= "<label class='mn-label'>Base path</label><select class='mn-select' name='base_path' style='margin-bottom:8px;'><option value='/mnt'>/mnt/</option><option value='/srv'>/srv/</option></select>";
    $html .= "<label class='mn-label'>Folder name</label><input class='mn-input' type='text' name='folder_name' placeholder='leave blank = username' style='margin-bottom:8px;'>";
    $html .= "<label class='mn-label'>Share type</label><select class='mn-select' name='share_type'><option value='standard' $std_selected>Standard Samba share</option><option value='timemachine' $tm_selected>TimeMachine backup target</option></select>";
    $html .= "</label></div>";

    $html .= "<div class='mn-form-col'>";
    $html .= "<input type='radio' name='creation_mode' value='group' id='mode_b_$default_type' class='mn-card-radio'>";
    $html .= "<label for='mode_b_$default_type' class='mn-card-label'>";
    $html .= "<div class='mn-card-title'><i class='ti ti-users' style='color:var(--mn-accent); margin-right:6px;'></i>Add to existing share</div>";
    $html .= "<div class='mn-card-desc' style='margin-bottom:12px;'>Creates the system user and adds them to an existing share.</div>";
    $html .= "<label class='mn-label'>Target share</label><select class='mn-select' name='target_group_share' style='margin-bottom:8px;'>";
    foreach my $sn (@$share_names_ref) { $html .= "<option value='$sn'>$sn</option>"; }
    $html .= "</select>";
    $html .= "<label class='mn-label'>Access level</label><select class='mn-select' name='group_perms'><option value='rw'>Read/Write</option><option value='ro'>Read-only</option></select>";
    $html .= "</label></div>";

    $html .= "</div>"; # form-row
    $html .= "<button type='submit' class='mn-btn mn-btn-primary' style='margin-top:4px;'><i class='ti ti-check'></i> Create user</button>";
    $html .= "</form>";
    return $html;
}

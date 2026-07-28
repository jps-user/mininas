#!/usr/bin/perl
package main;
use strict;
use warnings;
BEGIN { push(@INC, ".."); }
use WebminCore;
require 'mininas/mininas-init.pl';

&WebminCore::ui_print_header(undef, "MiniNAS", "", undef, 0, 0);
print mn_head();
print "<div class='mn-wrap'>";

# ── Daten sammeln (Etappe 4b: ausgelagert in mininas-lib.pl) ──────
my $data             = mn_collect_dashboard_data();
my $sections_ref     = $data->{sections_ref};
my $share_ok_lookup  = $data->{share_ok_lookup};
my $global_ok        = $data->{global_ok};
my %users            = %{ $data->{users} };
my $disks_ref        = $data->{disks_ref};
my $cache            = $data->{cache};
my $cache_ts         = $data->{cache_ts};

# ── Hamburger-Button + Sidebar (rechts, immer geschlossen beim Laden) ──
print "<button type='button' class='mn-hamburger' onclick='mnSidebarOpen()' title='Menu'><i class='ti ti-menu-2'></i></button>";
print "<div class='mn-sidebar-overlay' id='mn-sidebar-overlay' onclick='mnSidebarClose()'></div>";
print "<div class='mn-sidebar' id='mn-sidebar'>";
print "<div class='mn-sidebar-head'><span>Actions</span><button class='mn-sidebar-close' onclick='mnSidebarClose()'><i class='ti ti-x'></i></button></div>";
print "<div class='mn-sidebar-body'>";
print "<a class='mn-sidebar-item' href='provision_user.cgi?mode=isolated'><i class='ti ti-folder-plus'></i> New share</a>";
print "<a class='mn-sidebar-item' href='provision_user.cgi?mode=group'><i class='ti ti-user-plus'></i> New user</a>";
print "<div class='mn-sidebar-sep'></div>";
print "<a class='mn-sidebar-item' href='reload_samba.cgi'><i class='ti ti-refresh'></i> Reload Samba</a>";
print "<a class='mn-sidebar-item' href='edit_section.cgi?section=global'><i class='ti ti-settings'></i> Global Settings</a>";
print "<button type='button' class='mn-sidebar-item' id='testparm-btn' onclick='mnRunTestparm()'><i class='ti ti-file-check' id='testparm-icon'></i> <span id='testparm-result'>Test config</span></button>";
print "<div class='mn-sidebar-sep'></div>";
print "<button type='button' class='mn-sidebar-item' id='wake-measure-btn' onclick='mnWakeAndMeasure()'><i class='ti ti-bolt'></i> <span id='wake-measure-status'>Wake &amp; measure disks</span></button>";
print "<a class='mn-sidebar-item' href='manage_disks.cgi'><i class='ti ti-adjustments'></i> Manage Disks</a>";
print "</div></div>";

# ── Kacheln: Samba Status + Disk-Kachel(n) ────────────────────────
print "<div class='mn-tiles'>";

my $status_color = $global_ok ? 'var(--mn-green)' : 'var(--mn-red)';
my $status_label = $global_ok ? 'Active' : 'Issues';
print "<div class='mn-tile'>";
print "<div class='mn-tile-label'><i class='ti ti-server'></i> Samba status</div>";
print "<div class='mn-tile-val' style='color:$status_color;'>$status_label</div>";
print "</div>";

# Disk-Kachel(n): bis 5 Disks je Kachel, aus disks.conf + Cache.
# Rendering-Funktion mn_render_disk_tile() lebt in ui_components.pl
# (Etappe 4b) - zeigt "Updated: <timestamp>" neben dem Label.
if (@$disks_ref) {
    my @first5 = @$disks_ref[0 .. (scalar(@$disks_ref) > 5 ? 4 : $#$disks_ref)];
    mn_render_disk_tile(\@first5, $cache, 'Disks', $cache_ts);
    if (scalar(@$disks_ref) > 5) {
        my @rest = @$disks_ref[5 .. $#$disks_ref];
        mn_render_disk_tile(\@rest, $cache, 'Disks (cont.)', $cache_ts);
    }
} else {
    print "<div class='mn-tile'>";
    print "<div class='mn-tile-label'><i class='ti ti-device-sd-card'></i> Disks</div>";
    print "<div class='mn-tile-sub'>No disks configured.</div>";
    print "</div>";
}

print "</div>"; # mn-tiles

# ── Shares-Tabelle (volle Breite) ────────────────────────────────
print "<div class='mn-section'>";
print "<div class='mn-section-head'><i class='ti ti-folder' style='font-size:13px;'></i> Shares</div>";
print "<div class='mn-table-wrap'>";
print "<table class='mn-table' id='shares-table'>";
print "<tr><th>Share</th><th>Owner</th><th>Permissions</th><th>Usage</th><th>Actions</th></tr>";

foreach my $s (@$sections_ref) {
    next if $s->{name} eq 'global';
    my $path = mn_get_share_path($s);
    $path ||= "—";
    my $owner = "—";
    my ($rw_ref, undef) = mn_get_share_users($s);
    if (@$rw_ref) { $owner = $rw_ref->[0]; }
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
    my $share_ok = $share_ok_lookup->{$s->{name}};
    my $name_style = $share_ok ? "" : " style='color:var(--mn-red);'";

    my $edit_url = "edit_section.cgi?section=".&WebminCore::urlize($s->{name});
    my $del_url  = "delete_share.cgi?section=".&WebminCore::urlize($s->{name});

    my $perm_url = "edit_permissions.cgi?section=".&WebminCore::urlize($s->{name});

    # Usage aus Cache lesen – nie live gemessen, nie Platten aufwecken.
    my $usage_raw = $cache->{shares}{$s->{name}};
    my $usage_str = (defined($usage_raw) && $usage_raw ne 'n/a') ? $usage_raw : "n/a";

    # Welche konfigurierte Disk liegt dieser Share-Pfad? Fällt auf "Local"
    # zurück wenn kein disks.conf-Eintrag passt (z.B. System-Rootfs).
    my $disk_label = ($path ne "—") ? mn_find_disk_for_path($path) : undef;
    my $disk_badge = defined($disk_label)
        ? "<span class='mn-disk-badge'><i class='ti ti-device-sd-card'></i> ".&WebminCore::html_escape($disk_label)."</span>"
        : "<span class='mn-disk-badge mn-disk-badge-local'><i class='ti ti-server-2'></i> Local</span>";

    print "<tr data-section='$s->{name}'>";
    print "<td><span class='mn-share-name'$name_style>$s->{name}</span> $disk_badge<span class='mn-share-path'>$path</span></td>";
    print "<td>$owner</td>";
    print "<td class='mn-perm-cell'>$perm_str $perm_owner</td>";
    print "<td class='mn-mono'>$usage_str</td>";
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
    my ($rw_ref, $ro_ref) = mn_get_share_users($s);
    foreach my $u (@$rw_ref, @$ro_ref) {
        $users{$u} ||= "Ghost" if $u !~ /^@/;
    }
}

foreach my $u (sort keys %users) {
    my $uid = $users{$u};
    my @assigned;
    foreach my $s (@$sections_ref) {
        my ($rw_ref, $ro_ref) = mn_get_share_users($s);
        push(@assigned, $s->{name}) if grep { $_ eq $u } (@$rw_ref, @$ro_ref);
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
        print "<a class='mn-icon-btn' href='manage_home.cgi?user=".&WebminCore::urlize($u)."' title='Home directory'><i class='ti ti-home'></i></a>";
        print "<a class='mn-icon-btn mn-icon-btn-del' href='delete_user_form.cgi?user=".&WebminCore::urlize($u)."' title='Delete user'><i class='ti ti-trash'></i></a>";
        print "</td>";
    }
    print "</tr>";
}
print "</table>";
print "</div>"; # mn-table-wrap
print "</div>"; # mn-section

print "</div>"; # mn-wrap
&WebminCore::ui_print_footer("/", "Return to Webmin");

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
my $smbd_ok = mn_service_active('smbd');
my $nmbd_ok = mn_service_active('nmbd');

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

# Storage-Cache laden für Disk-Kacheln + Share-Usage-Spalte.
# Option C: Beim Dashboard-Laden wird der Cache nur dann aktualisiert,
# wenn /proc/diskstats seit der letzten Messung bereits Aktivität zeigt
# (Disk ist dann ohnehin schon wach – kein zusätzliches Aufwecken).
my $disks_ref  = mn_read_disks_conf();
my $any_active = 0;
foreach my $d (@$disks_ref) {
    my $sleeping = mn_disk_is_sleeping($d->{dev});
    if (defined($sleeping) && $sleeping == 0) { $any_active = 1; last; }
}
mn_update_storage_cache() if $any_active;

my $cache    = mn_read_storage_cache();
my $cache_ts = $cache->{timestamp} || '';

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
# Zeigt "Updated: <timestamp>" neben dem Label statt in einer separaten Kachel.
sub mn_render_disk_tile {
    my ($disks_slice_ref, $cache_ref, $title, $ts) = @_;
    print "<div class='mn-tile'>";
    print "<div class='mn-tile-label' style='display:flex; justify-content:space-between; align-items:baseline;'>";
    print "<span><i class='ti ti-device-sd-card'></i> $title</span>";
    my $ts_display = $ts ? $ts : 'never';
    print "<span class='mn-disk-updated'>Updated: $ts_display</span>";
    print "</div>";
    foreach my $d (@$disks_slice_ref) {
        my $dev   = $d->{dev};
        my $label = $d->{label};
        my $info  = $cache_ref->{disks}{$dev};
        print "<div class='mn-disk-row'>";
        print "<span class='mn-disk-label' title='$label'>$label</span>";
        if ($info && defined($info->{total_gb}) && defined($info->{used_gb}) && $info->{total_gb} > 0) {
            my $pct = int(($info->{used_gb} / $info->{total_gb}) * 100 + 0.5);
            $pct = 100 if $pct > 100;
            my $bar_class = $pct >= 90 ? 'mn-progress-crit' : ($pct >= 75 ? 'mn-progress-warn' : '');
            print "<div class='mn-progress'><div class='mn-progress-bar $bar_class' style='width:${pct}%;'></div></div>";
            print "<span class='mn-disk-pct'>$pct%</span>";
        } else {
            print "<div class='mn-progress'><div class='mn-progress-bar' style='width:0%;'></div></div>";
            print "<span class='mn-disk-na'>n/a</span>";
        }
        my $sleeping = $info ? $info->{sleeping} : undef;
        if (defined($sleeping) && $sleeping == 1) {
            print "<span class='mn-disk-sleep' title='Sleeping - values may be outdated'><i class='ti ti-moon'></i></span>";
        }
        print "</div>";
    }
    print "</div>"; # mn-tile
}

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

    # Usage aus Cache lesen – nie live gemessen, nie Platten aufwecken.
    my $usage_raw = $cache->{shares}{$s->{name}};
    my $usage_str = (defined($usage_raw) && $usage_raw ne 'n/a') ? "$usage_raw GB" : "n/a";

    # Welche konfigurierte Disk liegt dieser Share-Pfad? Fällt auf "Local"
    # zurück wenn kein disks.conf-Eintrag passt (z.B. System-Rootfs).
    my $disk_label = ($path ne "—") ? mn_find_disk_for_path($path) : undef;
    my $disk_badge = defined($disk_label)
        ? "<span class='mn-disk-badge'><i class='ti ti-device-sd-card'></i> ".&WebminCore::html_escape($disk_label)."</span>"
        : "<span class='mn-disk-badge mn-disk-badge-local'><i class='ti ti-server-2'></i> Local</span>";

    print "<tr data-section='$s->{name}'>";
    print "<td><span class='mn-share-name'$name_style>$s->{name}</span><span class='mn-share-path'>$path</span> $disk_badge</td>";
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

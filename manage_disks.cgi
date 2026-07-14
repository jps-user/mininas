#!/usr/bin/perl
# manage_disks.cgi - Verwaltet /var/lib/mininas/disks.conf: Disks hinzufügen/entfernen,
# Labels vergeben. Zeigt LXC-Hinweis, da in Containern meist nur Mountpoints (kein
# rohes Blockgerät) sichtbar sind - siehe mn_is_lxc().
package main;
BEGIN { push(@INC, ".."); };
use WebminCore;
&init_config();
&ReadParse();
require 'mininas/mininas-lib.pl';
require 'mininas/ui_components.pl';

my $action = $in{'action'} || '';
my @errors;

# ── POST: Disk hinzufügen ─────────────────────────────────────────
if ($action eq 'add') {
    my $path  = $in{'new_path'};
    my $label = $in{'new_label'};
    $path  =~ s/^\s+|\s+$//g if $path;
    $label =~ s/^\s+|\s+$//g if $label;

    if (!$path) {
        push @errors, 'Please select or enter a device / mount path.';
    } elsif (!(-b $path || -d $path)) {
        push @errors, "Path '$path' is neither a block device nor an existing directory.";
    } elsif ($label !~ /^[a-zA-Z0-9_ -]{1,32}$/) {
        push @errors, 'Label must be 1-32 characters (letters, numbers, space, - and _ only).';
    } else {
        my $disks_ref = mn_read_disks_conf();
        if (grep { $_->{dev} eq $path } @$disks_ref) {
            push @errors, "'$path' is already configured.";
        } else {
            push @$disks_ref, { dev => $path, label => $label };
            if (mn_write_disks_conf($disks_ref)) {
                write_mininas_log('DISK_ADD', "Added disk '$path' as '$label'.");
                mn_update_storage_cache();
                &WebminCore::redirect('manage_disks.cgi');
                exit;
            } else {
                push @errors, 'Failed to write disks.conf.';
            }
        }
    }
}

# ── POST: Disk entfernen ──────────────────────────────────────────
if ($action eq 'remove') {
    my $path = $in{'path'};
    if ($path) {
        my $disks_ref = mn_read_disks_conf();
        my @kept = grep { $_->{dev} ne $path } @$disks_ref;
        if (mn_write_disks_conf(\@kept)) {
            write_mininas_log('DISK_REMOVE', "Removed disk '$path'.");
        }
    }
    &WebminCore::redirect('manage_disks.cgi');
    exit;
}

# ── POST: Label umbenennen ────────────────────────────────────────
if ($action eq 'relabel') {
    my $path  = $in{'path'};
    my $label = $in{'label'};
    $label =~ s/^\s+|\s+$//g if $label;
    if ($path && $label && $label =~ /^[a-zA-Z0-9_ -]{1,32}$/) {
        my $disks_ref = mn_read_disks_conf();
        foreach my $d (@$disks_ref) { $d->{label} = $label if $d->{dev} eq $path; }
        if (mn_write_disks_conf($disks_ref)) {
            write_mininas_log('DISK_RELABEL', "Relabeled '$path' to '$label'.");
        }
    }
    &WebminCore::redirect('manage_disks.cgi');
    exit;
}

# ── Anzeige ────────────────────────────────────────────────────────
&WebminCore::ui_print_header(undef, "Manage Disks", "", undef, 0, 0);
print mn_head();
print "<div class='mn-wrap'>";
print "<div class='mn-page-header'><a class='mn-page-back' href='index.cgi'><i class='ti ti-arrow-left'></i> Dashboard</a><span class='mn-page-title'>Manage Disks</span></div>";

if (@errors) {
    print "<div class='mn-form-wrap' style='border-color:var(--mn-red);'>";
    foreach my $e (@errors) {
        print "<div style='color:var(--mn-red); font-size:14px; margin-bottom:4px;'><i class='ti ti-alert-circle'></i> ".&WebminCore::html_escape($e)."</div>";
    }
    print "</div>";
}

my $is_lxc = mn_is_lxc();
if ($is_lxc) {
    print "<div class='mn-form-wrap' style='border-color:var(--mn-amber);'>";
    print "<div style='color:var(--mn-amber); font-size:14px; display:flex; gap:8px; align-items:flex-start;'>";
    print "<i class='ti ti-info-circle' style='flex-shrink:0; margin-top:2px;'></i>";
    print "<span>Running inside an LXC container. Raw block devices (<code>/dev/sdX</code>) are usually not visible here " .
          "unless explicitly passed through. Disks reached via a Proxmox mount point (<code>mp0</code>) appear as regular " .
          "directories instead &mdash; add the <b>mount path</b> (e.g. <code>/mnt/testusb</code>) rather than a device node in that case. " .
          "Sleep detection (hdparm) only works for real block devices; for mount-path disks the sleep state is always " .
          "reported as unknown, and usage is measured on every cache refresh since a directory read cannot wake a sleeping disk.</span>";
    print "</div></div>";
}

# ── Aktuell konfigurierte Disks ────────────────────────────────────
my $disks_ref = mn_read_disks_conf();
my $cache     = mn_read_storage_cache();

print "<div class='mn-section'>";
print "<div class='mn-section-head'><i class='ti ti-device-sd-card' style='font-size:13px;'></i> Configured disks</div>";
print "<div class='mn-table-wrap'>";
print "<table class='mn-table'>";
print "<tr><th>Path</th><th>Label</th><th>Type</th><th>Usage</th><th>Actions</th></tr>";

if (@$disks_ref) {
    foreach my $d (@$disks_ref) {
        my $dev   = $d->{dev};
        my $label = $d->{label};
        my $type  = (-b $dev) ? 'Block device' : ((-d $dev) ? 'Mount path' : 'Not found');
        my $type_color = (-b $dev || -d $dev) ? 'var(--mn-muted)' : 'var(--mn-red)';
        my $info = $cache->{disks}{$dev};
        my $usage_str = 'n/a';
        if ($info && defined($info->{total_gb}) && defined($info->{used_gb})) {
            $usage_str = "$info->{used_gb} / $info->{total_gb} GB";
        }
        my $dev_esc = &WebminCore::html_escape($dev);
        print "<tr>";
        print "<td class='mn-mono'>$dev_esc</td>";
        print "<td>";
        print "<form action='manage_disks.cgi' method='post' style='display:flex; gap:6px; align-items:center;'>";
        print &WebminCore::ui_hidden('action', 'relabel');
        print &WebminCore::ui_hidden('path', $dev);
        print "<input class='mn-input' type='text' name='label' value='".&WebminCore::html_escape($label)."' style='max-width:160px; padding:5px 8px; font-size:13px;'>";
        print "<button type='submit' class='mn-icon-btn' title='Save label'><i class='ti ti-check'></i></button>";
        print "</form>";
        print "</td>";
        print "<td style='color:$type_color;'>$type</td>";
        print "<td class='mn-mono'>$usage_str</td>";
        print "<td style='text-align:center; white-space:nowrap;'>";
        print "<form action='manage_disks.cgi' method='post' onsubmit=\"return confirm('Remove $dev_esc from disks.conf? This does not unmount or delete data.');\" style='display:inline;'>";
        print &WebminCore::ui_hidden('action', 'remove');
        print &WebminCore::ui_hidden('path', $dev);
        print "<button type='submit' class='mn-icon-btn mn-icon-btn-del' title='Remove'><i class='ti ti-trash'></i></button>";
        print "</form>";
        print "</td>";
        print "</tr>";
    }
} else {
    print "<tr><td colspan='5' style='color:var(--mn-muted); font-style:italic;'>No disks configured yet.</td></tr>";
}
print "</table></div></div>";

# ── Erkannte Kandidaten (Blockgeräte + gängige Mountpoints) ────────
my @candidates;
if (opendir(my $dh, '/sys/block')) {
    foreach my $b (readdir($dh)) {
        next if $b =~ /^\./;
        next if $b =~ /^(loop|ram|sr|dm-|zram)/;
        my $devpath = "/dev/$b";
        push @candidates, $devpath if -b $devpath;
        # Partitionen mit auflisten (z.B. sda1)
        if (opendir(my $pdh, "/sys/block/$b")) {
            foreach my $p (readdir($pdh)) {
                next unless $p =~ /^\Q$b\E\d+$/;
                push @candidates, "/dev/$p" if -b "/dev/$p";
            }
            closedir($pdh);
        }
    }
    closedir($dh);
}
my %already = map { $_->{dev} => 1 } @$disks_ref;
@candidates = grep { !$already{$_} } @candidates;

my @mount_candidates;
if (open(my $mf, '<', '/proc/mounts')) {
    while (<$mf>) {
        my (undef, $mp, $fstype) = split(' ');
        next unless $mp;
        next if $mp eq '/' || $mp =~ m{^/(proc|sys|dev|run|boot)(/|$)};
        next if $fstype =~ /^(tmpfs|devtmpfs|proc|sysfs|cgroup|overlay|squashfs|autofs)$/;
        next if $already{$mp};
        push @mount_candidates, $mp;
    }
    close($mf);
}

# ── Formular: neue Disk hinzufügen ─────────────────────────────────
print "<div class='mn-form-wrap'>";
print "<div class='mn-form-title'><i class='ti ti-plus' style='margin-right:6px; color:var(--mn-muted);'></i>Add disk</div>";
print "<form action='manage_disks.cgi' method='post'>";
print &WebminCore::ui_hidden('action', 'add');

if (@candidates || @mount_candidates) {
    print "<div class='mn-hint' style='margin-bottom:8px;'>Detected but not yet configured:</div>";
    print "<div style='display:flex; flex-wrap:wrap; gap:6px; margin-bottom:14px;'>";
    foreach my $c (@candidates) {
        my $c_esc = &WebminCore::html_escape($c);
        print "<button type='button' class='mn-btn' style='font-size:12px; padding:5px 10px;' onclick=\"document.getElementById('new_path_input').value='$c_esc';\"><i class='ti ti-device-sd-card'></i> $c_esc</button>";
    }
    foreach my $c (@mount_candidates) {
        my $c_esc = &WebminCore::html_escape($c);
        print "<button type='button' class='mn-btn' style='font-size:12px; padding:5px 10px;' onclick=\"document.getElementById('new_path_input').value='$c_esc';\"><i class='ti ti-folder'></i> $c_esc</button>";
    }
    print "</div>";
}

print "<div class='mn-form-row'>";
print "<div class='mn-form-col'><label class='mn-label'>Device or mount path</label><input class='mn-input' type='text' name='new_path' id='new_path_input' placeholder='/dev/sdb1 or /mnt/mydisk'></div>";
print "<div class='mn-form-col'><label class='mn-label'>Label</label><input class='mn-input' type='text' name='new_label' placeholder='e.g. TimeMachine' maxlength='32'></div>";
print "</div>";
print "<div style='margin-top:10px;'><button type='submit' class='mn-btn mn-btn-primary'><i class='ti ti-plus'></i> Add disk</button></div>";
print "</form></div>";

print "</div>";
&WebminCore::ui_print_footer("index.cgi", "Back to Dashboard");

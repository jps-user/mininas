# /usr/share/webmin/mininas/mininas-lib.pl
# Zentrale Bibliothek – alle gemeinsamen Funktionen für MiniNAS

package main;
use strict;
use warnings;

# ── Konstanten ───────────────────────────────────────────────────

use constant SMB_CONF => '/etc/samba/smb.conf';

# Erlaubte Basispfade für Shares (Sicherheits-Whitelist)
use constant ALLOWED_BASE_PATHS => [qw(/mnt /srv)];

# ── smb.conf Zugriff ─────────────────────────────────────────────

sub get_smb_conf_path {
    return SMB_CONF;
}

# Parst alle Sektionen aus der smb.conf.
# Gibt (\@lines, \@sections) zurück.
# Jede Sektion: { name => '...', raw => '...' }
sub parse_smb_sections_v2 {
    my $path = get_smb_conf_path();
    my @lines;
    if (open(my $fh, '<', $path)) {
        @lines = <$fh>;
        close($fh);
    }
    my @sections;
    my $current = undef;
    foreach my $line (@lines) {
        if ($line =~ /^\s*\[([^\]]+)\]/) {
            $current = { name => $1, raw => '' };
            push(@sections, $current);
        } elsif ($current) {
            $current->{raw} .= $line;
        }
    }
    return (\@lines, \@sections);
}

# Gibt den Pfad eines Shares aus dem raw-Block zurück.
# Gibt '' zurück wenn nicht gefunden.
sub mn_get_share_path {
    my ($section) = @_;
    return '' unless $section && $section->{raw};
    my ($path) = ($section->{raw} =~ /path\s*=\s*([^\n]+)/i);
    $path =~ s/^\s+|\s+$//g if $path;
    return $path || '';
}

# Schreibt smb.conf atomar: lock → backup → tmp → rename → testparm → unlock
# Bei testparm-Fehler: Rollback auf Backup, unlock, error().
# $new_lines_ref: Arrayref mit den zu schreibenden Zeilen
sub mn_write_smb_conf {
    my ($new_lines_ref) = @_;
    my $smb_conf = get_smb_conf_path();
    my $tmp_conf = "$smb_conf.tmp";
    my $bak_conf = "$smb_conf.bak";

    &WebminCore::lock_file($smb_conf);
    system('cp', $smb_conf, $bak_conf);

    if (open(my $wfh, '>', $tmp_conf)) {
        print $wfh join('', @$new_lines_ref);
        close($wfh);
        rename($tmp_conf, $smb_conf);
    } else {
        system('cp', $bak_conf, $smb_conf);
        unlink($bak_conf);
        &WebminCore::unlock_file($smb_conf);
        &WebminCore::error("Failed to write smb.conf: $!");
    }

    my ($tp_ok, undef) = mn_testparm();
    if (!$tp_ok) {
        system('cp', $bak_conf, $smb_conf);
        unlink($bak_conf);
        &WebminCore::unlock_file($smb_conf);
        &WebminCore::error('Samba configuration syntax check failed – changes rolled back.');
    }

    unlink($bak_conf);
    &WebminCore::unlock_file($smb_conf);
    return 1;
}

# ── User-Validierung ─────────────────────────────────────────────

# Prüft ob ein Username syntaktisch gültig ist.
# $allow_upper: 1 = Grossbuchstaben erlauben (z.B. TM1, für Samba-only User)
sub mn_validate_username {
    my ($u, $allow_upper) = @_;
    return 0 unless $u;
    if ($allow_upper) {
        return ($u =~ /^[a-zA-Z_][a-zA-Z0-9_-]*$/) ? 1 : 0;
    }
    return ($u =~ /^[a-z_][a-z0-9_-]*$/) ? 1 : 0;
}

# Prüft ob ein Pfad in der Sicherheits-Whitelist liegt.
# Erlaubt beliebige Tiefe unterhalb eines Basis-Pfads (z.B. /mnt/<disk>/<share>
# für Shares auf einer konfigurierten Zusatz-Disk), keine ".." Traversal,
# keine Sonderzeichen ausserhalb a-zA-Z0-9_- und /.
sub mn_validate_path {
    my ($path) = @_;
    return 0 unless $path;
    return 0 if $path =~ /\.\./;
    foreach my $base (@{ALLOWED_BASE_PATHS()}) {
        return 1 if $path =~ m{^\Q$base\E(?:/[a-zA-Z0-9_\-]+)+$};
    }
    return 0;
}

# ── User aus smb.conf entfernen ──────────────────────────────────

# Entfernt einen User aus allen valid users / read list Zeilen der smb.conf.
# Schreibt atomar mit lock_file, OHNE testparm (reine Zeilen-Bereinigung).
# Gibt 1 bei Erfolg zurück.
sub mn_remove_user_from_conf {
    my ($u) = @_;
    my $smb_conf = get_smb_conf_path();

    open(my $fh, '<', $smb_conf) or return 0;
    my @lines = <$fh>;
    close($fh);

    my @new_lines;
    foreach my $line (@lines) {
        if ($line =~ /^\s*(valid users|read list)\s*=\s*(.*)/i) {
            my $type = $1;
            my $src  = $2;
            my @kept = grep { $_ ne $u } split(/[\s,]+/, $src);
            foreach my $r (@kept) {
                push(@new_lines, "    $type = $r\n");
            }
            # Leere Zeile wird weggelassen – korrekt
        } else {
            push(@new_lines, $line);
        }
    }

    &WebminCore::lock_file($smb_conf);
    if (open(my $wfh, '>', $smb_conf)) {
        print $wfh join('', @new_lines);
        close($wfh);
        &WebminCore::unlock_file($smb_conf);
        return 1;
    }
    &WebminCore::unlock_file($smb_conf);
    return 0;
}

# ── Samba-Dienste ────────────────────────────────────────────────

sub reload_samba {
    system('smbcontrol all reload-config >/dev/null 2>&1');
    system('systemctl reload smbd >/dev/null 2>&1');
}

# Prüft ob ein systemd-Service aktiv ist. Gibt 1/0 zurück.
sub mn_service_active {
    my ($service) = @_;
    return 0 unless $service;
    my $status = `systemctl is-active \Q$service\E 2>/dev/null`;
    chomp $status;
    return ($status eq 'active') ? 1 : 0;
}

# Führt testparm gegen die aktuelle smb.conf aus.
# Gibt ($ok, $raw_output) zurück. $ok ist 1 bei Erfolg, 0 bei Fehler.
sub mn_testparm {
    my $smb_conf = get_smb_conf_path();
    my $output = `testparm -s \Q$smb_conf\E 2>&1`;
    my $ok = ($? == 0) ? 1 : 0;
    return ($ok, $output);
}

# ── Linux-User-Verwaltung ────────────────────────────────────────

# Legt einen Linux-System-User an (ohne Login-Shell, für Samba-only Zugriff).
# $create_home: 1 = Home-Verzeichnis unter /home/$username anlegen, 0 = keins.
# Gibt 1 bei Erfolg, 0 bei Fehler zurück.
sub mn_create_os_user {
    my ($username, $create_home) = @_;
    return 0 unless $username;
    my @cmd = ('useradd', '-s', '/usr/sbin/nologin');
    if ($create_home) {
        push(@cmd, '-m', '-d', "/home/$username");
    } else {
        push(@cmd, '-M');    # explizit: kein Home-Verzeichnis
    }
    push(@cmd, $username);
    system(@cmd);
    return ($? == 0) ? 1 : 0;
}

# Gibt den aktuellen Home-Pfad eines Users zurück, oder '' wenn keiner existiert
# oder der User unbekannt ist.
sub mn_get_home_dir {
    my ($username) = @_;
    return '' unless $username;
    my @pw = getpwnam($username);
    return '' unless @pw;
    my $home = $pw[7];
    return ($home && -d $home) ? $home : '';
}

# Legt nachträglich ein Home-Verzeichnis für einen bestehenden User an.
# Gibt 1 bei Erfolg, 0 bei Fehler zurück.
sub mn_add_home_dir {
    my ($username) = @_;
    return 0 unless $username && mn_validate_username($username, 1);
    my $home = "/home/$username";
    return 0 if -d $home;    # existiert schon

    system('mkdir', '-p', $home);
    return 0 if $? != 0;
    system('chown', "$username:$username", $home);
    system('chmod', '0750', $home);
    system('usermod', '-d', $home, $username);
    return ($? == 0) ? 1 : 0;
}

# Entfernt das Home-Verzeichnis eines Users unwiderruflich.
# Nur Pfade unter /home/ werden akzeptiert (Sicherheits-Whitelist).
# Gibt 1 bei Erfolg, 0 bei Fehler zurück.
sub mn_remove_home_dir {
    my ($username) = @_;
    return 0 unless $username;
    my $home = mn_get_home_dir($username);
    return 1 unless $home;                      # kein Home vorhanden - nichts zu tun
    return 0 unless $home =~ m{^/home/[a-zA-Z0-9_.\-]+$};   # Sicherheits-Whitelist

    system('rm', '-rf', $home);
    return 0 if $? != 0;
    system('usermod', '-d', '/nonexistent', $username);
    return ($? == 0) ? 1 : 0;
}

# Setzt das Samba-Passwort für einen bestehenden User (OS oder Samba-only).
# Gibt 1 bei Erfolg, 0 bei Fehler zurück.
sub mn_set_samba_password {
    my ($username, $password) = @_;
    return 0 unless $username && $password;
    if (open(my $smb, '|-', 'smbpasswd', '-s', '-a', $username)) {
        print $smb "$password\n$password\n";
        close($smb);
        return ($? == 0) ? 1 : 0;
    }
    return 0;
}

# Entfernt einen User komplett aus Samba und dem Linux-System.
# Wird nur bei 'full_cleanup' aufgerufen, niemals bei 'config_only'.
sub mn_delete_os_user {
    my ($username) = @_;
    return 0 unless $username;
    system('smbpasswd', '-x', $username);
    system('userdel', '-r', $username);
    return 1;
}

# ── Filesystem-Berechtigungen ─────────────────────────────────────

# Setzt Owner:Group und Mode auf einen Pfad.
# Gibt 1 bei Erfolg, 0 bei Fehler zurück (chown ODER chmod fehlgeschlagen).
sub mn_set_ownership {
    my ($path, $owner, $group, $mode) = @_;
    return 0 unless $path && $owner;
    $group ||= 'sambashare';
    $mode  ||= '0770';
    system('chown', "$owner:$group", $path);
    return 0 if $? != 0;
    system('chmod', $mode, $path);
    return 0 if $? != 0;
    return 1;
}

# Legt ein Share-Verzeichnis an und setzt Standard-Berechtigungen (0770, sambashare).
# Gibt 1 bei Erfolg, 0 bei Fehler zurück.
sub mn_create_share_dir {
    my ($path, $owner, $group, $mode) = @_;
    return 0 unless $path;
    system('mkdir', '-p', $path);
    return 0 if $? != 0;
    return 1 unless $owner;    # kein Owner angegeben: nur Verzeichnis anlegen
    return mn_set_ownership($path, $owner, $group, $mode);
}

# ── Storage Cache (Etappe 1) ──────────────────────────────────────
# Zero-Additional-Infrastructure: kein Cron, kein Daemon. Der Cache wird
# nur nach Filesystem-Aktionen (Platten dann garantiert wach) und explizit
# via "Wake & measure" geschrieben. Disk-Messungen werden NIE ausgeführt
# wenn die Disk gerade schläft (kein ungewolltes Aufwecken).

use constant STORAGE_CACHE => '/var/lib/mininas/storage.cache';
use constant DISKS_CONF    => '/var/lib/mininas/disks.conf';

# Erkennt ob wir in einem LXC-Container laufen (vs. Bare Metal).
sub mn_is_lxc {
    return 1 if -f '/run/systemd/container';
    my $env = `grep -c "container=lxc" /proc/1/environ 2>/dev/null`;
    chomp $env if defined $env;
    return ($env && $env > 0) ? 1 : 0;
}

# Liest /var/lib/mininas/disks.conf: Zeilen "device:label".
# Gibt eine Arrayref von { dev => ..., label => ... } zurück, in Datei-Reihenfolge.
sub mn_read_disks_conf {
    my @disks;
    if (open(my $fh, '<', DISKS_CONF)) {
        while (my $line = <$fh>) {
            chomp $line;
            next unless $line =~ /\S/;
            my ($dev, $label) = split(/:/, $line, 2);
            next unless $dev;
            push @disks, { dev => $dev, label => $label || $dev };
        }
        close($fh);
    }
    return \@disks;
}

# Findet zu einem Share-Pfad die passende konfigurierte Disk (per längstem
# Mountpoint-Präfix-Match). Nur Mountpoint-Einträge in disks.conf sind hier
# relevant (Blockgerät-Einträge wie /dev/sdX haben keinen Pfad-Namensraum,
# der sich mit einem Share-Pfad wie /srv/foo überschneiden könnte).
# Gibt das Label zurück, oder undef wenn kein Match / Share auf dem
# System-Rootfs liegt (kein konfigurierter Disk-Eintrag passt).
sub mn_find_disk_for_path {
    my ($path) = @_;
    return undef unless $path;
    my $disks_ref = mn_read_disks_conf();
    my $best_label;
    my $best_len = 0;
    foreach my $d (@$disks_ref) {
        my $dev = $d->{dev};
        next if -b $dev;    # Blockgerät ohne eigenen Pfad-Namensraum -> nicht matchbar
        next unless -d $dev;
        my $prefix = $dev;
        $prefix =~ s{/+$}{};
        next unless $path eq $prefix || substr($path, 0, length($prefix) + 1) eq "$prefix/";
        if (length($prefix) > $best_len) {
            $best_len   = length($prefix);
            $best_label = $d->{label};
        }
    }
    return $best_label;
}

# Schreibt disks.conf neu aus einer Arrayref von { dev => ..., label => ... }.
sub mn_write_disks_conf {
    my ($disks_ref) = @_;
    system('mkdir', '-p', '/var/lib/mininas');
    if (open(my $fh, '>', DISKS_CONF)) {
        foreach my $d (@$disks_ref) {
            print $fh "$d->{dev}:$d->{label}\n";
        }
        close($fh);
        return 1;
    }
    return 0;
}

# Prüft ob eine Disk im Standby/Sleep-Zustand ist.
# Primär via hdparm -C, mit Fallback auf /proc/diskstats bei USB-Bridges,
# die hdparm -C oft nicht unterstützen (z.B. ORICO, ASMedia).
# Gibt 1 = schläft, 0 = wach/aktiv, undef = Status unbekannt zurück.
#
# Akzeptiert entweder ein Blockgerät (/dev/sdX) oder einen Mountpoint-Pfad
# (z.B. wenn die Disk via Proxmox mp0 als Verzeichnis ins LXC durchgereicht
# wird und kein Blockgerät im Container sichtbar ist). Für Mountpoint-Pfade
# ist der Sleep-Status grundsätzlich nicht feststellbar -> undef, die
# gecachten Werte bleiben dann einfach stehen (siehe mn_update_storage_cache).
sub mn_disk_is_sleeping {
    my ($dev) = @_;
    return undef unless $dev;
    return undef unless -b $dev;    # kein Blockgerät (z.B. Mountpoint-Pfad) -> Status unbekannt

    my $out = `hdparm -C \Q$dev\E 2>/dev/null`;
    if ($out =~ /drive state is:\s*(\S+)/i) {
        my $state = lc($1);
        return 1 if $state eq 'standby' || $state eq 'sleeping';
        return 0 if $state eq 'active/idle' || $state eq 'active';
    }

    # Fallback: /proc/diskstats – zwei Messungen im Abstand vergleichen.
    # Keine Aktivität über das Intervall wird als "vermutlich inaktiv" gewertet,
    # ist aber kein zuverlässiger Sleep-Nachweis – daher undef statt 1.
    my $devname = $dev; $devname =~ s{^/dev/}{};
    my $stat1 = mn_read_diskstat($devname);
    return undef unless defined $stat1;
    select(undef, undef, undef, 0.2);
    my $stat2 = mn_read_diskstat($devname);
    return undef unless defined $stat2;
    return ($stat1 == $stat2) ? undef : 0;
}

# Liest die Summe aus Sektoren gelesen+geschrieben für ein Device aus /proc/diskstats.
sub mn_read_diskstat {
    my ($devname) = @_;
    return undef unless -r '/proc/diskstats';
    open(my $fh, '<', '/proc/diskstats') or return undef;
    while (my $line = <$fh>) {
        my @f = split(' ', $line);
        next unless @f >= 14;
        if ($f[2] eq $devname) {
            close($fh);
            return $f[5] + $f[9];    # sectors read + sectors written
        }
    }
    close($fh);
    return undef;
}

# Liefert (total_gb, used_gb) für eine Disk via df.
# Akzeptiert entweder ein Blockgerät (/dev/sdX, muss gemountet sein) oder
# einen Mountpoint-Pfad (z.B. bei Proxmox mp0 Passthrough ohne Blockgerät
# im Container). Gibt (undef, undef) wenn nicht messbar.
sub mn_get_disk_usage {
    my ($dev) = @_;
    return (undef, undef) unless $dev;
    return (undef, undef) unless (-b $dev) || (-d $dev);
    my $out = `df -BG --output=size,used \Q$dev\E 2>/dev/null | tail -n1`;
    if ($out =~ /(\d+)G\s+(\d+)G/) {
        return ($1, $2);
    }
    return (undef, undef);
}

# Liefert den Füllstand eines Share-Pfads in GB via du -sh.
# Gibt 'n/a' zurück wenn der Pfad fehlt oder du fehlschlägt.
sub mn_get_share_usage {
    my ($path) = @_;
    return 'n/a' unless $path && -d $path;
    my $out = `du -sBG \Q$path\E 2>/dev/null | awk '{print \$1}'`;
    chomp $out;
    return 'n/a' unless $out;
    $out =~ s/G$//;
    return ($out =~ /^\d+$/) ? $out : 'n/a';
}

# Schreibt den kompletten Storage-Cache neu.
# WICHTIG: misst eine Disk nur wenn sie wach ist (mn_disk_is_sleeping == 0).
# Schläft sie (== 1) oder ist der Status unbekannt (undef), werden die
# zuvor gecachten Werte für diese Disk unverändert übernommen statt neu
# gemessen – so wird nie ungewollt eine schlafende Platte aufgeweckt.
sub mn_update_storage_cache {
    my $old = mn_read_storage_cache();
    my $disks_ref = mn_read_disks_conf();

    my %new_disks;
    foreach my $d (@$disks_ref) {
        my $dev   = $d->{dev};
        my $label = $d->{label};
        my $is_block_dev = -b $dev;
        my $sleeping = mn_disk_is_sleeping($dev);

        # Pfad-basierte Einträge (Mountpoint statt Blockgerät, z.B. Proxmox
        # mp0-Passthrough ohne sichtbares /dev/sdX im Container) werden immer
        # gemessen: df gegen einen Mountpoint liest nur Dateisystem-Metadaten
        # und kann eine schlafende Disk nicht aufwecken. Nur bei einem
        # echten Blockgerät mit unbekanntem/schlafendem Zustand wird
        # konservativ auf den alten Wert zurückgefallen.
        if ($is_block_dev && !(defined($sleeping) && $sleeping == 0)) {
            # Schläft oder unbekannt: alten Wert übernehmen, nicht messen.
            my $prev = $old->{disks}{$dev};
            $new_disks{$dev} = {
                total_gb => $prev ? $prev->{total_gb} : undef,
                used_gb  => $prev ? $prev->{used_gb}  : undef,
                label    => $label,
                sleeping => defined($sleeping) ? $sleeping : ($prev ? $prev->{sleeping} : undef),
            };
        } else {
            my ($total, $used) = mn_get_disk_usage($dev);
            $new_disks{$dev} = { total_gb => $total, used_gb => $used, label => $label,
                                  sleeping => $is_block_dev ? 0 : undef };
        }
    }

    # Shares nur messen wenn ALLE konfigurierten Disks wach sind (kein
    # Aufwecken durch du -sh auf einem Pfad, dessen Disk gerade schläft).
    my $any_sleeping = grep { defined($_->{sleeping}) && $_->{sleeping} == 1 } values %new_disks;
    my %new_shares;
    my (undef, $sections_ref) = parse_smb_sections_v2();
    foreach my $s (@$sections_ref) {
        next if $s->{name} eq 'global';
        my $path = mn_get_share_path($s);
        next unless $path;
        if ($any_sleeping) {
            my $prev = $old->{shares}{$s->{name}};
            $new_shares{$s->{name}} = defined($prev) ? $prev : 'n/a';
        } else {
            $new_shares{$s->{name}} = mn_get_share_usage($path);
        }
    }

    system('mkdir', '-p', '/var/lib/mininas');
    if (open(my $fh, '>', STORAGE_CACHE)) {
        my $ts = strftime_local();
        print $fh "timestamp:$ts\n";
        foreach my $dev (sort keys %new_disks) {
            my $d = $new_disks{$dev};
            my $total = defined($d->{total_gb}) ? $d->{total_gb} : 'n/a';
            my $used  = defined($d->{used_gb})  ? $d->{used_gb}  : 'n/a';
            print $fh "disk:$dev:total_gb:$total:used_gb:$used:label:$d->{label}\n";
        }
        foreach my $name (sort keys %new_shares) {
            print $fh "share:$name:used_gb:$new_shares{$name}\n";
        }
        close($fh);
        return 1;
    }
    return 0;
}

# Kleine lokale strftime-Helper ohne POSIX-Abhängigkeit (Y-m-d H:M:S).
sub strftime_local {
    my @t = localtime();
    return sprintf('%04d-%02d-%02d %02d:%02d:%02d',
        $t[5] + 1900, $t[4] + 1, $t[3], $t[2], $t[1], $t[0]);
}

# Liest den Storage-Cache und gibt eine Struktur zurück:
# { timestamp => '...', disks => { $dev => {total_gb,used_gb,label} }, shares => { $name => used_gb } }
sub mn_read_storage_cache {
    my %result = (timestamp => '', disks => {}, shares => {});
    return \%result unless -r STORAGE_CACHE;
    open(my $fh, '<', STORAGE_CACHE) or return \%result;
    while (my $line = <$fh>) {
        chomp $line;
        if ($line =~ /^timestamp:(.+)$/) {
            $result{timestamp} = $1;
        } elsif ($line =~ /^disk:([^:]+):total_gb:([^:]+):used_gb:([^:]+):label:(.+)$/) {
            $result{disks}{$1} = {
                total_gb => ($2 eq 'n/a' ? undef : $2),
                used_gb  => ($3 eq 'n/a' ? undef : $3),
                label    => $4,
            };
        } elsif ($line =~ /^share:([^:]+):used_gb:(.+)$/) {
            $result{shares}{$1} = $2;
        }
    }
    close($fh);
    return \%result;
}

# ── Logging ──────────────────────────────────────────────────────

sub write_mininas_log {
    my ($action, $msg) = @_;
    my $logfile = '/var/log/mininas.log';
    if (open(my $fh, '>>', $logfile)) {
        my $ts = scalar localtime();
        print $fh "[$ts] [$action] $msg\n";
        close($fh);
    }
}

# Letzte N Log-Einträge lesen (für Dashboard)
sub mn_read_log {
    my ($n) = @_;
    $n ||= 8;
    my $logfile = '/var/log/mininas.log';
    return () unless -r $logfile;
    open(my $fh, '<', $logfile) or return ();
    my @lines = <$fh>;
    close($fh);
    my @last = reverse(splice(@lines, -$n));
    my @entries;
    foreach my $line (@last) {
        chomp $line;
        if ($line =~ /\[([^\]]+)\]\s*\[([^\]]+)\]\s*(.+)/) {
            my ($ts, $action, $msg) = ($1, $2, $3);
            my $time = ($ts =~ /(\d{2}:\d{2})/) ? $1 : '—';
            push @entries, { time => $time, action => $action, msg => $msg };
        }
    }
    return @entries;
}

1;

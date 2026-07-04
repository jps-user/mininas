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

    system("testparm -s \Q$smb_conf\E >/dev/null 2>&1");
    if ($? != 0) {
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
sub mn_validate_path {
    my ($path) = @_;
    return 0 unless $path;
    foreach my $base (@{ALLOWED_BASE_PATHS()}) {
        return 1 if $path =~ m{^\Q$base\E/[a-zA-Z0-9_\-]+$};
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

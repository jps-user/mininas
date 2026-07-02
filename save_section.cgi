#!/usr/bin/perl
# save_section.cgi - Speichert Hybrid-Editor (strukturierte Felder + Raw)

package main;
BEGIN { push(@INC, ".."); };
use WebminCore;
&init_config();
&ReadParse();
require 'mininas/mininas-lib.pl';

if ($in{'action'} eq 'cancel') {
    &WebminCore::redirect("index.cgi");
    exit;
}

my $section     = $in{'section'};
my $old_section = $in{'old_section'} || $section;

if (!$section) { &WebminCore::error("No section name provided."); }

my $smb_conf = get_smb_conf_path();
my $tmp_conf = "$smb_conf.tmp";
my $bak_conf = "$smb_conf.bak";

my ($lines_ref, $sections_ref) = parse_smb_sections_v2();

# ── Prüfen ob [global] oder normaler Share ───────────────────────
my $is_global = ($section eq 'global');

my $new_block = "";

if ($is_global) {
    # Global: nur Raw, 1:1 übernehmen
    my $raw = $in{'raw_extra'} || "";
    $raw =~ s/\r\n/\n/g;
    # Jede Zeile mit 4 Spaces einrücken
    foreach my $rl (split(/\n/, $raw)) {
        $rl =~ s/^\s+//;
        if ($rl =~ /\S/) {
            $new_block .= "    $rl\n";
        } else {
            $new_block .= "\n";
        }
    }

} else {
    # ── Strukturierte Felder einlesen ────────────────────────────
    my $f_path      = $in{'f_path'}      || "";
    my $f_writable  = $in{'f_writable'}  ? "yes" : "no";
    my $f_browsable = $in{'f_browsable'} ? "yes" : "no";
    my $raw_extra   = $in{'raw_extra'}   || "";

    $f_path =~ s/^\s+|\s+$//g;
    $raw_extra =~ s/\r\n/\n/g;

    # RW-User: eine Zeile pro Eintrag
    my @rw_users = grep { /\S/ } split(/[\r\n]+/, $in{'f_valid_rw'} || "");
    my @ro_users = grep { /\S/ } split(/[\r\n]+/, $in{'f_valid_ro'} || "");
    s/^\s+|\s+$//g for (@rw_users, @ro_users);

    # ── Pfad-Aktion (Filesystem) ─────────────────────────────────
    my $path_action = $in{'path_action'} || 'none';

    # Alten Pfad aus bestehender Sektion ermitteln
    my ($target) = grep { $_->{name} eq $old_section } @$sections_ref;
    my $old_path = "";
    if ($target && $target->{raw} =~ /path\s*=\s*([^\n]+)/i) {
        $old_path = $1; $old_path =~ s/^\s+|\s+$//g;
    }

    if ($f_path && $f_path ne $old_path && $path_action ne 'none') {
        # Pfad-Validierung: nur /mnt/... oder /srv/...
        if ($f_path !~ m{^/(mnt|srv)/[a-zA-Z0-9_\-]+$}) {
            &WebminCore::error("Invalid path '$f_path'. Only /mnt/... and /srv/... are allowed.");
        }

        if ($path_action eq 'mkdir') {
            system("mkdir", "-p", $f_path);
            if ($? != 0) {
                &WebminCore::error("Failed to create directory '$f_path'. Check permissions.");
            }
            if (@rw_users) {
                system("chown", "$rw_users[0]:sambashare", $f_path);
                system("chmod", "0770", $f_path);
            }
        } elsif ($path_action eq 'rename') {
            if ($old_path && -d $old_path) {
                system("mv", $old_path, $f_path);
                if ($? != 0) {
                    &WebminCore::error("Failed to move '$old_path' to '$f_path'. " .
                                       "Check permissions or whether target already exists. " .
                                       "smb.conf was NOT changed.");
                }
            } else {
                system("mkdir", "-p", $f_path);
                if ($? != 0) {
                    &WebminCore::error("Failed to create directory '$f_path'. Check permissions.");
                }
                if (@rw_users) {
                    system("chown", "$rw_users[0]:sambashare", $f_path);
                    system("chmod", "0770", $f_path);
                }
            }
        }
    }

    # ── Neuen Config-Block zusammenbauen ─────────────────────────
    $new_block .= "    path = $f_path\n"       if $f_path;
    $new_block .= "    writable = $f_writable\n";
    $new_block .= "    browsable = $f_browsable\n";

    foreach my $u (@rw_users) {
        $new_block .= "    valid users = $u\n";
    }
    foreach my $u (@ro_users) {
        $new_block .= "    read list = $u\n";
    }

    # Raw-Extra anhängen: jede Zeile automatisch mit 4 Spaces einrücken
    if ($raw_extra =~ /\S/) {
        my @raw_lines = split(/\n/, $raw_extra);
        foreach my $rl (@raw_lines) {
            $rl =~ s/^\s+//;          # führende Spaces entfernen
            if ($rl =~ /\S/) {
                $new_block .= "    $rl\n";   # 4 Spaces voranstellen
            } else {
                $new_block .= "\n";           # Leerzeilen lassen
            }
        }
    }
}

# ── In smb.conf schreiben ────────────────────────────────────────
my @new_lines;
my $found = 0;

foreach my $s (@$sections_ref) {
    if ($s->{name} eq $old_section) {
        my $block = $new_block;
        $block =~ s/\n+$/\n/;    # trailing Leerzeilen auf eine reduzieren
        push(@new_lines, "[$section]\n");
        push(@new_lines, $block);
        push(@new_lines, "\n");   # genau eine Leerzeile nach Sektion
        $found = 1;
    } else {
        my $raw = $s->{raw};
        $raw =~ s/\n+$/\n/;      # trailing Leerzeilen aus raw entfernen
        push(@new_lines, "[$s->{name}]\n");
        push(@new_lines, $raw);
        push(@new_lines, "\n");   # genau eine Leerzeile nach Sektion
    }
}
if (!$found) {
    my $block = $new_block;
    $block =~ s/\n+$/\n/;
    push(@new_lines, "[$section]\n");
    push(@new_lines, $block);
    push(@new_lines, "\n");
}

&WebminCore::lock_file($smb_conf);
system("cp", $smb_conf, $bak_conf);

if (open(my $wfh, '>', $tmp_conf)) {
    print $wfh join('', @new_lines);
    close($wfh);
    rename($tmp_conf, $smb_conf);

    system("testparm -s \Q$smb_conf\E >/dev/null 2>&1");
    if ($? != 0) {
        system("cp", $bak_conf, $smb_conf);
        unlink($bak_conf);
        &WebminCore::unlock_file($smb_conf);
        &WebminCore::error("Samba config syntax check failed – changes rolled back.");
    }

    unlink($bak_conf);
    &WebminCore::unlock_file($smb_conf);
    reload_samba();
    write_mininas_log("SHARE_EDIT", "Edited section [$section] via hybrid editor.");
    &WebminCore::redirect("index.cgi");
} else {
    &WebminCore::unlock_file($smb_conf);
    &WebminCore::error("Failed to write smb.conf: $!");
}

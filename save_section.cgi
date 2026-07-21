#!/usr/bin/perl
package main;
BEGIN { push(@INC, '..'); }
use WebminCore;
&init_config();
&ReadParse();
require 'mininas/mininas-lib.pl';

&WebminCore::redirect('index.cgi') if $in{'action'} eq 'cancel';

my $section     = $in{'section'};
my $old_section = $in{'old_section'} || $section;
&WebminCore::error('No section name provided.') unless $section;

my ($lines_ref, $sections_ref) = parse_smb_sections_v2();
my $is_global = ($section eq 'global');
my $new_block = '';

if ($is_global) {
    my $raw = $in{'raw_extra'} || '';
    $raw =~ s/\r\n/\n/g;
    foreach my $rl (split(/\n/, $raw)) {
        $rl =~ s/^\s+//;
        $new_block .= ($rl =~ /\S/) ? "    $rl\n" : "\n";
    }
} else {
    my $f_path      = $in{'f_path'}     || '';
    my $f_writable  = $in{'f_writable'} ? 'yes' : 'no';
    my $f_browsable = $in{'f_browsable'}? 'yes' : 'no';
    my $raw_extra   = $in{'raw_extra'}  || '';

    $f_path =~ s/^\s+|\s+$//g;
    $raw_extra =~ s/\r\n/\n/g;

    my @rw_users = grep { /\S/ } split(/[\r\n]+/, $in{'f_valid_rw'} || '');
    my @ro_users = grep { /\S/ } split(/[\r\n]+/, $in{'f_valid_ro'} || '');
    s/^\s+|\s+$//g for (@rw_users, @ro_users);

    # Pfad-Aktion (Filesystem). Greift wenn sich der Pfad geändert hat ODER
    # das Zielverzeichnis schlicht fehlt (z.B. Pfad wurde in einer früheren
    # Session gesetzt, das Verzeichnis aber nie angelegt) - sonst würde
    # "Create directory" bei unverändertem Pfad stillschweigend nichts tun.
    my $path_action = $in{'path_action'} || 'none';
    my ($target)    = grep { $_->{name} eq $old_section } @$sections_ref;
    my $old_path    = $target ? mn_get_share_path($target) : '';
    my $path_needs_action = $f_path && (($f_path ne $old_path) || !-d $f_path);

    if ($path_needs_action && $path_action ne 'none') {
        &WebminCore::error("Invalid path '$f_path'. Only /mnt/... and /srv/... are allowed.")
            unless mn_validate_path($f_path);

        my $owner = @rw_users ? $rw_users[0] : undef;

        if ($path_action eq 'mkdir') {
            # Neuen, leeren Ordner anlegen. Rührt den alten Pfad nicht an -
            # falls dort noch Daten liegen, bleiben sie unangetastet zurück.
            mn_create_share_dir($f_path, $owner)
                or &WebminCore::error("Failed to create directory '$f_path' or set ownership.");
        } elsif ($path_action eq 'rename') {
            # Alter Pfad existiert danach nicht mehr (mv) - Daten sind
            # ausschliesslich am neuen Ort. Fehlschlag statt Vermischen wenn
            # alter Pfad fehlt oder Ziel schon existiert.
            my ($ok, $err) = mn_rename_share_dir($old_path, $f_path, $owner);
            &WebminCore::error("Rename failed: $err smb.conf was NOT changed.") unless $ok;
        } elsif ($path_action eq 'move') {
            # Daten werden zum neuen Ort kopiert, danach wird der alte
            # Ordner komplett entfernt. Ergebnis wie Rename, aber als zwei
            # separate Schritte statt einem atomaren mv.
            my ($ok, $err) = mn_move_share_dir($old_path, $f_path, $owner);
            &WebminCore::error("Move failed: $err smb.conf was NOT changed.") unless $ok;
        } elsif ($path_action eq 'copy') {
            # Daten werden kopiert, alter Ordner bleibt komplett unangetastet.
            # Sicherste Variante - beide Orte existieren danach parallel.
            my ($ok, $err) = mn_copy_share_dir($old_path, $f_path, $owner);
            &WebminCore::error("Copy failed: $err smb.conf was NOT changed.") unless $ok;
        }
    }

    $new_block .= "    path = $f_path\n"        if $f_path;
    $new_block .= "    writable = $f_writable\n";
    $new_block .= "    browsable = $f_browsable\n";
    $new_block .= "    valid users = $_\n" for @rw_users;
    $new_block .= "    read list = $_\n"   for @ro_users;

    if ($raw_extra =~ /\S/) {
        foreach my $rl (split(/\n/, $raw_extra)) {
            $rl =~ s/^\s+//;
            $new_block .= ($rl =~ /\S/) ? "    $rl\n" : "\n";
        }
    }
}

# Neuen Block in Sections einfügen
my @new_lines;
my $found = 0;
foreach my $s (@$sections_ref) {
    if ($s->{name} eq $old_section) {
        my $block = $new_block; $block =~ s/\n+$/\n/;
        push(@new_lines, "[$section]\n", $block, "\n");
        $found = 1;
    } else {
        my $raw = $s->{raw}; $raw =~ s/\n+$/\n/;
        push(@new_lines, "[$s->{name}]\n", $raw, "\n");
    }
}
unless ($found) {
    my $block = $new_block; $block =~ s/\n+$/\n/;
    push(@new_lines, "[$section]\n", $block, "\n");
}

mn_write_smb_conf(\@new_lines);
reload_samba();
write_mininas_log('SHARE_EDIT', "Edited section [$section] via hybrid editor.");
mn_update_storage_cache();
&WebminCore::redirect('index.cgi');

#!/usr/bin/perl
package main;
use strict;
use warnings;
BEGIN { push(@INC, '..'); }
use WebminCore;
&init_config();
&ReadParse();
require 'mininas/mininas-lib.pl';

&WebminCore::redirect('index.cgi') if $in{'cancel'};

my $u = $in{'user'};
&WebminCore::error('No user specified.') unless $u;
&WebminCore::error("Invalid username '".&WebminCore::html_escape($u)."'.")
    unless mn_validate_username($u, 1);

my ($lines_ref, $sections_ref) = parse_smb_sections_v2();

foreach my $s (@$sections_ref) {
    next if $s->{name} eq 'global';
    my $sn        = $s->{name};
    my $is_active = $in{"share_active_$sn"};
    my $perm_mode = $in{"perm_mode_$sn"} || 'rw';

    # Bestehende Mitgliedschaft holen, $u entfernen, bei Bedarf neu hinzufügen.
    # WICHTIG: am Ende darf pro Section nur je EINE "valid users"- und EINE
    # "read list"-Zeile stehen. Samba übernimmt bei mehrfach vorkommenden
    # Parametern innerhalb derselben Section ausschliesslich die letzte
    # Instanz - eine zusätzlich angehängte Zeile würde alle bestehenden
    # Mitglieder der vorherigen Zeile stillschweigend rauswerfen.
    my ($rw_ref, $ro_ref) = mn_get_share_users($s);
    my %rw_seen; my @rw = grep { $_ ne $u && !$rw_seen{$_}++ } @$rw_ref;
    my %ro_seen; my @ro = grep { $_ ne $u && !$ro_seen{$_}++ } @$ro_ref;
    if ($is_active) {
        push(@rw, $u);
        push(@ro, $u) if $perm_mode eq 'ro';
    }

    # Alle bisherigen valid-users/read-list Zeilen entfernen, Rest beibehalten
    my @new_lines;
    foreach my $line (split(/\n/, $s->{raw})) {
        next if $line =~ /^\s*(valid users|read list)\s*=/i;
        push(@new_lines, $line);
    }
    push(@new_lines, "    valid users = " . join(' ', @rw)) if @rw;
    push(@new_lines, "    read list = "  . join(' ', @ro)) if @ro;

    $s->{raw} = join("\n", @new_lines);
}

my @new_lines;
foreach my $s (@$sections_ref) {
    my $raw = $s->{raw}; $raw =~ s/\n+$/\n/;
    push(@new_lines, "[$s->{name}]\n", $raw, "\n");
}

mn_write_smb_conf(\@new_lines);
reload_samba();
write_mininas_log('SHARES_SAVE', "Updated share permissions for user $u.");
&WebminCore::redirect('index.cgi');

#!/usr/bin/perl
package main;
BEGIN { push(@INC, '..'); }
use WebminCore;
&init_config();
&ReadParse();
require 'mininas/mininas-lib.pl';

&WebminCore::redirect('index.cgi') if $in{'cancel'};

my $u = $in{'user'};
&WebminCore::error('No user specified.') unless $u;

my ($lines_ref, $sections_ref) = parse_smb_sections_v2();

foreach my $s (@$sections_ref) {
    next if $s->{name} eq 'global';
    my $sn        = $s->{name};
    my $is_active = $in{"share_active_$sn"};
    my $perm_mode = $in{"perm_mode_$sn"} || 'rw';

    # User aus dieser Sektion entfernen
    my @new_lines;
    foreach my $line (split(/\n/, $s->{raw})) {
        next if $line =~ /^\s*(valid users|read list)\s*=\s*.*\b\Q$u\E\b/i;
        push(@new_lines, $line);
    }

    # Bei aktiver Zuweisung: User als eigene Zeile einfügen
    if ($is_active) {
        push(@new_lines, "    valid users = $u");
        push(@new_lines, "    read list = $u") if $perm_mode eq 'ro';
    }

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

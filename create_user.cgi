#!/usr/bin/perl
package main;
use strict;
use warnings;
BEGIN { push(@INC, '..'); }
use WebminCore;
&init_config();
&ReadParse();
require 'mininas/mininas-lib.pl';

my $username = $in{'username'};
my $password = $in{'password'};
my $mode     = $in{'creation_mode'};

&WebminCore::error('Username and password are required.')
    unless $username && $password;

&WebminCore::error('Invalid username format. Use lowercase letters, digits, - or _.')
    unless mn_validate_username($username, 0);

&WebminCore::error('Password must be at least 6 characters.')
    if length($password) < 6;

# 1. OS-User anlegen
mn_create_os_user($username, $in{'create_home'} ? 1 : 0)
    or &WebminCore::error("Failed to create Linux system user '$username'. Does it already exist?");

# 2. Samba-Passwort setzen
mn_set_samba_password($username, $password);

my ($lines_ref, $sections_ref) = parse_smb_sections_v2();

if ($mode eq 'isolated') {
    my $base   = $in{'base_path'} || '/mnt';
    my $folder = $in{'folder_name'} || $username;
    $base =~ s{/+$}{};
    my $path = "$base/$folder";

    &WebminCore::error('Invalid base path. Only /mnt and /srv are allowed.')
        unless mn_validate_path($path);

    mn_create_share_dir($path, $username)
        or &WebminCore::error("Failed to create directory '$path' or set ownership.");

    # Share-Block aufbauen
    my $share_type = $in{'share_type'} || 'standard';
    my $block  = "\n[$username]\n";
    $block    .= "    path = $path\n";
    $block    .= "    writable = yes\n";
    $block    .= "    browsable = yes\n";
    $block    .= "    valid users = $username\n";
    if ($share_type eq 'timemachine') {
        $block .= "    fruit:time machine = yes\n";
        $block .= "    fruit:time machine max size = 500G\n";
        $block .= "    vfs objects = catia fruit streams_xattr\n";
        $block .= "    ea support = yes\n";
    }

    # Bestehende Zeilen + neuer Block
    my $smb_conf = get_smb_conf_path();
    open(my $fh, '<', $smb_conf) or &WebminCore::error("Cannot read smb.conf: $!");
    my @existing = <$fh>;
    close($fh);
    push(@existing, split(/(?<=\n)/, $block));
    mn_write_smb_conf(\@existing);

} elsif ($mode eq 'group') {
    my $target = $in{'target_group_share'};
    my $perm   = $in{'group_perms'};
    my $key    = ($perm eq 'ro') ? 'read list' : 'valid users';

    my ($target_section) = grep { $_->{name} eq $target } @$sections_ref;
    &WebminCore::error("Share '".&WebminCore::html_escape($target)."' not found.") unless $target_section;

    my ($rw_ref, $ro_ref) = mn_get_share_users($target_section);
    my %rw_seen; my @rw = grep { !$rw_seen{$_}++ } @$rw_ref;
    my %ro_seen; my @ro = grep { !$ro_seen{$_}++ } @$ro_ref;
    if ($perm eq 'ro') { push(@ro, $username) unless grep { $_ eq $username } @ro; }
    else                { push(@rw, $username) unless grep { $_ eq $username } @rw; }

    my @new_lines;
    foreach my $s (@$sections_ref) {
        push(@new_lines, "[$s->{name}]\n");
        if ($s->{name} eq $target) {
            # Bestehende valid-users/read-list Zeilen entfernen, dann genau
            # eine konsolidierte Zeile je Schluessel neu schreiben - sonst
            # gewinnt bei Samba nur die zuletzt geschriebene Zeile und alle
            # bisherigen Mitglieder verlieren stillschweigend den Zugriff.
            foreach my $line (split(/\n/, $s->{raw})) {
                next if $line =~ /^\s*(valid users|read list)\s*=/i;
                push(@new_lines, "$line\n") if $line =~ /\S/;
            }
            push(@new_lines, "    valid users = " . join(' ', @rw) . "\n") if @rw;
            push(@new_lines, "    read list = "   . join(' ', @ro) . "\n") if @ro;
        } else {
            push(@new_lines, $s->{raw});
        }
        push(@new_lines, "\n");
    }
    mn_write_smb_conf(\@new_lines);
}

reload_samba();
write_mininas_log('USER_CREATE', "Provisioned user $username via mode $mode.");
mn_update_storage_cache();
&WebminCore::redirect('index.cgi');

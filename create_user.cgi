#!/usr/bin/perl
package main;
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

# 1. OS-User anlegen
system('useradd', '-m', '-s', '/usr/sbin/nologin', $username);
&WebminCore::error("Failed to create Linux system user '$username'. Does it already exist?")
    if $? != 0;

# 2. Samba-Passwort setzen
if (open(my $smb, '|-', 'smbpasswd', '-s', '-a', $username)) {
    print $smb "$password\n$password\n";
    close($smb);
}

my ($lines_ref, $sections_ref) = parse_smb_sections_v2();

if ($mode eq 'isolated') {
    my $base   = $in{'base_path'} || '/mnt';
    my $folder = $in{'folder_name'} || $username;
    $base =~ s{/+$}{};
    my $path = "$base/$folder";

    &WebminCore::error('Invalid base path. Only /mnt and /srv are allowed.')
        unless mn_validate_path($path);

    system('mkdir', '-p', $path);
    system('chown', "$username:sambashare", $path);
    system('chmod', '0770', $path);

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

    my @new_lines;
    foreach my $s (@$sections_ref) {
        push(@new_lines, "[$s->{name}]\n");
        if ($s->{name} eq $target) {
            push(@new_lines, $s->{raw});
            push(@new_lines, "    $key = $username\n");
        } else {
            push(@new_lines, $s->{raw});
        }
        push(@new_lines, "\n");
    }
    mn_write_smb_conf(\@new_lines);
}

reload_samba();
write_mininas_log('USER_CREATE', "Provisioned user $username via mode $mode.");
&WebminCore::redirect('index.cgi');

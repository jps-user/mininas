#!/usr/bin/perl
package main;
BEGIN { push(@INC, ".."); };
use WebminCore;
&init_config();
&ReadParse();
require 'mininas/mininas-lib.pl';

my $username = $in{'username'};
my $password = $in{'password'};
my $mode     = $in{'creation_mode'};

if (!$username || !$password) {
    &WebminCore::error("Username and Password are required.");
}

# Username-Validierung
if ($username !~ /^[a-z_][a-z0-9_-]*$/) {
    &WebminCore::error("Invalid username format. Use lowercase letters, digits, - or _.");
}

# 1. OS-User anlegen
system("useradd", "-m", "-s", "/usr/sbin/nologin", $username);
if ($? != 0) {
    &WebminCore::error("Failed to create Linux system user '$username'. Does it already exist?");
}

# 2. Samba-Passwort setzen
if (open(my $smb, "|-", "smbpasswd", "-s", "-a", $username)) {
    print $smb "$password\n$password\n";
    close($smb);
}

my $smb_conf = get_smb_conf_path();

if ($mode eq 'isolated') {
    my $base   = $in{'base_path'} || '/mnt/';   # FIX: aus Formular lesen
    my $folder = $in{'folder_name'} || $username;

    # Sicherheitsprüfung Basispfad
    $base =~ s{/+$}{};  # trailing slash entfernen
    if ($base !~ m{^/(mnt|srv)$}) {
        &WebminCore::error("Invalid base path. Only /mnt and /srv are allowed.");
    }
    my $path = "$base/$folder";

    system("mkdir", "-p", $path);
    system("chown", "$username:sambashare", $path);
    system("chmod", "0770", $path);

    &WebminCore::lock_file($smb_conf);
    system("cp", $smb_conf, "$smb_conf.bak");

    if (open(my $fh, '>>', $smb_conf)) {
        print $fh "\n[$username]\n";
        print $fh "    path = $path\n";
        print $fh "    writable = yes\n";
        print $fh "    browsable = yes\n";
        print $fh "    valid users = $username\n";
        if ($in{'share_type'} eq 'timemachine') {
            print $fh "    fruit:time machine = yes\n";
            print $fh "    fruit:time machine max size = 500G\n";
            print $fh "    vfs objects = catia fruit streams_xattr\n";
            print $fh "    ea support = yes\n";
        }
        close($fh);
    }

    system("testparm -s \Q$smb_conf\E >/dev/null 2>&1");
    if ($? != 0) {
        system("cp", "$smb_conf.bak", $smb_conf);
        unlink("$smb_conf.bak");
        &WebminCore::unlock_file($smb_conf);
        &WebminCore::error("Samba configuration check failed! Rollback applied.");
    }
    unlink("$smb_conf.bak");
    &WebminCore::unlock_file($smb_conf);

} elsif ($mode eq 'group') {
    my $target = $in{'target_group_share'};
    my $perm   = $in{'group_perms'};
    my $key    = ($perm eq 'ro') ? "read list" : "valid users";

    my ($lines_ref, $sections_ref) = parse_smb_sections_v2();
    my @new_lines;

    foreach my $s (@$sections_ref) {
        push(@new_lines, "[$s->{name}]\n");
        if ($s->{name} eq $target) {
            foreach my $l (split("\n", $s->{raw})) {
                push(@new_lines, "$l\n");
            }
            push(@new_lines, "    $key = $username\n");
        } else {
            push(@new_lines, $s->{raw});
        }
    }

    &WebminCore::lock_file($smb_conf);
    system("cp", $smb_conf, "$smb_conf.bak");

    if (open(my $wfh, '>', $smb_conf)) {
        print $wfh join('', @new_lines);
        close($wfh);
    } else {
        system("cp", "$smb_conf.bak", $smb_conf);
        unlink("$smb_conf.bak");
        &WebminCore::unlock_file($smb_conf);
        &WebminCore::error("Failed to write smb.conf: $!");
    }

    system("testparm -s \Q$smb_conf\E >/dev/null 2>&1");
    if ($? != 0) {
        system("cp", "$smb_conf.bak", $smb_conf);
        unlink("$smb_conf.bak");
        &WebminCore::unlock_file($smb_conf);
        &WebminCore::error("Samba configuration check failed after adding user to group! Rollback applied.");
    }
    unlink("$smb_conf.bak");
    &WebminCore::unlock_file($smb_conf);
}

reload_samba();
write_mininas_log("USER_CREATE", "Provisioned user $username via mode $mode.");
&WebminCore::redirect("index.cgi");

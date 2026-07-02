#!/usr/bin/perl
package main;
BEGIN { push(@INC, ".."); };
use WebminCore;
&init_config();
&ReadParse();
require 'mininas/mininas-lib.pl';

my $u    = $in{'user'};
my $mode = $in{'delete_mode'};

if (!$u) { &WebminCore::error("No user specified."); }
if ($u !~ /^[a-z_][a-z0-9_-]*$/) { &WebminCore::error("Invalid username format."); }

# 1. User aus smb.conf austragen (1-per-line)
my $smb_conf = get_smb_conf_path();
if (open(my $fh, '<', $smb_conf)) {
    my @lines = <$fh>;
    close($fh);

    my @new_lines;
    foreach my $line (@lines) {
        if ($line =~ /^\s*(valid users|read list)\s*=\s*(.*)/i) {
            my $type  = $1;
            my $src   = $2;
            my @clean = grep { $_ ne $u } split(/[\s,]+/, $src);
            foreach my $r (@clean) {
                push(@new_lines, "    $type = $r\n");    # 4 Leerzeichen
            }
        } else {
            push(@new_lines, $line);
        }
    }

    # FIX (Gemini Punkt 2): lock_file
    &WebminCore::lock_file($smb_conf);
    if (open(my $wfh, '>', $smb_conf)) {
        print $wfh join('', @new_lines);
        close($wfh);
        &WebminCore::unlock_file($smb_conf);
    } else {
        &WebminCore::unlock_file($smb_conf);
        &WebminCore::error("Failed to write smb.conf: $!");
    }
}

# 2. OS-Deletion NUR bei full_cleanup
if ($mode eq 'full_cleanup') {
    system("smbpasswd", "-x", $u);
    system("userdel", "-r", $u);
    write_mininas_log("USER_DELETE", "Full cleanup: $u removed from OS and config.");
} else {
    system("smbcontrol", "smbd", "close-share", $u);
    write_mininas_log("USER_DELETE", "Config-only: $u removed from smb.conf, OS user kept.");
}

reload_samba();
&WebminCore::redirect("index.cgi");

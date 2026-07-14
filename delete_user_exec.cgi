#!/usr/bin/perl
package main;
BEGIN { push(@INC, '..'); }
use WebminCore;
&init_config();
&ReadParse();
require 'mininas/mininas-lib.pl';

my $u    = $in{'user'};
my $mode = $in{'delete_mode'};

&WebminCore::error('No user specified.')      unless $u;
&WebminCore::error('Invalid username format.') unless mn_validate_username($u, 0);

# 1. User aus smb.conf entfernen
mn_remove_user_from_conf($u)
    or &WebminCore::error("Failed to update smb.conf for user '$u'.");

# 2. OS-Deletion nur bei full_cleanup
if ($mode eq 'full_cleanup') {
    mn_delete_os_user($u);
    write_mininas_log('USER_DELETE', "Full cleanup: $u removed from OS and config.");
} else {
    system('smbcontrol', 'smbd', 'close-share', $u);
    write_mininas_log('USER_DELETE', "Config-only: $u removed from smb.conf, OS user kept.");
}

reload_samba();
&WebminCore::redirect('index.cgi');

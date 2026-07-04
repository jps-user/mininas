#!/usr/bin/perl
package main;
BEGIN { push(@INC, '..'); }
use WebminCore;
&init_config();
&ReadParse();
require 'mininas/mininas-lib.pl';

my $u = $in{'user'};
&WebminCore::error('No user specified.') unless $u;
&WebminCore::error('Invalid username format.') unless mn_validate_username($u, 1);

mn_remove_user_from_conf($u)
    or &WebminCore::error("Failed to update smb.conf for user '$u'.");

reload_samba();
write_mininas_log('GHOST_CLEAN', "Removed ghost user $u from smb.conf.");
&WebminCore::redirect('index.cgi');

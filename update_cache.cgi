#!/usr/bin/perl
# update_cache.cgi - Weckt Disks explizit und misst Füllstände neu (AJAX vom Dashboard "Wake & measure").
package main;
BEGIN { push(@INC, "..") }
use WebminCore;
&init_config();
require 'mininas/mininas-lib.pl';

my $ok = mn_update_storage_cache();
write_mininas_log('CACHE_UPDATE', 'Manual "Wake & measure" triggered.') if $ok;

my $cache = mn_read_storage_cache();
my $ts = $cache->{timestamp} || '';
$ts =~ s/([\\"])/\\$1/g;

print "Content-type: application/json\n\n";
print "{\"ok\":" . ($ok ? 1 : 0) . ",\"timestamp\":\"$ts\"}";

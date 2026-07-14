#!/usr/bin/perl
# testparm.cgi - Prüft smb.conf Syntax und gibt JSON zurück (für AJAX-Aufruf vom Dashboard)
package main;
BEGIN { push(@INC, "..") }
use WebminCore;
&init_config();
require 'mininas/mininas-lib.pl';

my ($ok, $output) = mn_testparm();

my $summary = $ok ? 'Loaded services file OK' : 'Syntax error in smb.conf';
if ($output =~ /(WARNING:.+)/i) { $summary = $1; }

# Sauberes JSON-Escaping
$summary =~ s/([\\"])/\\$1/g;
$summary =~ s/\n/ /g;

print "Content-type: application/json\n\n";
print "{\"ok\":" . ($ok ? 1 : 0) . ",\"summary\":\"$summary\"}";

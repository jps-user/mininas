#!/usr/bin/perl
# testparm.cgi - Prüft smb.conf Syntax und gibt JSON zurück (für AJAX-Aufruf vom Dashboard)
package main;
BEGIN { push(@INC, ".."); };
use WebminCore;
&init_config();
require 'mininas/mininas-lib.pl';

my $smb_conf = get_smb_conf_path();
my $output = `testparm -s \Q$smb_conf\E 2>&1`;
my $ok = ($? == 0) ? 1 : 0;

# Kurzfassung der wichtigsten Zeile extrahieren
my $summary = $ok ? "Loaded services file OK" : "Syntax error in smb.conf";
if ($output =~ /(WARNING:.+)/i) { $summary = $1; }

# Sauberes JSON-Escaping (statt quotemeta, das auch Leerzeichen escaped)
$summary =~ s/([\\"])/\\$1/g;
$summary =~ s/\n/ /g;

print "Content-type: application/json\n\n";
print "{\"ok\":".($ok?1:0).",\"summary\":\"$summary\"}";

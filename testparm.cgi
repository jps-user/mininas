#!/usr/bin/perl
# testparm.cgi - Prüft smb.conf Syntax und gibt JSON zurück (für AJAX-Aufruf vom Dashboard)

package main;
use strict;
use warnings;
BEGIN { push(@INC, ".."); }
use WebminCore;
require 'mininas/mininas-init.pl';
use JSON::PP;

my ($ok, $output) = mn_testparm();

my $summary = $ok ? 'Loaded services file OK' : 'Syntax error in smb.conf';
if ($output =~ /(WARNING:.+)/i) { $summary = $1; }
$summary =~ s/\n/ /g;

print "Content-type: application/json\n\n";
print encode_json({ ok => ($ok ? JSON::PP::true : JSON::PP::false), summary => $summary });

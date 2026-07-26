#!/usr/bin/perl
package main;
use strict;
use warnings;
BEGIN { push(@INC, ".."); }
use WebminCore;
require 'mininas/mininas-init.pl';

reload_samba();
write_mininas_log("RELOAD", "Samba configuration reloaded manually.");
&WebminCore::redirect("index.cgi");

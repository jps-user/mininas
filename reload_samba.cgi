#!/usr/bin/perl
package main;
BEGIN { push(@INC, ".."); };
use WebminCore;
&init_config();
require 'mininas/mininas-lib.pl';
reload_samba();
write_mininas_log("RELOAD", "Samba configuration reloaded manually.");
&WebminCore::redirect("index.cgi");

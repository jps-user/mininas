# /usr/share/webmin/mininas/mininas-init.pl
use strict;
use warnings;
BEGIN { push(@INC, ".."); };
use WebminCore;
&init_config();
require './mininas-lib.pl';
1;
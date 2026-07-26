# /usr/share/webmin/mininas/mininas-init.pl
#
# Zentraler Einstiegspunkt fuer alle MiniNAS CGI-Skripte. Buendelt das
# wiederkehrende Boilerplate (WebminCore laden, Charset, Config/Parse-Init,
# Lib-Requires) an einer Stelle statt es in jeder .cgi zu wiederholen.
#
# WICHTIG (Perl-Semantik): "use strict;" und "use warnings;" sind
# datei-/blocklokale Compile-Pragmas und werden NICHT ueber require an den
# Aufrufer weitergereicht. Jede .cgi-Datei muss sie daher weiterhin selbst
# deklarieren - siehe Standard-Header unten. Ebenso muss der @INC-Push
# (BEGIN { push(@INC, ".."); }) in jeder .cgi VOR diesem require stehen,
# da genau dieser Pfad noetig ist, um "mininas/mininas-init.pl" ueberhaupt
# zu finden.
package main;
use WebminCore;
$main::default_charset = 'utf-8';
&init_config();
&ReadParse();
require 'mininas/mininas-lib.pl';
require 'mininas/ui_components.pl';
1;

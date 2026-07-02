#!/usr/bin/perl
package main;
BEGIN { push(@INC, ".."); };
use WebminCore;
&init_config();
&ReadParse();
require 'mininas/mininas-lib.pl';

my $u        = $in{'user'};
my $smb_conf = get_smb_conf_path();

if (open(my $fh, '<', $smb_conf)) {
    my @lines = <$fh>;
    close($fh);

    my @new_lines;
    foreach my $line (@lines) {
        if ($line =~ /^\s*(valid users|read list)\s*=\s*(.*)/i) {
            my $type  = $1;
            my $src   = $2;
            my @clean = grep { $_ ne $u } split(/[\s,]+/, $src);
            foreach my $r (@clean) {
                push(@new_lines, "    $type = $r\n");    # 4 Leerzeichen
            }
            # Leere Zeile fällt weg - korrekt
        } else {
            push(@new_lines, $line);
        }
    }

    # FIX (Gemini Punkt 2): lock_file
    &WebminCore::lock_file($smb_conf);
    if (open(my $wfh, '>', $smb_conf)) {
        print $wfh join('', @new_lines);
        close($wfh);
        &WebminCore::unlock_file($smb_conf);
        reload_samba();
    } else {
        &WebminCore::unlock_file($smb_conf);
    }
}

write_mininas_log("GHOST_CLEAN", "Removed ghost user $u from smb.conf.");
&WebminCore::redirect("index.cgi");

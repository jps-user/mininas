#!/usr/bin/perl
use WebminCore;

sub get_smb_conf_path { return "/etc/samba/smb.conf"; }

sub parse_smb_sections_v2 {
    my $path = get_smb_conf_path();
    my @lines;
    if (open(my $fh, '<', $path)) { @lines = <$fh>; close($fh); }

    my @sections;
    my $current = undef;

    foreach my $line (@lines) {
        if ($line =~ /^\s*\[([^\]]+)\]/) {
            $current = { name => $1, raw => "" };
            push(@sections, $current);
        } elsif ($current) {
            $current->{raw} .= $line;
        }
    }
    return (\@lines, \@sections);
}

sub reload_samba {
    system("smbcontrol all reload-config >/dev/null 2>&1");
    system("systemctl reload smbd >/dev/null 2>&1");
}

sub write_mininas_log {
    my ($action, $msg) = @_;
    my $logfile = "/var/log/mininas.log";
    if (open(my $fh, '>>', $logfile)) {
        my $ts = scalar localtime();
        print $fh "[$ts] [$action] $msg\n";
        close($fh);
    }
}
1;
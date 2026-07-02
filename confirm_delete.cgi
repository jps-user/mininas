#!/usr/bin/perl
package main;
BEGIN { push(@INC, ".."); };
use WebminCore;
&init_config();
&ReadParse();
require 'mininas/mininas-lib.pl';
require 'mininas/ui_components.pl';

if (defined($in{'cancel'})) {
    &WebminCore::redirect("index.cgi");
    exit;
}

my $sec_name = $in{'section'};
my $mode     = $in{'delete_mode'};

if (!$sec_name) { &WebminCore::error("Missing section name."); }

&WebminCore::ui_print_header(undef, "Deleting Share...", "", undef, 0, 0);
print mn_head();
print "<div class='mn-wrap'>";
print "<div class='mn-page-header'>";
print "<span class='mn-page-title'><i class='ti ti-trash' style='color:var(--mn-red); margin-right:8px;'></i>Deleting: $sec_name</span>";
print "</div>";

print "<div class='mn-section'>";
print "<div class='mn-section-head'><i class='ti ti-loader-2' style='font-size:13px;'></i> Processing</div>";
print "<div style='padding:16px;' id='progress'>";

my ($lines_ref, $sections_ref) = parse_smb_sections_v2();
my ($target) = grep { $_->{name} eq $sec_name } @$sections_ref;

sub step_ok  { print "<div style='padding:5px 0; color:var(--mn-green);'><i class='ti ti-circle-check'></i> $_[0]</div>\n"; }
sub step_err { print "<div style='padding:5px 0; color:var(--mn-red);'><i class='ti ti-alert-circle'></i> $_[0]</div>\n"; }

if ($target) {
    my $path = ($target->{raw} =~ /path\s*=\s*([^\n]*)/) ? $1 : "";
    $path =~ s/^\s+|\s+$//g;

    if ($mode eq "full_cleanup") {
        if ($path =~ /^\/(mnt|srv)\/[a-zA-Z0-9_\-]+$/ && -d $path) {
            system("rm", "-rf", $path);
            $? == 0 ? step_ok("Directory removed: $path") : step_err("Could not remove directory: $path");
        }

        my %users_to_wipe;
        while ($target->{raw} =~ /^\s*(?:valid users|read list)\s*=\s*([^\n]+)/gim) {
            foreach my $u (split(/[\s,]+/, $1)) {
                $u =~ s/^\s+|\s+$//g;
                $users_to_wipe{$u} = 1 if ($u && $u !~ /^@/);
            }
        }
        foreach my $u (sort keys %users_to_wipe) {
            if ($u =~ /^[a-z_][a-z0-9_-]*$/) {
                system("smbpasswd", "-x", $u);
                system("userdel", "-r", $u);
                step_ok("User removed: $u");
            }
        }
    }
}

# Sektion aus smb.conf entfernen
my $smb_conf = get_smb_conf_path();
if (open(my $fh, '<', $smb_conf)) {
    my @lines = <$fh>;
    close($fh);
    my @new_lines;
    my $inside = 0;
    foreach my $line (@lines) {
        if ($line =~ /^\s*#\s*BEGIN\s+MININAS\s+SHARE\s+\Q$sec_name\E/i) { $inside=1; next; }
        if ($inside==1 && $line =~ /^\s*#\s*END\s+MININAS\s+SHARE\s+\Q$sec_name\E/i) { $inside=0; next; }
        if (!$inside && $line =~ /^\s*\[\Q$sec_name\E\]/i && $sec_name ne "global") { $inside=2; next; }
        if ($inside==2 && $line =~ /^\s*\[/) { $inside=0; }
        push(@new_lines, $line) unless $inside;
    }
    &WebminCore::lock_file($smb_conf);
    if (open(my $wfh, '>', $smb_conf)) {
        print $wfh join('', @new_lines);
        close($wfh);
        &WebminCore::unlock_file($smb_conf);
        step_ok("Configuration updated");
    } else {
        &WebminCore::unlock_file($smb_conf);
        step_err("Error writing smb.conf: $!");
    }
} else {
    step_err("Error opening smb.conf: $!");
}

write_mininas_log("DELETED", "Share '$sec_name' removed (Mode: $mode)");
reload_samba();
step_ok("Samba reloaded");

print "</div>";
print "<div style='padding:0 16px 16px;'>";
print "<a href='index.cgi' class='mn-btn mn-btn-primary'><i class='ti ti-arrow-left'></i> Back to Dashboard</a>";
print "</div>";
print "</div>";
print "</div>";
&WebminCore::ui_print_footer("/", "Return to Webmin");

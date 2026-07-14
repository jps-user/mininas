#!/usr/bin/perl
package main;
BEGIN { push(@INC, '..'); }
use WebminCore;
&init_config();
&ReadParse();
require 'mininas/mininas-lib.pl';
require 'mininas/ui_components.pl';

&WebminCore::redirect('index.cgi') if defined $in{'cancel'};

my $sec_name = $in{'section'};
my $mode     = $in{'delete_mode'};
&WebminCore::error('Missing section name.') unless $sec_name;

&WebminCore::ui_print_header(undef, 'Deleting Share...', '', undef, 0, 0);
print mn_head();
print "<div class='mn-wrap'>";
print "<div class='mn-page-header'>";
print "<span class='mn-page-title'><i class='ti ti-trash' style='color:var(--mn-red); margin-right:8px;'></i>Deleting: $sec_name</span>";
print "</div>";
print "<div class='mn-section'>";
print "<div class='mn-section-head'><i class='ti ti-loader-2' style='font-size:13px;'></i> Processing</div>";
print "<div style='padding:16px;'>";

sub step_ok  { print "<div style='padding:5px 0; color:var(--mn-green);'><i class='ti ti-circle-check'></i> $_[0]</div>\n"; }
sub step_err { print "<div style='padding:5px 0; color:var(--mn-red);'><i class='ti ti-alert-circle'></i> $_[0]</div>\n"; }

my ($lines_ref, $sections_ref) = parse_smb_sections_v2();
my ($target) = grep { $_->{name} eq $sec_name } @$sections_ref;

if ($target && $mode eq 'full_cleanup') {
    my $path = mn_get_share_path($target);

    if ($path && mn_validate_path($path) && -d $path) {
        system('rm', '-rf', $path);
        $? == 0 ? step_ok("Directory removed: $path")
                : step_err("Could not remove directory: $path");
    }

    # Alle User dieser Sektion sammeln und löschen
    my %users_to_wipe;
    while ($target->{raw} =~ /^\s*(?:valid users|read list)\s*=\s*([^\n]+)/gim) {
        foreach my $u (split(/[\s,]+/, $1)) {
            $u =~ s/^\s+|\s+$//g;
            $users_to_wipe{$u} = 1 if ($u && $u !~ /^@/);
        }
    }
    foreach my $u (sort keys %users_to_wipe) {
        next unless mn_validate_username($u, 0);
        mn_delete_os_user($u);
        step_ok("User removed: $u");
    }
}

# Sektion aus smb.conf entfernen
my @new_lines;
my $inside = 0;
my $smb_conf = get_smb_conf_path();
if (open(my $fh, '<', $smb_conf)) {
    my @lines = <$fh>;
    close($fh);
    foreach my $line (@lines) {
        if (!$inside && $line =~ /^\s*\[\Q$sec_name\E\]/i && $sec_name ne 'global') {
            $inside = 1; next;
        }
        if ($inside && $line =~ /^\s*\[/) { $inside = 0; }
        push(@new_lines, $line) unless $inside;
    }
}

&WebminCore::lock_file($smb_conf);
if (open(my $wfh, '>', $smb_conf)) {
    print $wfh join('', @new_lines);
    close($wfh);
    &WebminCore::unlock_file($smb_conf);
    step_ok('Configuration updated');
} else {
    &WebminCore::unlock_file($smb_conf);
    step_err("Error writing smb.conf: $!");
}

write_mininas_log('DELETED', "Share '$sec_name' removed (mode: $mode).");
reload_samba();
step_ok('Samba reloaded');
mn_update_storage_cache();

print "</div>";
print "<div style='padding:0 16px 16px;'>";
print "<a href='index.cgi' class='mn-btn mn-btn-primary'><i class='ti ti-arrow-left'></i> Back to Dashboard</a>";
print "</div></div></div>";
&WebminCore::ui_print_footer('/', 'Return to Webmin');

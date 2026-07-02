#!/usr/bin/perl
package main;
BEGIN { push(@INC, ".."); };
use WebminCore;
&init_config();
&ReadParse();
require 'mininas/mininas-lib.pl';

if ($in{'cancel'}) {
    &WebminCore::redirect("index.cgi");
    exit;
}

my $u = $in{'user'};
if (!$u) { &WebminCore::error("No user specified."); }

my ($lines_ref, $sections_ref) = parse_smb_sections_v2();

foreach my $s (@$sections_ref) {
    next if $s->{name} eq "global";

    my $share_name = $s->{name};
    my $is_active  = $in{"share_active_$share_name"};
    my $perm_mode  = $in{"perm_mode_$share_name"} || "rw";

    # 1. User aus allen Zeilen dieser Sektion entfernen (1-per-line: ganzen Match löschen)
    my @new_lines;
    foreach my $line (split(/\n/, $s->{raw})) {
        if ($line =~ /^\s*(valid users|read list)\s*=\s*.*\b\Q$u\E\b/i) {
            next;    # Zeile für diesen User löschen
        }
        push(@new_lines, $line);
    }

    # 2. Falls aktiv: User als saubere eigene Zeile(n) einfügen
    if ($is_active) {
        push(@new_lines, "   valid users = $u");
        if ($perm_mode eq "ro") {
            push(@new_lines, "   read list = $u");
        }
    }

    $s->{raw} = join("\n", @new_lines);
}

# 3. FIX: get_smb_conf_path() statt $config{'smb_conf'}
my $conf_path = get_smb_conf_path();
my $tmp_path  = "$conf_path.tmp";

&WebminCore::lock_file($conf_path);
if (open(my $fh, '>', $tmp_path)) {
    foreach my $s (@$sections_ref) {
        print $fh "[$s->{name}]\n$s->{raw}\n\n";
    }
    close($fh);
    rename($tmp_path, $conf_path);
} else {
    &WebminCore::unlock_file($conf_path);
    &WebminCore::error("Failed to write config: $!");
}
&WebminCore::unlock_file($conf_path);

reload_samba();
write_mininas_log("SHARES_SAVE", "Updated share permissions for user $u.");
&WebminCore::redirect("index.cgi");

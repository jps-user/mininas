#!/usr/bin/perl
package main;
BEGIN { push(@INC, '..'); }
use WebminCore;
&init_config();
&ReadParse();
require 'mininas/mininas-lib.pl';

sub json_ok  { my $m=shift; $m=~s/(["\\])/\\$1/g; print "Content-type: application/json\n\n{\"ok\":1,\"msg\":\"$m\"}"; exit; }
sub json_err { my $m=shift; $m=~s/(["\\])/\\$1/g; print "Content-type: application/json\n\n{\"ok\":0,\"msg\":\"$m\"}"; exit; }

my $sec  = $in{'section'};
my $own  = $in{'owner'};
my $grp  = $in{'group'};
my $mode = $in{'mode'};

json_err('No section specified.')              unless $sec;
json_err('Invalid owner format.')              unless mn_validate_username($own, 1);
json_err('Invalid group format.')              unless mn_validate_username($grp, 1);
json_err('Invalid mode (use 4 digits 0-7).')   unless $mode =~ /^[0-7]{4}$/;

my ($lines_ref, $sections_ref) = parse_smb_sections_v2();
my ($target) = grep { $_->{name} eq $sec } @$sections_ref;
json_err("Section '$sec' not found.") unless $target;

my $path = mn_get_share_path($target);
json_err('Path not found in config.')          unless $path;
json_err("Path '$path' does not exist.")       unless -d $path;
json_err("Path '$path' outside allowed directories (/mnt, /srv).")
    unless mn_validate_path($path);

system('chown', "$own:$grp", $path);
json_err("chown $own:$grp failed. Do user and group exist?") if $? != 0;

system('chmod', $mode, $path);
json_err("chmod $mode failed.") if $? != 0;

my @st        = stat($path);
my $new_mode  = sprintf('%04o', $st[2] & 07777);
my $new_owner = (getpwuid($st[4]))[0] || $st[4];
my $new_group = (getgrgid($st[5]))[0] || $st[5];

write_mininas_log('SET_PERMS', "Set $path: $own:$grp $mode");
json_ok("$new_mode $new_owner:$new_group");

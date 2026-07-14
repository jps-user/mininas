#!/usr/bin/perl
package main;
BEGIN { push(@INC, ".."); };
use WebminCore;
&init_config();

my @users;
if (open(my $fh, '<', '/etc/passwd')) {
    while (<$fh>) {
        my ($u, undef, $uid) = split(':');
        push(@users, $u) if defined $uid && $uid >= 0;
    }
    close($fh);
}

my @groups;
if (open(my $fh, '<', '/etc/group')) {
    while (<$fh>) {
        my ($g) = split(':');
        push(@groups, $g) if $g;
    }
    close($fh);
}

sub json_arr {
    my @items = @_;
    my $j = join(",", map { s/(["\\])/\\$1/g; "\"$_\"" } @items);
    return "[$j]";
}

print "Content-type: application/json\n\n";
print "{\"users\":".json_arr(@users).",\"groups\":".json_arr(@groups)."}";

#!/usr/bin/perl
package main;
use strict;
use warnings;
BEGIN { push(@INC, ".."); }
use WebminCore;
require 'mininas/mininas-init.pl';
use JSON::PP;

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

print "Content-type: application/json\n\n";
print encode_json({ users => \@users, groups => \@groups });

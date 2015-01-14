#!/usr/bin/env perl

use strict;

# Use mg-biom-view to implement the transform.
# mg-biom-view accepts -i/--input -o/--output on command line to specify input / output.

my @cmd = ("mg-biom-view", @ARGV);
my $rc = system(@cmd);

if ($rc != 0)
{
    die "Transform command failed with rc=$rc: @cmd\n";
}

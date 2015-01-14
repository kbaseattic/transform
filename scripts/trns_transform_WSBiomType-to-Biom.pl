#!/usr/bin/env perl

use strict;
use Getopt::Long;

my $biom_object_file = "";
my $biom_output_file = "";

GetOptions("input|i=s" => \$biom_object_file,
           "output|o=s" => \$biom_output_file);

my @cmd = ("mv", $biom_object_file, $biom_output_file);
my $rc = system(@cmd);

if ($rc != 0)
{
    die "Transform command failed with rc=$rc: @cmd\n";
}

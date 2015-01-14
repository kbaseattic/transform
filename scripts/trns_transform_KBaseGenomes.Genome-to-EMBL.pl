use strict;

#
# Use rast-export-genome to implement the transform. If -i / -o passed on command line
# these will pass to rast-export-genome to change input / output. Otherwise defaults to
# stdin / stdout.
#

my @cmd = ("rast-export-genome", 'embl', @ARGV);
my $rc = system(@cmd);

if ($rc != 0)
{
    die "Transform command failed with rc=$rc: @cmd\n";
}

use strict;
use Bio::KBase::Transform::Client;
use Test::More tests => 3;
use Data::Dumper;
use Test::Cmd;
use JSON;


my $ws_id="loader_test";
my $in_id = "Loader.csv-1.0";
my $out_id = "test_pair2";
my $cc = Bio::KBase::Transform::Client->new("http://localhost:7778");

print "This test requires the $in_id is stored in $ws_id(workspace)\n";
print "It also requires read and write ability in the $ws_id(workspace)\n";
ok( defined $cc, "Check if the server is working" );

#my $job_id = $cc->validate({ws_id => $ws_id, inobj_id => $in_id, outobj_id => $out_id});
my $job_id = $cc->validate({etype => $in_id, id => "d3eecb7f-5b52-4b63-9871-62ecedfd149e"});
ok(ref($job_id) eq "ARRAY","mys_example returns an array");
ok(@{$job_id} eq 2, "returns two job ids for mys_example");

# TODO: wait job to be done

# TODO: check the internal value to be correct

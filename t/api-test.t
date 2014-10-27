use strict;
use Bio::KBase::Loader::Client;
use Test::More tests => 3;
use Data::Dumper;
use Test::Cmd;
use JSON;


my $ws_id="kbasetest:home";
my $in_id = "test_pair";
my $out_id = "test_pair2";
my $cc = Bio::KBase::Loader::Client->new("http://localhost:7777");

print "This test requires the $in_id is stored in $ws_id(workspace)\n";
print "It also requires read and write ability in the $ws_id(workspace)\n";
ok( defined $cc, "Check if the server is working" );

my $job_id = $cc->mys_example({ws_id => $ws_id, inobj_id => $in_id, outobj_id => $out_id, p_value => "0.05", method => "anova"});
ok(ref($job_id) eq "ARRAY","mys_example returns an array");
ok(@{$job_id} eq 2, "returns two job ids for mys_example");

# TODO: wait job to be done

# TODO: check the internal value to be correct

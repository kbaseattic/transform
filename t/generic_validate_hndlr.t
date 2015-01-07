use strict;
use Bio::KBase::Transform::Client;
use Test::More tests => 3;
use Data::Dumper;
use Test::Cmd;
use JSON;
use Bio::KBase::userandjobstate::Client;
use Bio::KBase::AuthToken;
use Bio::KBase::workspace::Client;

#authors:
#Fei He(plane83@gmail.com)
#Shinjae Yoo(sjyoo@bnl.gov)

#created: Nov. 24, 2014
#updated: Dec. 08, 2014


#This is a script to test the API of transform service.
#it assume a data file have already been stored in SHOCK
#it checks if a new workspace object has been created in the right workspace by 'upload'.
#it checks if a shock node stores a gene bank file in the right format
#...
#it roughly checks if the new objects are as expected, but it does not check any possible error in the data conversion
die "Usage: generic_upload.t <input_test_config_filename>" if $#ARGV != 0;

my $cfg_fn = $ARGV[0];

open CFG, "$cfg_fn" or die "Couldn't open $cfg_fn\n";
my @lines = <CFG>;
my $cfg_json = join ' ', @lines;
my $conf = from_json($cfg_json);
note($conf->{test_name}) if defined $conf->{test_name};

## Parameter setting up...
my $transform_url="http://127.0.0.1:7778";
$transform_url = $conf->{test_server_url} if defined $conf->{test_server_url};
$transform_url = $ENV{TEST_SERVER_URL} if defined $ENV{TEST_SERVER_URL};

my $ujs_url = "http://10.1.16.87:7083";
$ujs_url = $conf->{ujs_url} if defined $conf->{ujs_url};
$ujs_url = $ENV{UJS_URL} if defined $ENV{UJS_URL};

my $check_interval = 3;
$check_interval = $conf->{check_interval} if defined $conf->{check_interval};

my $max_iter = 100;
$max_iter = $conf->{max_wait_sec} / $check_interval if defined $conf->{max_wait_sec};

# for now, it test only one node
my $in_id =  "";
$in_id = $conf->{input_data_url}[0] if defined $conf->{input_data_url};
#$in_id = join /,/ @{$conf->{input_data_url}};
if ($in_id eq "") {
	print STDERR "CRITICAL: input_data_url is not defined\n";
	exit(1);
}


my $etype = "";
$etype = $conf->{external_type} if $conf->{external_type};
if ($etype eq "") {
	print STDERR "CRITICAL: external_type is not defined\n";
	exit(2);
}

my $opt_args = "{}";
$opt_args = $conf->{optional_args} if $conf->{optional_args};


## Setup clients
#my $cc = Bio::KBase::Transform::Client->new($transform_url);
ok(defined $cc, "Transform server is working");

#my $uc = Bio::KBase::userandjobstate::Client->new($ujs_url);
ok(defined $uc, "ujs server is working");

## Execute validation
#my $job_id = $cc->validate({etype => $etype, in_id => $in_id, "optional_args" => $opt_args});

my $rst = `trns_validate_hndlr -u ws_url -x svc_ws_name -c config_obj -s shock_url -i $in_id -r $ujs_url -e $etype -a $opt_args`;

## Result checking
$check = 1;
$check = 0 if $? >> 8 == 0;
ok($check==$conf->{expected_result}, "validattion test for the data for $in_id successfully\n");

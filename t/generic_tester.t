use strict;
use Bio::KBase::Transform::Client;
use Test::More;# tests => 3;
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
die "Usage: generic_tester.t <input_test_server_config_filename> <input_test_config_filename> <function> <mode> " if $#ARGV != 3;

my %params;
if ($ARGV[0] ne "") {  
	my %Config = ();
	tie %Config, "Config::Simple", $ARGV[0];
	my $service = "Transform";
	my @list = grep /^$service\./, sort keys %Config;
	for my $k (@list) {
		my $v = $Config{$k};
		$k =~ m/^$service\.(.*)$/;
		if ($v) {
			$params{$1} = $v;
		}
	}
}

# set default values for testing
#$params{ujs_url} = 'http://localhost:7083' if! defined $params{ujs_url};
$params{ws_url} = 'http://localhost:7058' if! defined $params{ws_url};
$params{shock_url} = 'http://localhost:7078' if! defined $params{shock_url};
$params{awe_url} = 'http://localhost:7080' if! defined $params{awe_url};
$params{svc_ws_un} = 'kbasetest' if! defined $params{svc_ws_un};
$params{svc_ws_name} = 'loader_test' if! defined $params{svc_ws_name};
$params{svc_ws_cfg_name} = 'script_configs' if! defined $params{svc_ws_cfg_name};

my $cfg_fn = $ARGV[1];

my $function = $ARGV[2];
my $mode = $ARGV[3];

if ($mode ne "client" and $mode ne "hndlr") {
	$mode = "hndlr";
	print STDERR "WARNING: mode to be enforced to hdnlr\n";
}

if ($function ne "upload" and $function ne "validate" and $function ne "donwload") {
	$function = "upload";
	print STDERR "WARNING: function to be enforced to upload test\n";
}


open CFG, "$cfg_fn" or die "Couldn't open $cfg_fn\n";
my @lines = <CFG>;
my $cfg_json = join ' ', @lines;
my $conf = from_json($cfg_json);
note($conf->{test_name}) if defined $conf->{test_name};

## Parameter setting up...
my $transform_url="http://127.0.0.1:7778";
$transform_url = $conf->{test_server_url} if defined $conf->{test_server_url};
$transform_url = $ENV{TEST_SERVER_URL} if defined $ENV{TEST_SERVER_URL};

my $ujs_url = 'http://localhost:7083';
$ujs_url = $conf->{ujs_url} if defined $conf->{ujs_url};
$ujs_url = $params{ujs_url} if defined $params{ujs_url};
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

my $kb_type = "";
$kb_type = $conf->{kbase_type} if $conf->{kbase_type};
if ($kb_type eq "" and $function eq "upload") {
	print STDERR "CRITICAL: kbase_type is not defined\n";
	exit(3);
}

my $ws_name = "";
$ws_name = $conf->{ws_name} if $conf->{ws_name};
if ($ws_name eq "" and $function eq "upload") {
	print STDERR "CRITICAL: ws_name is not defined\n";
	exit(4);
}

my $obj_name = "";
$obj_name = $conf->{obj_name} if $conf->{obj_name};
if ($obj_name eq "" and $function eq "upload") {
	print STDERR "CRITICAL: obj_name is not defined\n";
	exit(5);
}

my $opt_args = "{}";
$opt_args = $conf->{optional_args} if $conf->{optional_args};

my $check = 0;
## Setup clients
if ($mode eq "client") {
	my $cc = Bio::KBase::Transform::Client->new($transform_url);
	ok(defined $cc, "Transform server is working");

	my $uc = Bio::KBase::userandjobstate::Client->new($ujs_url);
	ok(defined $uc, "ujs server is working");

## Execute validation
	my $job_id = [];
	if( $function eq "upload") {
        $job_id = $cc->upload( 
			{etype => $etype, 
			kb_type => $kb_type, 
			ws_name => $ws_name, 
			obj_name => $obj_name, 
			in_id => $in_id, 
			optional_args => $opt_args}
			);
	} elsif ($function eq "validate") {
	} elsif ($function eq "download") {
		$job_id = $cc->validate({etype => $etype, in_id => $in_id, "optional_args" => $opt_args});
	} else {
		# this should not be happen because of the above parameter settings
	}

	my $jid = $job_id->[1];
	my $i=0;
	$check=255;
	while($i < $max_iter && $check ==255){
		$i++;
		note("PROGRESS: checking job status for $jid: $i... \n");
		my @ress=$uc->get_job_status($jid);
		print "@ress\n";
		sleep $check_interval;
		my $line=join "",@ress;
		if($line =~/Succeed/i){
			$check=1;
		}
		elsif ($line =~/Fail/i or $line =~/error/i) {
			$check=0;
		}
	}

} else { # it has to be hndlr
	my $rst = '';
	if( $function eq "upload") {
		$rst = `trns_upload_hndlr -u $params{ws_url} -x $params{svc_ws_name} -c $params{svc_ws_cfg_name} -s $params{shock_url} -i $in_id -w $ws_name -o $obj_name -e $etype -t $kb_type -a $opt_args 2>&1`;
	}elsif( $function eq "download") {
		$rst = `date`; # do nothing yet
	}elsif( $function eq "validate") {
		$rst = `trns_validate_hndlr -u $params{ws_url} -x $params{svc_ws_name} -c $params{svc_ws_cfg_name} -s $params{shock_url} -i $in_id -r $ujs_url -e $etype -a $opt_args 2>&1`;
	} else {
		# this should not be happen because of the above parameter settings
	}

	print "======Output Dump======\n";
	print $rst;
	print "\n=======================\n$?\n";

## Result checking
	$check = 0;
	$check = 1 if $? == 0;
}
## Result checking
ok($check==$conf->{expected_result}, "Done upload test for the data $in_id successfully\n");
done_testing();

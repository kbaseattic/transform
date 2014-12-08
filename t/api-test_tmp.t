use strict;
use Bio::KBase::Transform::Client;
use Test::More tests => 12;
use Data::Dumper;
use Test::Cmd;
use JSON;
use Bio::KBase::userandjobstate::Client;
use Bio::KBase::AuthToken;
use Bio::KBase::workspace::Client;







my $shock_url="http://10.1.16.87:7078";
my $ujs_url = "http://10.1.16.87:7083";
my $transform_url="http://10.1.16.87:7778";

my $cc = Bio::KBase::Transform::Client->new($transform_url);

ok( defined $cc, "Check if the transform server is working" );


my $to = Bio::KBase::AuthToken->new();
my $token = $to->{token};


#good genebank file
my $job_id = $cc->validate({etype => "KBaseGenomes.GBK", in_id => "a2a7e05a-35a0-4ac6-8a63-a0ef98796829"});

#bad genebank file
#my $job_id = $cc->validate({etype => "KBaseGenomes.GBK", in_id => "318506ad-7a4d-4e34-ad47-e920dcd1024d"});



our $uc = Bio::KBase::userandjobstate::Client->new($ujs_url, 'token' => $token);

my $jid = $job_id->[1];

my $i;
my @ress;

while($i<100){
	$i++;
	print "checking job status for $jid: $i \n";
	@ress=$uc->get_job_status($jid);
	print "@ress\n";
	sleep 1;
}
#print "check job status for job id $jid\n";












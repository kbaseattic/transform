use strict;
use Bio::KBase::Transform::Client;
use Test::More tests => 34;
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




################################################################################
#set up server url and prot#####################################################
#http://10.1.16.87 is the server set up by Shinjae. It hosts shock, workspace, user_job_status and transform
my $shock_url="http://10.1.16.87:7078";
my $ujs_url = "http://10.1.16.87:7083";
my $transform_url="http://10.1.16.87:7778";
my $ws_url="http://10.1.16.87:7058";
print "set the server for shock, ujs workspace and transform\n";
print "please login as kbasetest\n";

my $res1;
my @tmp_all;
undef my @ress;
my $line;
my $job_id;
my $jid;
my $lim;
my $check;
my $res;
my $running_time=0;
my @para;
my $rand_text=int rand(time);
my $ws_id="loader_test";
my $shock_id1="a2a7e05a-35a0-4ac6-8a63-a0ef98796829"; #genebank file
my $shock_id2="80ba7a92-b7f6-410d-9571-e022ec096f48"; #reference assembly file
my $shock_id3_1="cea4071a-2c0c-4286-8d43-32710b4e8dfd"; #pair end
my $shock_id3_2="214e7a7e-bff7-48b0-b08f-cce24dcc91c9"; #pair end
my $shock_id4="cea4071a-2c0c-4286-8d43-32710b4e8dfd"; #single end



my @tem;
my $n;
my $i;
my %rec_hash;
my $in;

my $cc = Bio::KBase::Transform::Client->new($transform_url);

print "This test requires a genbank file($shock_id1) is stored in shock.\n";
print "It also requires read and write ability in the $ws_id(workspace)\n";
ok( defined $cc, "Check if the transform server is working" );


################################################################################
#check if the data is stored in SHOCK###########################################
#print "check if the data is stored in shock\n";

my $to = Bio::KBase::AuthToken->new();
my $token = $to->{token};

print "check if the right data is stored in $shock_id1\n";
$para[0]=$shock_id1;
$para[1]="tmp_shock_".$rand_text;
&downloadfromshock(@para);
open MM,"$para[1]" or die "No file can be donwloaded from shock\n";
@tmp_all=<MM>;
close MM;
$line=join "", @tmp_all;
ok(-e $para[1], "Generating a temporary file for $shock_id1\n");
ok( $line =~/organism/i && $line =~/LOCUS/i && $line=~/gene/i && $line=~/feature/i, "it seems the shock node($shock_id1) is a gene bank file\n");
ok(unlink($para[1]), "deleting the temporary file for $shock_id1\n");


print "check if the right data is stored in $shock_id2\n";
$rand_text=int rand(time);
$para[0]=$shock_id2;
$para[1]="tmp_shock_".$rand_text;
&downloadfromshock(@para);
ok(-e $para[1], "Generating a temporary file for $shock_id2\n");
open MM,"$para[1]" or die "No file can be donwloaded from shock\n";
@tmp_all=<MM>;
close MM;
my $line=join "", @tmp_all;
undef @tem;
if(@tmp_all>20){
	$lim=20;
}else{
	$lim=@tmp_all;
}
for ($i=0;$i<$lim;$i++){
	next if $tmp_all[$i]=~/^>/;
	@tem=split//,$tmp_all[$i];
	foreach $in(@tem){
		$rec_hash{$in}=1;
	}
}
$n=@tem=keys %rec_hash;
print "The first 10 or so sequence of $shock_id2 contains the following letters:\n@tem\n";
ok($n <10,"it seems the shock node($shock_id2) contains only DNA sequence");
ok( $line =~/^>/ ,"it seems the shock node($shock_id2) is a  fasta file\n");
ok(unlink($para[1]), "deleting the temporary file for $shock_id2\n");


print "check if the right data is stored in $shock_id3_1\n";
$rand_text=int rand(time);
$para[0]=$shock_id3_1;
$para[1]="tmp_shock_".$rand_text;
&downloadfromshock(@para);
open MM,"$para[1]" or die "No file can be donwloaded from shock\n";
@tmp_all=<MM>;
close MM;

if(@tmp_all>20){
	$lim=20;
}else{
	$lim=@tmp_all;
}
$check=0;
for ($i=0;$i<$lim;$i++){
	next if $tmp_all[$i] !~/\@/;
	$check=1 if length($tmp_all[$i]) >1000;
}
ok($check ==0,"$shock_id3_1 looks like a pair end file because it contains short reads");
ok($tmp_all[0]=~/^\@/, "$shock_id3_1 looks like a pair end file");
ok(unlink($para[1]), "deleting the temporary file for $shock_id3_1\n");


print "check if the right data is stored in $shock_id3_2\n";
$rand_text=int rand(time);
$para[0]=$shock_id3_2;
$para[1]="tmp_shock_".$rand_text;
&downloadfromshock(@para);
open MM,"$para[1]" or die "No file can be donwloaded from shock\n";
@tmp_all=<MM>;
close MM;

if(@tmp_all>20){
	$lim=20;
}else{
	$lim=@tmp_all;
}
$check=0;
for ($i=0;$i<$lim;$i++){
	next if $tmp_all[$i] !~/\@/;
	$check=1 if length($tmp_all[$i]) >1000;
}
ok($check ==0,"$shock_id3_2 looks like a pair end file because it contains short reads");
ok($tmp_all[0]=~/^\@/, "$shock_id3_2 looks like a pair end file");
ok(unlink($para[1]), "deleting the temporary file for $shock_id3_2\n");


print "check if the right data is stored in $shock_id4\n";
$rand_text=int rand(time);
$para[0]=$shock_id4;
$para[1]="tmp_shock_".$rand_text;
&downloadfromshock(@para);
open MM,"$para[1]" or die "No file can be donwloaded from shock\n";
@tmp_all=<MM>;
close MM;
if(@tmp_all>20){
	$lim=20;
}else{
	$lim=@tmp_all;
}
$check=0;
for ($i=0;$i<$lim;$i++){
	next if $tmp_all[$i] !~/\@/;
	$check=1 if length($tmp_all[$i]) >1000;
}
ok($check ==0,"$shock_id4 looks like a single end file because it contains short reads");
ok($tmp_all[0] =~/\@/,"$shock_id4 looks like a single end file because it start with a \@");
ok(unlink($para[1]), "deleting the temporary file for $shock_id4\n");



################################################################################
#start uploading the data from SHOCK to workspace###############################
my $obj_name="uploaded_testdata_".$rand_text;
print "generateing a random text for the newly generated workspace object:\t$obj_name\n";

$token = $ENV{'KB_AUTH_TOKEN'};
our $uc = Bio::KBase::userandjobstate::Client->new($ujs_url, 'token' => $token);
ok(defined $uc, "ujs server is working");

$job_id = $cc->upload({etype => "KBaseGenomes.GBK", kb_type => "KBaseGenomes.Genome", in_id =>$shock_id1, "ws_name" => $ws_id, "obj_name" => $obj_name, "opt_args" => '{}'});
ok(ref($job_id) eq "ARRAY","upload returns an array");
ok(@{$job_id} eq 2, "upload returns two job ids");
$jid = $job_id->[1];
print "check job status for job id $jid\n";
$check=0;
undef @ress;
$running_time=0;
while($check <1){
	sleep 3;
	@ress=$uc->get_job_status($jid);
	if($ress[1] =~/complete/i && $ress[2] =~/succeed/i){
		$check=1;
	}

	if($ress[1] =~/error|fail/i && $ress[2] =~/error|fail/i){
		$check=2;
	}

	$running_time=$running_time+3;
	print "waiting for the job to be finished...$running_time seconds past\n";
	
	if($running_time>1800){
		print "job can not be finished in 30 minutes\n";
		$check=2;
	}

}
ok($check==1, "uploading job finished in $running_time seconds\n");
print "The new object($obj_name) is now uploaded into workspace($ws_id)\n" if $check==1;
print "uploading job can not be finished in $running_time seconds\n" if $check==2;


$rand_text=int rand(time);
my $obj_name2="api-test-rl_".$rand_text;
$job_id = $cc->upload({etype => "KBaseAssembly.FA", kb_type => "KBaseAssembly.ReferenceAssembly", in_id =>$shock_id2, "ws_name" => $ws_id, "obj_name" => $obj_name2, "optional_args"=> '{"validator":{},"transformer":{"reference_name":"test_ref_name","handle_service_url":"http://10.1.16.87:7109","shock_url":"http://10.1.16.87:7078"}}'});
ok(ref($job_id) eq "ARRAY","upload returns an array");
ok(@{$job_id} eq 2, "upload returns two job ids");
$jid = $job_id->[1];
print "check job status for job id $jid\n";
$check=0;
while($check <1){
	sleep 3;
	@ress=$uc->get_job_status($jid);
	if($ress[1] =~/complete/i && $ress[2] =~/succeed/i){
		$check=1;
	}
	if($ress[1] =~/error|fail/i && $ress[2] =~/error|fail/i){
		$check=2;
	}
	$running_time=$running_time+3;
	print "waiting for the job to be finished...$running_time seconds past\n";
	if($running_time>1800){
		print "job can not be finished in 30 minutes\n";
		$check=2;
	}
}
ok($check==1, "uploading job finished in $running_time seconds\n");
print "The new object($obj_name2) is now uploaded into workspace($ws_id)\n" if $check==1;
print "uploading job can not be finished in $running_time seconds\n" if $check==2;


$rand_text=int rand(time);
my $obj_name3="api-test-pel_".$rand_text;
$job_id = $cc->upload({etype => "KBaseAssembly.FQ", kb_type => "KBaseAssembly.PairedEndLibrary", in_id => "$shock_id3_1,$shock_id3_2", "ws_name" => "loader_test", "obj_name" => $obj_name3, "optional_args"=> '{"validator":{},"transformer":{"handle_service_url":"http://10.1.16.87:7109","shock_url":"http://10.1.16.87:7078"}}'});
ok(ref($job_id) eq "ARRAY","upload returns an array");
ok(@{$job_id} eq 2, "upload returns two job ids");
$jid = $job_id->[1];
print "check job status for job id $jid\n";
$check=0;
while($check <1){
	sleep 3;
	@ress=$uc->get_job_status($jid);
	if($ress[1] =~/complete/i && $ress[2] =~/succeed/i){
		$check=1;
	}
	if($ress[1] =~/error|fail/i && $ress[2] =~/error|fail/i){
		$check=2;
	}
	$running_time=$running_time+3;
	print "waiting for the job to be finished...$running_time seconds past\n";
	if($running_time>1800){
		print "job can not be finished in 30 minutes\n";
		$check=2;
	}
}
ok($check==1, "uploading job finished in $running_time seconds\n");
print "The new object($obj_name3) is now uploaded into workspace($ws_id)\n" if $check==1;
print "uploading job can not be finished in $running_time seconds\n" if $check==2;












my $para2;
my @ws_obj;


################################################################################
#using workspace API to retreive the newly uploaded data and roughly verfiy them

my $ws_client= Bio::KBase::workspace::Client->new($ws_url);
ok(defined $ws_client, "workspace server is working");
$para2->{'workspaces'}=[$ws_id];
$res1=$ws_client->list_objects($para2);



print "check if $obj_name is stored in workspace\n"; 

for($i=0;$i<@$res1;$i++){
	next if $res1->[$i]->[1] !~/$obj_name/;
	push @ws_obj , $res1->[$i]->[1];
}
ok(@ws_obj ==2 , "two new objects have been created in workspace:\n$ws_obj[0]\n$ws_obj[1]\n");

my $contig=$ws_obj[0] if $ws_obj[0]=~/cs$/i;
$contig=$ws_obj[1] if $ws_obj[1]=~/cs$/i;
undef $para2;
$para2->{'id'}=$contig;
$para2->{'workspace'}=$ws_id;
$res=$ws_client->get_object($para2);

my $len=length($res->{'data'}->{'contigs'}->[0]->{'sequence'});
print "after uploading, the length of the contig is $len\n";
ok($len>10000, "the length of the contig is more than 10k in the workspace");

my $ff=$ws_obj[0] if $ws_obj[0]=~/gn$/i;
$ff=$ws_obj[1] if $ws_obj[1]=~/gn$/i;

$para2->{'id'}=$ff;
$para2->{'workspace'}=$ws_id;
$res=$ws_client->get_object($para2);

my $num=@{$res->{'data'}->{'features'}};
print "$num features are detected in the genome\n";
ok($num>10, "the number of features in the genome is more than 10");


print "\n\ncheck if $obj_name2 is stored in workspace\n";
print "$obj_name2 is a workspace object. It contains a shock node id, which stores the reference genome in fasta format\n";
undef @ws_obj;
for($i=0;$i<@$res1;$i++){
	next if $res1->[$i]->[1] !~/$obj_name2/;
	#print "$res->[$i]->[1]\n";
	push @ws_obj , $res1->[$i]->[1];
}
ok(@ws_obj ==1 , "one new objects have been created in workspace:\n$ws_obj[0]\n");
#to do:
#check the format of this object


print "\n\ncheck if $obj_name3 is stored in workspace\n";
print "$obj_name3 is a workspace object. It contains a shock node id, which stores the reference genome in fasta format\n";
undef @ws_obj;
for($i=0;$i<@$res1;$i++){
	next if $res1->[$i]->[1] !~/$obj_name3/;
	#print "$res->[$i]->[1]\n";
	push @ws_obj , $res1->[$i]->[1];
}
ok(@ws_obj ==1 , "one new objects have been created in workspace:\n$ws_obj[0]\n");


################################################################################
#testing validate


my $job_id = $cc->validate({etype => "KBaseGenomes.GBK", in_id => $shock_id1});
$jid = $job_id->[1];
$i=0;
$check=0;
while($i<100 && $check ==0){
	$i++;
	print "checking job status for $jid: $i... \n";
	@ress=$uc->get_job_status($jid);
	print "@ress\n";
	sleep 3;
	$line=join "",@ress;
	if($line =~/Succeed/i){
		$check=1;
	}
}
ok($check==1, "validate the data for $shock_id1 successfully\n");




















#this is a function to download the file from shock
sub downloadfromshock {
  my $sid = shift;
  my $file =shift;

  #upload data to shock and capture node id
  my $cmd = "curl -s -H \"Authorization: OAuth $token\" -X GET  $shock_url/node/$sid?download >$file";
  `$cmd`;
  return $file;
}



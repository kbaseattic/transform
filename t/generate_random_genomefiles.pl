use strict;
use warnings;

use POSIX;
use JSON;

use Data::Dumper;
use  Bio::KBase::AuthToken;

#author: Fei He(plane83@gmail.com)
#This script will download a list of bacteria genomes from NCBI in Genbank format and fasta format
#the downloaded genomes will be stored in shock
#config files will be generated.

#The purpose of this script is to generate config file for a randomly downloaded bacteria genome
#updated Jan. 8, 2015






my $to = Bio::KBase::AuthToken->new();
my  $token = $to->{token};

#define some dummy variables
my $tmp;
my @array;
my @array2;
my @array3;
my @array_fasta;
my %hash;
my $i;
my $id;
my @tem;
my @para;

#define some varibales
my $shock_url='http://10.1.16.87:7078';
my $transform_url='http://10.1.16.87:7778';

my $workspace_name='loader_test';
my $workspace_obj1="random_bacteria_genome1";
my $workspace_obj2="random_bacteria_genome2";
#$workspace_obj=int rand(time);
#$workspace_obj="random_".$workspace_obj;

my $logfile="wget_logfile.txt";
my $number_of_genomes=1;
my $tmpdir="randomly_selected_genomes_in_Genbank_format";
my $tmpdir2="randomly_selected_genomes_in_fasta_format";
my $config_file="configs/upload-KBaseGenomes.GBK-to-KBaseGenomes.Genomes_random.json";
my $config_file2="configs/upload-KBaseGenomes.FASTA-to-KBaseGenomes.Genomes_random.json";


my $source='ftp://ftp.ncbi.nlm.nih.gov/genomes/Bacteria/';
`wget $source -o $logfile`;

$tmp=int rand(1000);
$tmp="file_".$tmp;
`mv index.html $tmp`;
open MM,"$tmp" or die "no file";
while(<MM>){
	next if $_!~/Directory/;
	if($_=~/"(ftp.*?)"/){
	#print "$1\n";
		push @array,$1;
	}
}
close MM;
unlink($tmp);
$tmp=@array;
print "\n\n############################################################\n\n";
print "$tmp bacteria genomes detected in $source\n";
print "randomly select $number_of_genomes genomes\n";
for($i=0;$i<$number_of_genomes;$i++){
	$tmp=int rand(@array);
	push @array2,$array[$tmp];
	print "$i\t$array[$tmp] selected\n";
}

print "\n\n############################################################\n\n";
if(-d $tmpdir){
	`rm -r $tmpdir`;
}
`mkdir $tmpdir`;
if(-d $tmpdir2){
	`rm -r $tmpdir2`;
}
`mkdir $tmpdir2`;
print "All genomes will be stored in the folder:$tmpdir and $tmpdir2\n";
print "start downloading genomes in Genbank format and fasta format\n";
foreach $i(@array2){
	`wget $i -o $logfile`;
	$tmp=int rand(1000);
	$tmp="file_".$tmp;
	`mv index.html $tmp`;
	#print "$tmp\n";
	
	undef @array_fasta;
	undef @array;
	open MM,"$tmp" or die "No file";
	while(<MM>){
		next if $_!~/File/;
		if($_=~/"(ftp.*?gbk)"/){
			push @array,$1;	
			#print "$1\n";	
		}
		if($_=~/"(ftp.*?fna)"/){
			push @array_fasta,$1;	
			#print "$1\n";	
		}


	}
	close MM;
	unlink($tmp);

	
	if(@array>0){
		@tem=split/\//,$array[0];
		$id=$tem[-2];
		push @array3,$id;
	}else{
		next;
	}


	print "\ngenerating a sub directory for $id\n";
	`mkdir $tmpdir/$id`;
	$tmp=$tmpdir."/".$id;
	foreach (@array){
		`wget $_ -P $tmp -o $logfile`;
	}
	`mkdir $tmpdir2/$id`;
	$tmp=$tmpdir2."/".$id;
	foreach (@array_fasta){
		`wget $_ -P $tmp -o $logfile`;
	}

}
print "\n\n############################################################\n\n";
print "downloading genomes in Genbank and fasta finished:\n\n";
foreach (@array3){
	print "$tmpdir/$_\n";
	print "$tmpdir2/$_\n";
}


print "\n\nthese genomes are stored in $tmpdir and $tmpdir2\n";
print "each genome is stored in a sub-directory in $tmpdir and $tmpdir2\n";
print "some genome may contain several Genbank files\n";
print "Now, you're ready to use those genomes for testing\n";

unlink($logfile);


##########################################################
print "\n\n############################################################\n\n";
print "uploading files into shock server at $shock_url\n\n";

@tem=glob("$tmpdir/*");
print "uploading $tem[0] into shock\n";
@array=glob("$tem[0]/*gbk");
#print "@array\n";
undef @array2;
undef %hash;

foreach (@array){
	$para[0]=$_;
	$tmp=upload2shock(@para);
#	print "uploading $_ into shock node:\n";
#	print "$tmp\n\n";
	$hash{$_}=$tmp;
}

undef @array;
#print "A randomly selected GenBank genome has been stored in the following shock nodes:\n";
foreach (sort keys %hash){
	print "$_\t$hash{$_}\n";
	push @array,$hash{$_};
}

open NN,">$config_file" or die "can not create a file\n";
undef $tmp;
$tmp->{'test_name'}= "uploading KBaseGenomes.GBK to KBaseGenomes.Genome";
$tmp->{'test_server_url'}=$transform_url;
$tmp->{'input_data_url'}=\@array;
$tmp->{'external_type'}='KBaseGenomes.GBK';
$tmp->{'kbase_type'}='KBaseGenomes.Genome';
$tmp->{'ws_name'}=$workspace_name;
$tmp->{'obj_name'}=$workspace_obj1;
$tmp->{'max_wait_sec'}='300';
$tmp->{'check_interval'}='3';
$tmp->{'optional_args'}='{}';
$tmp->{'expected_result'}='1';
$tmp->{'skip_server_test'}='true';
$tmp= to_json($tmp);
print NN "$tmp\n";
close NN;

print "#######################################################\n\n";
print "config file has been generated for the randomly downloaded genomes(GenBank format):\n";
print "$config_file\n\n\n";


@tem=glob("$tmpdir2/*");
print "uploading $tem[0] into shock\n";
@array=glob("$tem[0]/*fna");
#print "@array\n";
undef @array2;
undef %hash;

foreach (@array){
	$para[0]=$_;
	$tmp=upload2shock(@para);
#	print "uploading $_ into shock node:\n";
#	print "$tmp\n\n";
	$hash{$_}=$tmp;
}

undef @array;
#print "A randomly selected FASTA genome has been stored in the following shock nodes:\n";
foreach (sort keys %hash){
	print "$_\t$hash{$_}\n";
	push @array,$hash{$_};
}

open NN,">$config_file2" or die "can not create a file\n";
undef $tmp;
$tmp->{'test_name'}= "uploading KBaseGenomes.FASTA to KBaseGenomes.Genome";
$tmp->{'test_server_url'}=$transform_url;
$tmp->{'input_data_url'}=\@array;
$tmp->{'external_type'}='KBaseGenomes.FASTA';
$tmp->{'kbase_type'}='KBaseGenomes.Genome';
$tmp->{'ws_name'}=$workspace_name;
$tmp->{'obj_name'}=$workspace_obj2;
$tmp->{'max_wait_sec'}='300';
$tmp->{'check_interval'}='3';
$tmp->{'optional_args'}='{}';
$tmp->{'expected_result'}='1';
$tmp->{'skip_server_test'}='true';
$tmp= to_json($tmp);
print NN "$tmp\n";
close NN;

print "#######################################################\n\n";
print "config file has been generated for the randomly downloaded genomes(FASTA format):\n";
print "$config_file2\n\n\n";
















sub upload2shock {
  my $fn = shift; #file name to be uploaded to shock
  #upload data to shock and capture node id
  my $cmd = "curl -s -H \"Authorization: OAuth $token\" -X POST -F upload=\@$fn $shock_url/node";
  my $out_shock_meta = from_json(`$cmd`);
  my $nodeid = $out_shock_meta->{data}->{id};
  #return nodeid of upload
  return $nodeid;
}





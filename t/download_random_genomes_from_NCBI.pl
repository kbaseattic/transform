use strict;
use warnings;


#This script will download a list of bacteria genomes from NCBI in Genbank format



#define some dummy variables
my $tmp;
my @array;
my @array2;
my @array3;
my %hash;
my $i;
my $id;
my @tem;

my $logfile="wget_logfile.txt";
my $number_of_genomes=10;
my $tmpdir="randomly_selected_genomes_in_Genbank_format";

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
print "All genomes will be stored in the folder:$tmpdir\n";
print "start downloading genomes in Genbank format\n";
foreach $i(@array2){
	`wget $i -o $logfile`;
	$tmp=int rand(1000);
	$tmp="file_".$tmp;
	`mv index.html $tmp`;
	#print "$tmp\n";
	
	undef @array;
	open MM,"$tmp" or die "No file";
	while(<MM>){
		next if $_!~/File/;
		if($_=~/"(ftp.*?gbk)"/){
			push @array,$1;	
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

}
print "\n\n############################################################\n\n";
print "downloading genomes finished:\n\n";
foreach (@array3){
	print "$tmpdir/$_\n";
}
print "\n\nthese genomes are stored in $tmpdir\n";
print "each genome is stored in a sub-directory in $tmpdir\n";
print "some genome may contain several Genbank files\n";
print "Now, you're ready to use those genomes for testing\n";






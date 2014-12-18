use strict;
use warnings;




#author: Fei He(plane83@gmail.com)

#This script will download a list of bacteria genomes from NCBI in Genbank format and fasta format
#the downloaded genomes will be stored in new folders


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

#define some varibales
my $logfile="wget_logfile.txt";
my $number_of_genomes=10;
my $tmpdir="randomly_selected_genomes_in_Genbank_format";
my $tmpdir2="randomly_selected_genomes_in_fasta_format";

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





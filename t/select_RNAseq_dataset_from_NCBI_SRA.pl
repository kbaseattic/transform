use strict;
use warnings;




#author: Fei He(plane83@gmail.com)

#This script randomly selects a list of bacteria RNAseq data


#$file contains all available bacteria RNAseq data IDs from NCBI SRA. This is a file manually prepared by Fei.
my $file='SraAcc_candidates.txt';

#define dummy variables
my %hash;
my @array;
my @array2;
my $tmp;
my $i;

open MM,"$file" or die "No SraAcc file!";
while(<MM>){
	chomp;
	next if $_=~/#/;
	push @array,$_;
}
close MM;
$tmp=@array;
print "$tmp datasets are available from $file\n";
print "randomly select 10 datasets\n\n";
for($i=0;$i<10;$i++){
	$tmp=int rand (@array);
	print "$array[$tmp] is selected\n";
	push @array2,$array[$tmp];
}
$tmp=@array;

print "\n\nyou selected 10 bacteria RNAseq datasets from NCBI SRA($tmp datasets in total)\n";
print join "\n",@array2;


print "\n\nyou can use the following command to download fastq file for each dataset:\n";
print "fastq-dump -Z $array2[0] >output_fastq\n";
print "you can also use the following command to print out the first 5 spots\n";
print "fastq-dump -X 5 -Z $array2[0] >output_fastq\n\n";
print "fastq-dump is a command provided by NCBI. You can download it from\nhttp://www.ncbi.nlm.nih.gov/Traces/sra/sra.cgi?view=software\n";

print "\nYou are now ready to use those dataset for further testing\n";







#!/usr/bin/env perl
#PERL USE
use warnings;
use strict;
use Data::Dumper;
use Getopt::Long;
use Digest::MD5;

#KBASE USE
use Bio::KBase::Transform::ScriptHelpers qw( getStderrLogger );

=head1 NAME

trns_transform_FASTA_Transcripts_to_KBaseGenomes.Genome.pl

=head1 SYNOPSIS

trns_transform_FASTA_Transcripts_to_KBaseGenomes.Genome.pl --input_file_name fasta-file --output_file_name genome-id

=head1 DESCRIPTION

Transform a FASTA file into a KBaseGenomes.Genome object in the workspace.

=head1 COMMAND-LINE OPTIONS
trns_transform_KBaseFBA.SBML-to-KBaseFBA.FBAModel.pl --input --output
	-i --input_file_name      sbml file
	-o --output_file_name     id under which KBaseGenomes.Genome is to be saved
        --help                    print usage message and exit

=cut

my %genetic_code = (TTT => 'F',  TCT => 'S',  TAT => 'Y',  TGT => 'C',
		    TTC => 'F',  TCC => 'S',  TAC => 'Y',  TGC => 'C',
		    TTA => 'L',  TCA => 'S',  TAA => '*',  TGA => '*',
		    TTG => 'L',  TCG => 'S',  TAG => '*',  TGG => 'W',
		    CTT => 'L',  CCT => 'P',  CAT => 'H',  CGT => 'R',
		    CTC => 'L',  CCC => 'P',  CAC => 'H',  CGC => 'R',
		    CTA => 'L',  CCA => 'P',  CAA => 'Q',  CGA => 'R',
		    CTG => 'L',  CCG => 'P',  CAG => 'Q',  CGG => 'R',
		    ATT => 'I',  ACT => 'T',  AAT => 'N',  AGT => 'S',
		    ATC => 'I',  ACC => 'T',  AAC => 'N',  AGC => 'S',
		    ATA => 'I',  ACA => 'T',  AAA => 'K',  AGA => 'R',
		    ATG => 'M',  ACG => 'T',  AAG => 'K',  AGG => 'R',
		    GTT => 'V',  GCT => 'A',  GAT => 'D',  GGT => 'G',
		    GTC => 'V',  GCC => 'A',  GAC => 'D',  GGC => 'G',
		    GTA => 'V',  GCA => 'A',  GAA => 'E',  GGA => 'G',
		    GTG => 'V',  GCG => 'A',  GAG => 'E',  GGG => 'G');

my %reverse_genetic_code = (A  => "GCN",
			    C  => "TGY",
			    D  => "GAY",
			    E  => "GAR",
			    F  => "TTY",
			    G  => "GGN",
			    H  => "CAY",
			    I  => "ATH",
			    K  => "AAR",
			    L  => "YTN",
			    M  => "ATG",
			    N  => "AAY",
			    P  => "CCN",
			    Q  => "CAR",
			    R  => "MGN",
			    S  => "WSN",
			    T  => "ACN",
			    U  => "TGA",
			    V  => "GTN",
			    W  => "TGG",
			    X  => "NNN",
			    Y  => "TAY",
                           '*' => "TRR");

my $logger = getStderrLogger();

my $In_File   = "";
my $Out_File  = "";
my $Genome_ID = "";
my $IsDNA     = 0;
my $Help      = 0;
GetOptions("input_file_name|i=s"   => \$In_File,
	   "output_file_name|o=s"  => \$Out_File,
	   "genome_id|g=s" => \$Genome_ID,
	   "dna|d"         => \$IsDNA,
           "help|h"        => \$Help);

if($Help || !$In_File || !$Out_File){
    print($0." --input_file_name|-i <Input Fasta File> --output_file_name|-o <Output KBaseGenomes.Genome JSON Flat File> --genome_id|g <Genome ID (input_file_name used by default)> --dna|d");
    $logger->warn($0." --input_file_name|-i <Input Fasta File> --output_file_name|-o <Output KBaseGenomes.Genome JSON Flat File> --genome_id|g <Genome ID (input_file_name used by default)> --dna|d");
    exit();
}

if ($Genome_ID eq "" || !defined($Genome_ID)) {
    my(@names) = split(m%/%, $In_File);
    $Genome_ID = $names[-1];
}

#if($Genome_ID ne "" && $Genome_ID !~ /^[\w\|.-]+$/){
#    $logger->warn("Genome_id parameter contains illegal characters, must only use a-z, A-Z, '_', '|', '.', and '-'");
#    die("Genome_id parameter contains illegal characters, must only use a-z, A-Z, '_', '|', '.', and '-'");
#}


if(!-f $In_File){
    $logger->warn("Cannot find file ".$In_File);
    die("Cannot find $In_File");
}

$logger->info("Mandatory Data passed = ".join(" | ", ($In_File,$Out_File)));
$logger->info("Optional Data passed = ".join(" | ", ("Genome:".$Genome_ID,"DNA:".$IsDNA)));

#use in reading in linebreaks '\r' & '\n'
use File::Stream;

#use in reading gzipped files
use IO::Uncompress::Gunzip qw(gunzip $GunzipError);

my $fh = getFileHandle($In_File);
my @seqs = read_fasta($fh,1);


my $GenomeHash = {id => $Genome_ID,
		  scientific_name => '',
		  domain => "Plant",
		  genetic_code => 1,
		  source => "User",
		  source_id => "User",
		  taxonomy => "viridiplantae",
		  gc_content => 0.5,
		  dna_size => 0,
		  features => [],
                  contigs => [],
		  num_contigs => 0,
		  contig_lengths => [],
		  contig_ids => []};

#Test first sequence for NAs
if(!$IsDNA){
    my %entities=();
    foreach my $en ( map { uc($_) } split(//,$seqs[0][2]) ){
	$entities{$en}++;
    }
    my $sum = $entities{'A'}+$entities{'G'}+$entities{'C'}+$entities{'T'};
    $IsDNA = 1 if ( $sum/length($seqs[0][2]) > 0.75 );
}

my $Contig = "1";
my $Contig_Location = "0";

my $GCs=0;
my $DNA_Size=0;
foreach my $Seq (@seqs){
    my ($ProtSeq,$DNASeq)=("","");
    if($IsDNA){
	$DNASeq = $Seq->[2];
	my @codons = $DNASeq =~ m/(...?)/g;
	$ProtSeq = join( '', map { exists($genetic_code{$_}) ? $genetic_code{$_} : '*' } map { uc($_) } @codons );
    }else{
	$ProtSeq = $Seq->[2];
	$DNASeq = join( '' , map { exists($reverse_genetic_code{$_}) ? $reverse_genetic_code{$_} : 'NNN' } map { uc($_) } split(//,$ProtSeq) );
    }

    $DNA_Size+=length($DNASeq);
    foreach my $na (split(//,$DNASeq)){
	$GCs++ if $na =~ /[GgCc]/;
    }


    if( $Seq->[0] !~ /^([\w\.\|\-]+)$/){
	$Seq->[0] =~ s/[\s:,-]/_/g;
    }

    my $CDSHash={id=>$Seq->[0],
		 type=>'CDS',
		 protein_translation=>$ProtSeq,
		 protein_translation_length=>length($ProtSeq),
		 md5=>Digest::MD5::md5_hex($ProtSeq),
		 dna_sequence => $DNASeq,
		 dna_sequence_length => length($DNASeq),
		 location => []};

    push @{$CDSHash->{location}}, [$Contig,$Contig_Location+0,'>',length($DNASeq)];
    $Contig_Location+=length($DNASeq)+1;

    push(@{$GenomeHash->{features}},$CDSHash);
}

$GCs = sprintf("%.2f",($GCs/$DNA_Size)) + 0.0;
$GenomeHash->{gc_content} = $GCs;
$GenomeHash->{dna_size} = $DNA_Size;

$logger->info("Writing Genome WS Object");


eval {
    use JSON;
    my $json_text = encode_json($GenomeHash);
    open(OUT, "> $Out_File");
    print OUT $json_text;
    close(OUT);

    $logger->info("Writing Genome WS Object Complete");
};

if ($@) {
    die("Unable to create JSON :: ".$@);
}

sub getFileHandle{
    my $file=shift;
    my $stream;
    
    my $fh = new IO::Uncompress::Gunzip($file,Transparent=>1) or die "IO::Uncompress::Gunzip failed on $file: $GunzipError\n";;
    $stream = (File::Stream->new($fh, separator => qr{[\cM\r\n]}))[1];
    return $stream;
}

sub read_fasta
{
    my $file = $_[0];
    my $dataR;

    while(<$file>){
	$dataR.=$_;
    }

    my $is_fasta = $dataR =~ m/^[\s\r]*>/;
    my @seqs = map { $_->[2] =~ tr/ \n\r\t//d; $_ }
               map { /^(\S+)([ \t]+([^\n\r]+)?)?[\n\r]+(.*)$/s ? [ $1, $3 || '', $4 || '' ] : () }
               split /[\n\r]+>[ \t]*/m, $dataR;

    #  Fix the first sequence, if necessary
    if ( @seqs )
    {
        if ( $is_fasta )
        {
            $seqs[0]->[0] =~ s/^>//;  # remove > if present
        }
        elsif ( @seqs == 1 )
        {
            $seqs[0]->[1] =~ s/\s+//g;
            @{ $seqs[0] } = ( 'raw_seq', '', join( '', @{$seqs[0]} ) );
        }
        else  #  First sequence is not fasta, but others are!  Throw it away.
        {
            shift @seqs;
        }
    }

    wantarray ? @seqs : \@seqs;
}

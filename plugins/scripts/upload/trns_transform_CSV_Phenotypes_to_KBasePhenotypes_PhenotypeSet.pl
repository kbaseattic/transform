#!/usr/bin/env perl
#PERL USE
use warnings;
use strict;
use Data::Dumper;
use Getopt::Long;

#KBASE USE
use Bio::KBase::Transform::ScriptHelpers qw( parse_input_table getStderrLogger );
use Bio::KBase::fbaModelServices::ScriptHelpers qw(fbaws get_fba_client runFBACommand universalFBAScriptCode );

=head1 NAME

trns_transform_CSV_Phenotypes_to_KBasePhenotypes.PhenotypeSet.pl

=head1 SYNOPSIS

trns_transform_CSV_Phenotypes_to_KBasePhenotypes.PhenotypeSet.pl --input_file_name csv-file --object_name model-id --workspace_name workspace-id [--genome genome-id]

=head1 DESCRIPTION

Transform a CSV file into a KBasePhenotypes.PhenotypeSet object in the
workspace. A genome object in the same workspace is needed if one
wishes to include phenotypes with gene knockouts.

=head1 COMMAND-LINE OPTIONS
trns_transform_CSV_Phenotypes_to_KBasePhenotypes.PhenotypeSet.pl --input_file_name --object_name --workspace_name [--genome]
	-i --input_file_name      csv file
	-o --object_name     id under which KBasePhenotypes.PhenotypeSet is to be saved
        -w --workspace_name     workspace where KBasePhenotypes.PhenotypeSet is to be saved
        -g --genome     id of KBaseGenomes.Genome object to associate with KBasePhenotypes.PhenotypeSet. The object must be in the same workspace designated with workspace_name
	--help          print usage message and exit

=cut

my $logger = getStderrLogger();

my $In_File   = "";
my $Out_Object = "";
my $Out_WS    = "";
my $Genome    = "Empty";
my $Help      = 0;
my $fbaurl = "";
my $wsurl = "";

GetOptions("input_file_name|i=s"  => \$In_File,
	   "object_name|o=s" => \$Out_Object,
	   "workspace_name|w=s" => \$Out_WS,
	   "genome|g=s" => \$Genome,
	   "workspace_service_url=s" => $wsurl,
	   "fba_service_url=s" => $fbaurl,
	   "help|h"     => \$Help);

if (length($fbaurl) == 0) {
	$fbaurl = undef;
}
if (length($wsurl) == 0) {
	$wsurl = undef;
}

if($Help || !$In_File || !$Out_Object || !$Out_WS){
    print($0." --input_file_name/-i <Input CSV File> --object_name/-o <Output Object ID> --workspace_name/-w <Workspace to save Object in> --genome/-g <Input Genome ID>");
    $logger->warn($0." --input_file_name/-i <Input CSV File> --object_name/-o <Output Object ID> --workspace_name/-w <Workspace to save Object in> --genome/-g <Input Genome ID>");
    exit();
}

$logger->info("Mandatory Data passed = ".join(" | ", ($In_File,$Out_Object,$Out_WS)));
$logger->info("Optional Data passed = ".join(" | ", ("Genome:".$Genome)));

my $phenodata = parse_input_table($In_File,[
	["geneko",0,[],";"],
	["media",1,""],
	["mediaws",1,""],
	["addtlCpd",0,[],";"],
	["growth",1]
]);

for (my $i=0; $i < @{$phenodata}; $i++) {
	if ($phenodata->[$i]->[0]->[0] eq "none") {
		$phenodata->[$i]->[0] = [];
	}
	if ($phenodata->[$i]->[3]->[0] eq "none") {
		$phenodata->[$i]->[3] = [];
	}
}

my $Genome_WS = $Out_WS;
$Genome_WS = "PlantSEED" if $Genome eq "Empty";

my $input = {
	workspace=>$Out_WS,
	genome=>$Genome,
	genome_workspace=>$Genome_WS,
	phenotypes=>$phenodata,
	phenotypeSet=>$Out_Object,
	ignore_errors=>1
};

$logger->info("Loading PhenotypeSet WS Object");

use Capture::Tiny qw( capture );
my ($stdout, $stderr, @result) = capture {
    my $fba = get_fba_client($fbaurl);
    if (defined($wsurl)) {
    	$input->{wsurl} = $wsurl;
    }
    $fba->import_phenotypes($input);
};

$logger->info("fbaModelServices import_phenotypes() informational messages\n".$stdout) if $stdout;
$logger->warn("fbaModelServices import_phenotypes() warning messages\n".$stderr) if $stderr;
$logger->info("Loading PhenotypeSet WS Object Complete");

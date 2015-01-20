#!/usr/bin/env perl
use warnings;
use strict;
use Data::Dumper;
use Getopt::Long;
use Bio::KBase::Transform::ScriptHelpers qw( parse_input_table getStderrLogger );
use Bio::KBase::fbaModelServices::ScriptHelpers qw(fbaws get_fba_client runFBACommand universalFBAScriptCode );

=head1 NAME

trns_transform_KBasePhenotypes.CSV-to-KBasePhenotypes.PhenotypeSet.pl

=head1 SYNOPSIS

trns_transform_KBasePhenotypes.CSV-to-KBasePhenotypes.PhenotypeSet.pl --input csv-file --output model-id --out_ws workspace-id [--genome genome-id]

=head1 DESCRIPTION

Transform a CSV file into a KBasePhenotypes.PhenotypeSet object in the
workspace. A genome object in the same workspace is needed if one
wishes to include phenotypes with gene knockouts.

=head1 COMMAND-LINE OPTIONS
trns_transform_KBasePhenotypes.CSV-to-KBasePhenotypes.PhenotypeSet.pl --input --output --out_ws [--genome]
	-i --input      csv file
	-o --output     id under which KBasePhenotypes.PhenotypeSet is to be saved
        -w --out_ws     workspace where KBasePhenotypes.PhenotypeSet is to be saved
        -g --genome     id of KBaseGenomes.Genome object to associate with KBasePhenotypes.PhenotypeSet. The object must be in the same workspace designated with out_ws
	--help          print usage message and exit

=cut

my $logger = getStderrLogger();

my $In_File   = "";
my $Out_Object = "";
my $Out_WS    = "";
my $Genome    = "Empty";
my $Help      = 0;

GetOptions("input|i=s"  => \$In_File,
	   "output|o=s" => \$Out_Object,
	   "out_ws|w=s" => \$Out_WS,
	   "genome|g=s" => \$Genome,
	   "help|h"     => \$Help);

if($Help || !$In_File || !$Out_Object || !$Out_WS){
    print($0." --input/-i <Input CSV File> --output/-o <Output Object ID> --out_ws/-w <Workspace to save Object in> --genome/-g <Input Genome ID>");
    $logger->warn($0." --input/-i <Input CSV File> --output/-o <Output Object ID> --out_ws/-w <Workspace to save Object in> --genome/-g <Input Genome ID>");
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
    my $fba = get_fba_client();
    $fba->import_phenotypes($input);
};

$logger->info("fbaModelServices import_phenotypes() informational messages\n".$stdout) if $stdout;
$logger->warn("fbaModelServices import_phenotypes() warning messages\n".$stderr) if $stderr;
$logger->info("Loading PhenotypeSet WS Object Complete");

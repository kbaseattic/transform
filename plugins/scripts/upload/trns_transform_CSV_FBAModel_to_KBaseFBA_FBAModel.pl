#!/usr/bin/env perl
#PERL USE
use warnings;
use strict;
use Data::Dumper;
use Getopt::Long;

#KBASE USE
use Bio::KBase::Transform::ScriptHelpers qw( parse_input_table getStderrLogger );
use Bio::KBase::fbaModelServices::ScriptHelpers qw(fbaws get_fba_client runFBACommand universalFBAScriptCode );

my $script = "trns_transform_CSV_FBAModel-to-KBaseFBA.FBAModel.pl";

=head1 NAME

$script

=head1 SYNOPSIS

$script --input_file_name/-i <Input CSV Reaction File> --compounds/-c <Input CSV Compound File> --object_name/-o <Output Object ID> --workspace_name/-w <Workspace to save Object in> --genome/-g <Input Genome ID> --biomass/-b <Input Biomass ID>

=head1 DESCRIPTION

Transform a CSV file into an object in the workspace.

=head1 COMMAND-LINE OPTIONS
$script
	-i --input_file_name   name of reactions file with model data
	-c --compounds         csv file with compound data
	-o --object_name       id under which KBaseBiochem.Media is to be saved
	-w --workspace_name    workspace where KBaseBiochem.Media is to be saved
	-g --genome	       genome for which model was constructed
	-b --biomass	       id of biomass reaction in model
	--help                 print usage message and exit

=cut

my $logger = getStderrLogger();

my $In_RxnFile   = "";
my $In_CpdFile = "";
my $Out_Object = "";
my $Out_WS    = "";
my $Genome    = "Empty";
my $Biomass   = "";
my $Help      = 0;

GetOptions("input_file_name|i=s"  => \$In_RxnFile,
	   "compounds|c=s"  => \$In_CpdFile,
	   "object_name|o=s" => \$Out_Object,
	   "workspace_name|w=s" => \$Out_WS,
	   "genome|g=s" => \$Genome,
	   "biomass|b=s" => \$Biomass,
	   "help|h"     => \$Help);

if($Help || !$In_RxnFile || !$In_CpdFile || !$Out_Object || !$Out_WS){
    print($0." --input_file_name/-i <Input Reaction CSV File> --compounds/-c <Input Compound CSV File> --object_name/-o <Output Object ID> --workspace_name/-w <Workspace to save Object in> --genome/-g <Input Genome ID> --biomass/-b <Input Biomass ID>\n");
    $logger->warn($0." --input_file_name/-i <Input Reaction CSV File> --compounds/-c <Input Compound CSV File> --object_name/-o <Output Object ID> --workspace_name/-w <Workspace to save Object in> --genome/-g <Input Genome ID> --biomass/-b <Input Biomass ID>\n");
    exit();
}

$logger->info("Mandatory Data passed = ".join(" | ", ($In_RxnFile,$In_CpdFile,$Out_Object,$Out_WS)));
$logger->info("Optional Data passed = ".join(" | ", ("Genome:".$Genome,"Biomass:".$Biomass)));

my $input = {
	model => $Out_Object,
	workspace => $Out_WS,
	genome_workspace => $Out_WS,
	genome => $Genome,
	reactions => [],
	compounds => [],
	biomass => $Biomass,
};
if ($Genome eq "Empty") {
	$input->{genome_workspace} = "PlantSEED" ;
}

$input->{reactions} = parse_input_table($In_RxnFile,[
	["id",1],
	["direction",0,"="],
	["compartment",0,"c"],
	["gpr",1],
	["name",0,undef],
	["enzyme",0,undef],
	["pathway",0,undef],
	["reference",0,undef],
	["equation",0,undef],
]);

$input->{compounds} = parse_input_table($In_CpdFile,[
	["id",1],
	["charge",0,undef],
	["formula",0,undef],
	["name",1],
	["aliases",0,undef]
]);

$logger->info("Loading FBAModel WS Object");

use Capture::Tiny qw( capture );
my ($stdout, $stderr, @result) = capture {
    my $fba = get_fba_client();
    $fba->import_fbamodel($input);
};

$logger->info("fbaModelServices import_fbamodel() informational messages\n".$stdout) if $stdout;
$logger->warn("fbaModelServices import_fbamodel() warning messages\n".$stderr) if $stderr;
$logger->info("Loading FBAModel WS Object Complete");

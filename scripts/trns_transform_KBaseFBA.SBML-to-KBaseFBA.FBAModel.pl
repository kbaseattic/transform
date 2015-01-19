#!/usr/bin/env perl
use warnings;
use strict;
use Data::Dumper;
use Getopt::Long;
use Bio::KBase::Transform::ScriptHelpers qw( parse_input_table getStderrLogger );
use Bio::KBase::fbaModelServices::ScriptHelpers qw(fbaws get_fba_client runFBACommand universalFBAScriptCode );

my $script = "trns_transform_KBaseFBA.SBML-to-KBaseFBA.FBAModel.pl";

=head1 NAME

$script

=head1 SYNOPSIS

$script --sbml/-s <Input SBML File> --output/-o <Output Object ID> --out_ws/-w <Workspace to save Object in> --compounds-c <Input Compounds CSV File> --genome/-g <Input Genome ID> --biomass/-b <Input Biomass ID>

=head1 DESCRIPTION

Transform a CSV file into an object in the workspace.

=head1 COMMAND-LINE OPTIONS
$script
	-s --sbml		name of sbml file with model data
	-c --compounds  csv file with compound data
	-o --output     id under which KBaseBiochem.Media is to be saved
	-w --out_ws     workspace where KBaseBiochem.Media is to be saved
	-g --genome		genome for which model was constructed
	-b --biomass	id of biomass reaction in model
	--help          print usage message and exit

=cut

my $logger = getStderrLogger();

my $In_RxnFile   = "";
my $In_CpdFile = "";
my $Out_Object = "";
my $Out_WS    = "";
my $Genome    = "Empty";
my $Biomass   = "";
my $Help      = 0;

GetOptions("sbml=s"  => \$In_RxnFile,
	   "compounds|c=s"  => \$In_CpdFile,
	   "output|o=s" => \$Out_Object,
	   "out_ws|w=s" => \$Out_WS,
	   "genome|g=s" => \$Genome,
	   "biomass|b=s" => \$Biomass,
	   "help|h"     => \$Help);

if($Help || !$In_RxnFile || !$Out_Object || !$Out_WS){
    print($0." --sbml/-s <Input SBML File> --output/-o <Output Object ID> --out_ws/-w <Workspace to save Object in> --compounds/-c <Input Compound CSV File> --genome/-g <Input Genome ID> --biomass/-b <Input Biomass ID>\n");
    $logger->warn($0." --sbml/-s <Input SBML File> --output/-o <Output Object ID> --out_ws/-w <Workspace to save Object in> --compounds/-c <Input Compound CSV File> --genome/-g <Input Genome ID> --biomass/-b <Input Biomass ID>\n");
    exit();
}

$logger->info("Mandatory Data passed = ".join(" | ", ($In_File,$Out_Object,$Out_WS)));
$logger->info("Optional Data passed = ".join(" | ", ("Compounds:".$In_CpdFile,"Genome:".$Genome,"Biomass:".$Biomass)));

my $input = {
	model => $Out_Object,
	workspace => $Out_WS,
	genome_workspace => $Out_WS,
	genome => $Genome,
	sbml => "",
	biomass => $Biomass,
};
if ($Genome eq "Empty") {
	$input->{genome_workspace} = "PlantSEED" ;
}
if (!-e $In_RxnFile) {
	print "Could not find input file:".$In_RxnFile."!\n";
	exit();
}
open(my $fh, "<", $In_RxnFile) || return;
while (my $line = <$fh>) {
	$input->{sbml} .= $line;
}
close($fh);

if (defined($In_CpdFile) && length($In_CpdFile) > 0) {
	$input->{compounds} = parse_input_table($In_CpdFile,[
		["id",1],
		["charge",0,undef],
		["formula",0,undef],
		["name",1],
		["aliases",0,undef]
	]);
}

$logger->info("Loading FBAModel WS Object");

use Capture::Tiny qw( capture );
my ($stdout, $stderr, @result) = capture {
    my $fba = get_fba_client();
    $fba->import_fbamodel($input);
};

$logger->info("fbaModelServices import_fbamodel() informational messages\n".$stdout) if $stdout;
$logger->warn("fbaModelServices import_fbamodel() warning messages\n".$stderr) if $stderr;
$logger->info("Loading FBAModel WS Object Complete");

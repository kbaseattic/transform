#! /usr/bin/env perl
#PERL USE
use strict;
use Data::Dumper;
use JSON;
use Getopt::Long;

#KBASE USE
use Bio::KBase::Transform::ScriptHelpers qw( getStderrLogger );

=head1 NAME

trns_transform_OBO_Ontology_to_KBaseOntology_OntologyDictionary.pl

=head1 SYNOPSIS

trns_transform_OBO_Ontology_to_KBaseOntology_OntologyDictionary.pl --input_file_name fasta-file --output_file_name genome-id

=head1 DESCRIPTION

Transform an OBO file into KBaseOntology.OntologyDictionary object

=head1 COMMAND-LINE OPTIONS
trns_transform_OBO_Ontology_to_KBaseOntology_OntologyDictionary.pl --input_file_name --output_file_name
	-i --input_file_name      OBO file
	-o --output_file_name     id under which KBaseOntology.OntologyDictionary is to be saved
        --help                    print usage message and exit

=cut

my $Command = "../../../lib/obo.pl";

my ($help, $input, $output);
GetOptions("h|help"      => \$help,
	   "i|input_file_name=s" => \$input,
	   "o|output_file_name=s" => \$output
	  ) or die("Error in command line arguments\n");

my $logger = getStderrLogger();

if($help || !$input || !$output){
    print($0." --input_file_name|-i <Input Fasta File> --output_file_name|-o <Output KBaseOntology.OntologyDictionary JSON Flat File>");
    $logger->warn($0." --input_file_name|-i <Input Fasta File> --output_file_name|-o <Output KBaseOntology.OntologyDictionary JSON Flat File>");
    exit();
}
$logger->info("Mandatory Data passed = ".join(" | ", ($input,$output)));

$logger->info("Running OBO transform script");
eval { !system("$Command --to-json $input > $output") or die $ERRNO };
$logger->warn("Unable to run OBO transform script: $Command --to-json $input > $output");




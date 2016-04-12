#! /usr/bin/env perl
#PERL USE
use strict;
use Data::Dumper;
use JSON;
use Getopt::Long;

#KBASE USE
use Bio::KBase::Transform::ScriptHelpers qw( getStderrLogger );

=head1 NAME

trns_transform_KBaseOntology_OntologyDictionary_to_OBO_Ontology.pl

=head1 SYNOPSIS

trns_transform_KBaseOntology_OntologyDictionary_to_OBO_Ontology.pl --input_file_name json-file --output_file_name obo-file

=head1 DESCRIPTION

Transform a KBaseOntology.OntologyDictionary object into OBO file

=head1 COMMAND-LINE OPTIONS
trns_transform_KBaseOntology_OntologyDictionary_to_OBO_Ontology.pl --input_file_name --output_file_name
	-i --input_file_name      KBaseOntology.OntologyDictionary object
	-o --output_file_name     OBO file
        --help                    print usage message and exit

=cut

my $Command = "../core/obo.pl";

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

$logger->info("Running core OBO transform script");
system("$Command --from-json $input > $output");

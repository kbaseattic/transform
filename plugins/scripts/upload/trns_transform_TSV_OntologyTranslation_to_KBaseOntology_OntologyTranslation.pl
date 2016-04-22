#! /usr/bin/env perl
#PERL USE
use strict;
use Getopt::Long;
use Try::Tiny;
use JSON;

#KBASE USE
use Bio::KBase::Transform::ScriptHelpers qw( getStderrLogger );

=head1 NAME

trns_transform_TSV_OntologyTranslation_to_KBaseOntology_OntologyTranslation.pl

=head1 SYNOPSIS

trns_transform_TSV_OntologyTranslation_to_KBaseOntology_OntologyTranslation.pl --input_file_name tsv-file --output_file_name ontology-translation

=head1 DESCRIPTION

Transform a TSV file into KBaseOntology.OntologyTranslation object

=head1 COMMAND-LINE OPTIONS
trns_transform_TSV_OntologyTranslation_to_KBaseOntology_OntologyTranslation.pl --input_file_name --output_file_name
	-i --input_file_name      TSV file
	-o --output_file_name     id under which KBaseOntology.OntologyTranslation is to be saved
        --help                    print usage message and exit

=cut

my $Command = "./ont.pl";

my ($help, $input, $output);
GetOptions("h|help"      => \$help,
	   "i|input_file_name=s" => \$input,
	   "o|output_file_name=s" => \$output
	  ) or die("Error in command line arguments\n");

my $logger = getStderrLogger();

if($help || !$input || !$output){
    print($0." --input_file_name|-i <Input TSV File> --output_file_name|-o <Output KBaseOntology.OntologyTranslation JSON Flat File>");
    $logger->warn($0." --input_file_name|-i <Input TSV File> --output_file_name|-o <Output KBaseOntology.OntologyTranslation JSON Flat File>");
    exit();
}
$logger->info("Mandatory Data passed = ".join(" | ", ($input,$output)));


try {
    $logger->info("Running TSV transform script");
    system("$Command --from-trans $input > $output")
} catch {
    $logger->warn("Unable to run TSV transform script: $Command --from-trans $input > $output");
    die $_;
};

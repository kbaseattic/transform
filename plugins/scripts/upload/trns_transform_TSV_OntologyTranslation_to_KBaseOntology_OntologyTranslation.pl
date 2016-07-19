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
	-i --input_file_name	TSV file
	-o --output_file_name	ID under which KBaseOntology.OntologyTranslation is to be saved
        -1 --first_dict		Name of first KBaseOntology.OntologyDictionary
        -2 --second_dict	Name of second KBaseOntology.OntologyDictionary
        -u --workspace_service_url	Workspace URL
        -w --workspace_name	Workspace
        --help			print usage message and exit

=cut

use File::Basename;
my $Working_Dir=dirname($0);
my $Command = $Working_Dir."/ont.pl";

my ($help, $input, $output, $first, $second, $workspace, $url);
GetOptions("h|help"      => \$help,
	   "i|input_file_name=s" => \$input,
	   "o|output_file_name=s" => \$output,
	   "1|first_dict=s" => \$first,
	   "2|second_dict=s" => \$second,
	   "w|workspace_name=s" => \$workspace,
	   "u|workspace_service_url=s" => \$url
	  ) or die("Error in command line arguments\n");

my $logger = getStderrLogger();

if($help || !$input || !$output || !$first || !$second || !$workspace || !$url){
    print($0." --input_file_name|-i <Input TSV File> --output_file_name|-o <Output KBaseOntology.OntologyTranslation JSON Flat File> --first_dict|-1 <KBaseOntology.OntologyDictionary Name> --second_dict|-2 <KBaseOntology.OntologyDictionary Name>");
    $logger->warn($0." --input_file_name|-i <Input TSV File> --output_file_name|-o <Output KBaseOntology.OntologyTranslation JSON Flat File> --first_dict|-1 <KBaseOntology.OntologyDictionary Name> --second_dict|-2 <KBaseOntology.OntologyDictionary Name>");
    exit();
}
$logger->info("Mandatory Data passed = ".join(" | ", ($input,$output,$first,$second,$url,$workspace)));

my $wsclient = Bio::KBase::workspace::Client->new($url);
my $ret = $wsclient->get_objects([{ name => $first, workspace => $workspace }])->[0];
if(!exists($ret->{data})){
    die "Invalid return from get_objects for workspace=" . $workspace . " name=" . $first;
}

my $wsclient = Bio::KBase::workspace::Client->new($url);
my $ret = $wsclient->get_objects([{ name => $second, workspace => $workspace }])->[0];
if(!exists($ret->{data})){
    die "Invalid return from get_objects for workspace=" . $workspace . " name=" . $second;
}

try {
    $logger->info("Running TSV transform script");
    system("$Command --from-trans $input --first-dict $workspace/$first --second-dict $workspace/$second > $output")
} catch {
    $logger->warn("Unable to run TSV transform script: $Command --from-trans $input > $output");
    die $_;
};

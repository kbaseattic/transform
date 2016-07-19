#! /usr/bin/env perl
#PERL USE
use strict;
use Getopt::Long;
use Try::Tiny;
use JSON;

#KBASE USE
use Bio::KBase::workspace::Client;
use Bio::KBase::Transform::ScriptHelpers qw( getStderrLogger );

=head1 NAME

trns_transform_KBaseOntology_OntologyDictionary_to_OBO_Ontology.pl

=head1 SYNOPSIS

trns_transform_KBaseOntology_OntologyDictionary_to_OBO_Ontology.pl --workspace_service_url url --object_name object --workspace_name workspace --output_file_name obo file

=head1 DESCRIPTION

Transform a KBaseOntology.OntologyDictionary object into OBO file

=head1 COMMAND-LINE OPTIONS
trns_transform_KBaseOntology_OntologyDictionary_to_OBO_Ontology.pl --workspace_service_url --object_name --workspace --output_file_name
        -u --workspace_service_url        Workspace URL
	-i --object_name          KBaseOntology.OntologyDictionary object
        -w --workspace_name       Workspace
	-o --output_file_name     OBO file
        --help                    print usage message and exit

=cut

use File::Basename;
my $Working_Dir=dirname($0);
my $Command = $Working_Dir."/ont.pl";

my ($help, $url, $object, $workspace, $output);
GetOptions("h|help"      => \$help,
	   "i|object_name=s" => \$object,
	   "w|workspace_name=s" => \$workspace,
	   "u|workspace_service_url=s" => \$url,
	   "o|output_file_name=s" => \$output
	  ) or die("Error in command line arguments\n");

my $logger = getStderrLogger();

if($help || !$url || !$object || !$workspace || !$output){
    print($0." --workspace_service_url|_u < Workspace Service URL> --object_name|-i <Input KBaseOntology.OntologyDictionary Object Name> --workspace_name|-w <Workspace Containing Object> --output_file_name|-o <Output OBO File>");
    $logger->warn($0." --workspace_service_url|_u < Workspace Service URL> --object_name|-i <Input KBaseOntology.OntologyDictionary Object Name> --workspace_name|-w <Workspace Containing Object> --output_file_name|-o <Output OBO File>");
    exit();
}
$logger->info("Mandatory Data passed = ".join(" | ", ($url,$object,$workspace,$output)));

my $wsclient = Bio::KBase::workspace::Client->new($url);
my $ret = $wsclient->get_objects([{ name => $object, workspace => $workspace }])->[0];
my $obj;
if(exists($ret->{data})){
    $obj = $ret->{data};
}else{
    die "Invalid return from get_objects for workspace=" . $workspace . " name=" . $object;
}

open(OUT, "> Toy.json");
print OUT to_json($obj, { pretty => 1, ascii => 1});
close(OUT);

try {
    $logger->info("Running OBO transform script");
    system("$Command --to-obo Toy.json > $output")
} catch {
    $logger->warn("Unable to run OBO transform script: $Command --to-obo Toy.json > $output");
    die $_;
};

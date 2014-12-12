#!/usr/bin/env perl
use warnings;
use strict;
use Data::Dumper;
use Getopt::Long;

my $In_File   = "";
my $Out_Model = "";
my $Out_WS    = "";
my $Genome    = "Empty";

GetOptions("in_file|i=s"   => \$In_File,
	   "out_model|o=s" => \$Out_Model,
	   "out_ws|w=s"    => \$Out_WS,
	   "genome|g=s"    => \$Genome);

if(!$In_File || !$Out_Model || !$Out_WS){
    die($0." --in_file|-i <Input Fasta File> --out_model|-o <Output FBAModel ID> --out_ws|-w <Workspace to save FBAModel in>");
}

if(!-f $In_File){
    die("Cannot find $In_File");
}

my $AToken = $ENV{KB_AUTH_TOKEN} ;

if(!$AToken){
    use Bio::KBase::fbaModelServices::ScriptHelpers qw( getToken );
    $AToken = getToken();
}

use Bio::KBase::fbaModelServices::Impl;
my $FBAImpl = Bio::KBase::fbaModelServices::Impl->new({'accounttype' => "kbase",
                                                       'workspace-url' => "http://kbase.us/services/ws"});
$FBAImpl->_setContext(undef,{auth=>$AToken});

open(FH, "< $In_File");
my $sbml;
while(<FH>){$sbml.=$_;}
close(FH);

my $Genome_WS = $Out_WS;
$Genome_WS = "PlantSEED" if $Genome eq "Empty";

my $Model = $In_File; $Model =~ s/\.sbml$/_Model/;

$FBAImpl->import_fbamodel({workspace=>$Out_WS,genome=>$Genome,genome_workspace=>$Genome_WS,sbml=>$sbml,model=>$Model});

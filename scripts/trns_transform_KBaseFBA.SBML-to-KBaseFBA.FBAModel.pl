#!/usr/bin/env perl
use warnings;
use strict;
use Data::Dumper;
use Getopt::Long;

=head1 NAME

trns_transform_KBaseFBA.SBML-to-KBaseFBA.FBAModel.pl

=head1 SYNOPSIS

trns_transform_KBaseFBA.SBML-to-KBaseFBA.FBAModel.pl --input sbml-file --output model-id --out_ws workspace-id [--genome genome-id]

=head1 DESCRIPTION

Transform an SBML file into a KBaseFBA.FBAModel object in the
workspace. A genome object in the same workspace is needed if one
wishes to explore gene-reaction associations.

=head1 COMMAND-LINE OPTIONS
trns_transform_KBaseFBA.SBML-to-KBaseFBA.FBAModel.pl --input --output --out_ws [--genome]
	-i --input      sbml file
	-o --output     id under which KBaseFBA.FBAModel is to be saved
        -w --out_ws     workspace where KBaseFBA.FBAModel is to be saved
        -g --genome     id of KBaseGenomes.Genome object to associate with KBaseFBA.FBAModel. The object must be in the same workspace designated with out_ws
	--help          print usage message and exit

=cut

my $In_File   = "";
my $Out_Model = "";
my $Out_WS    = "";
my $Genome    = "Empty";
my $Help      = 0;

GetOptions("input|i=s"  => \$In_File,
	   "output|o=s" => \$Out_Model,
	   "out_ws|w=s" => \$Out_WS,
	   "genome|g=s" => \$Genome,
	   "help|h"     => \$Help);

if($Help || !$In_File || !$Out_Model || !$Out_WS){
    print($0." --input/-i <Input SBML File> --output/-o <Output FBAModel ID> --out_ws/-w <Workspace to save FBAModel in> --genome/-g <Input Genome ID>");
    exit();
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

__END__

    Logging:

Log output format
           Datetime in UTC - name of script - log level:
 log message
<YYYY-MM-DDTHH:mm:SS>
 - <script_name> - <level>: <message>

           e.g., 2014-12-10T00:00:00Z - trns_transform_KBaseGenomes.GBK-to-KBaseGenomes.Genome
 - INFO: Validating input file sample.gbff




#1 How many <level> do you plan to support?
#2 What?s the failure report LEVEL? FATAL, FAIL, ???
#3 Do you have any recommended library to use to dump the above format?

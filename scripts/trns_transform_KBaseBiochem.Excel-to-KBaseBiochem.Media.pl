#!/usr/bin/env perl
use warnings;
use strict;
use Data::Dumper;
use Getopt::Long;
use Bio::KBase::Transform::ScriptHelpers qw( parse_excel parse_input_table );
use Bio::KBase::fbaModelServices::ScriptHelpers qw( fbaws get_fba_client runFBACommand universalFBAScriptCode );

=head1 NAME

trns_transform_KBaseBiochem.Excel-to-KBaseBiochem.Media.pl

=head1 SYNOPSIS

trns_transform_KBaseBiochem.Excel-to-KBaseBiochem.Media.pl --input excel-file --output media-id --out_ws workspace-id

=head1 DESCRIPTION

Transform an Excel file into an object in the workspace.

=head1 COMMAND-LINE OPTIONS
trns_transform_KBaseBiochem.Excel-to-KBaseBiochem.Media.pl --input --output --out_ws
	-i --input      excel file
	-o --output     id under which KBaseBiochem.Media is to be saved
	-w --out_ws     workspace where KBaseBiochem.Media is to be saved
	--help          print usage message and exit

=cut

my $In_File   = "";
my $Out_Object = "";
my $Out_WS    = "";
my $Help      = 0;

GetOptions("input|i=s"  => \$In_File,
	   "output|o=s" => \$Out_Object,
	   "out_ws|w=s" => \$Out_WS,
	   "help|h"     => \$Help);

if($Help || !$In_File || !$Out_Object || !$Out_WS){
    print($0." --input/-i <Input Excel File> --output/-o <Output Object ID> --out_ws/-w <Workspace to save Object in>\n");
    exit();
}

my $sheets = parse_excel($In_File);
my $Media = (grep { $_ =~ /[Mm]edia/ } keys %$sheets)[0];
my $mediadata = parse_input_table($sheets->{$Media},[
	["compounds",1],
	["concentrations",0,"0.001"],
	["minflux",0,"-100"],
	["maxflux",0,"100"],
]);

foreach my $sheet (keys %$sheets){
    system("rm ".$sheets->{$sheet});
}

my $input = {media => $Out_Object,workspace => $Out_WS};
for (my $i=0; $i < @{$mediadata}; $i++) {
	push(@{$input->{compounds}},$mediadata->[$i]->[0]);
	push(@{$input->{maxflux}},$mediadata->[$i]->[3]);
	push(@{$input->{minflux}},$mediadata->[$i]->[2]);
	push(@{$input->{concentrations}},$mediadata->[$i]->[1]);
}

my $fba = get_fba_client();

$fba->addmedia($input);

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

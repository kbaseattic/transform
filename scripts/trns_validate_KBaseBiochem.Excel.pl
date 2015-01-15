#!/usr/bin/env perl
use warnings;
use strict;
use Data::Dumper;
use Getopt::Long;
use Spreadsheet::ParseExcel;
use Spreadsheet::XLSX;
use Bio::KBase::Transform::ScriptHelpers qw( parse_excel );

my $In_File = "";
my $Help = 0;
GetOptions("input|i=s"  => \$In_File,
	   "help|h"     => \$Help);

if($Help || !$In_File){
    print($0." --input/-i <Input Excel File>");
    exit(0);
}

if(!-f $In_File){
    die("Cannot find $In_File");
}

my $sheets = parse_excel($In_File);

if(!exists($sheets->{Media}) && !exists($sheets->{media})){
    die("$In_File does not contain a worksheet for media which should be named 'Media'");
}

foreach my $sheet (keys %$sheets){
    system("rm ".$sheets->{$sheet});
}

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

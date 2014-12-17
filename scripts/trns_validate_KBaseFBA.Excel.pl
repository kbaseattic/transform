#!/usr/bin/env perl
use warnings;
use strict;
use Data::Dumper;
use Getopt::Long;
use Spreadsheet::ParseExcel;
use Spreadsheet::XLSX;

my $In_File   = "";
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

if($In_File !~ /\.xlsx?$/){
    die("$In_File does not have excel suffix (.xls or .xlsx)");
}

if($In_File =~ /\.xlsx$/){
    eval {
	my $excel = Spreadsheet::XLSX->new($In_File);
    };
    if ($@) {
	#Logging
	#print "Failed Validation\n";
	#print "ERROR_MESSAGE\n".$@."END_ERROR_MESSAGE\n";
	exit(1);
    }else{
	exit(0);
    }
}else{
    my $parser   = Spreadsheet::ParseExcel->new();
    my $workbook = $parser->parse($In_File);
    if (!defined $workbook) {
	#logging
	#print $parser->error(),".\n";
	exit(1);
    }else{
	exit(0);
    }
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

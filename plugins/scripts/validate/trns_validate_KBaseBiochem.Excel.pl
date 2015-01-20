#!/usr/bin/env perl
use warnings;
use strict;
use Data::Dumper;
use Getopt::Long;
use Spreadsheet::ParseExcel;
use Spreadsheet::XLSX;
use Bio::KBase::Transform::ScriptHelpers qw( parse_excel getStderrLogger );

my $logger = getStderrLogger();

my $In_File = "";
my $Help = 0;
GetOptions("input|i=s"  => \$In_File,
	   "help|h"     => \$Help);

if($Help || !$In_File){
    print($0." --input/-i <Input Excel File>");
    $logger->warn($0." --in_file|-i <Input Excel File>");
    exit(0);
}

if(!-f $In_File){
    $logger->warn("Cannot find file ".$In_File);
    die("Cannot find $In_File");
}

my $sheets = parse_excel($In_File);

if(!exists($sheets->{Media}) && !exists($sheets->{media})){
    $logger->warn("$In_File does not contain a worksheet for media which should be named 'Media'");
    die("$In_File does not contain a worksheet for media which should be named 'Media'");
}

foreach my $sheet (keys %$sheets){
    system("rm ".$sheets->{$sheet});
}

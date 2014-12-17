#!/usr/bin/env perl
use warnings;
use strict;
use Data::Dumper;
use Getopt::Long;
use File::Stream;

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

if($In_File !~ /\.([ct]sv|txt)$/){
    die("$In_File does not have correct suffix (.txt or .csv or .tsv)");
}

#Open File, making sure to be able to read DOS/WINDOWS/MAC files
open(my $fh, "< $In_File");
my $stream = (File::Stream->new($fh, separator => qr{[\cM\r\n]}))[1];
my $Header_Line=<$stream>;
chomp $Header_Line;

#Check Comma or Tab
my %Headers = map { uc($_) => 1 } split(/,/,$Header_Line);
if(scalar(keys %Headers) < 2){
    print join("\n", map {uc($_)} split(/\t/,$Header_Line)),"\n";
    %Headers = map { uc($_) => 1 } split(/\t/,$Header_Line);
    if(scalar(keys %Headers) < 2){
	die("$In_File either does not use commas or tabs as a separator, or does not have enough columns");
    }
}

#Check Obligatory Headers
#For now, id, direction, gpr, equation for reactions and id, name, charge, formula for compounds
my ($reactions,$compounds) = (1,1);
if(!exists($Headers{ID}) || !exists($Headers{DIRECTION}) || !exists($Headers{GPR}) || !exists($Headers{EQUATION})){
    $reactions=0;
}

if(!exists($Headers{ID}) || !exists($Headers{NAME}) || !exists($Headers{CHARGE}) || !exists($Headers{FORMULA})){
    $compounds=0;
}

if(!$reactions && !$compounds){
    die("$In_File does not contain the obligatory headers for either reactions (ID,DIRECTION,GPR,EQUATION) or compounds (ID,NAME,CHARGE,FORMULA)\n");
}elsif($reactions && $compounds){
    #Possible problem with mixing column headers, but wouldn't affect ModelSEED code if proper arguments used
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

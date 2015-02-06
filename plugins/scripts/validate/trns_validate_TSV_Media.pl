#!/usr/bin/env perl
#PERL USE
use warnings;
use strict;
use Data::Dumper;
use Getopt::Long;
use File::Stream;

#KBASE USE
use Bio::KBase::Transform::ScriptHelpers qw( getStderrLogger );

my $logger = getStderrLogger();
my $In_File   = "";
my $Help = 0;
GetOptions("input_file_name|i=s"  => \$In_File,
	   "help|h"     => \$Help);

if($Help || !$In_File){
    print($0." --input_file_name/-i <Input TSV File>");
    $logger->warn($0." --input_file_name|-i <Input TSV File>");
    exit(0);
}

if(!-f $In_File){
    $logger->warn("Cannot find file ".$In_File);
    die("Cannot find $In_File");
}

if($In_File !~ /\.(tsv|txt)$/){
    $logger->warn("$In_File does not have correct suffix (.txt or .tsv)");
    die("$In_File does not have correct suffix (.txt or .tsv)");
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
	$logger->warn("$In_File either does not use commas or tabs as a separator, or does not have enough columns");
	die("$In_File either does not use commas or tabs as a separator, or does not have enough columns");
    }
}

#Check Obligatory Headers
if(!exists($Headers{ID}) || !exists($Headers{NAME})){
    $logger->warn("$In_File does not contain the obligatory headers for either reactions (ID,DIRECTION,GPR,EQUATION) or compounds (ID,NAME,CHARGE,FORMULA) or media (ID, NAME)\n");
    die("$In_File does not contain the obligatory headers for either reactions (ID,DIRECTION,GPR,EQUATION) or compounds (ID,NAME,CHARGE,FORMULA) or media (ID, NAME)\n");
}

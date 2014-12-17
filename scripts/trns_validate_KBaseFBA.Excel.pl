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

my $excel = '';
my @worksheets = ();
if($In_File =~ /\.xlsx$/){
    eval {
	$excel = Spreadsheet::XLSX->new($In_File);
    };
    if ($@) {
	#Logging
	#print "Failed Validation\n";
	#print "ERROR_MESSAGE\n".$@."END_ERROR_MESSAGE\n";
	exit(1);
    }else{
	@worksheets = @{$excel->{Worksheet}};
    }
}else{
    $excel   = Spreadsheet::ParseExcel->new();
    my $workbook = $excel->parse($In_File);
    if(!defined $workbook){
	#logging
	#print $parser->error(),".\n";
	exit(1);
    }else{
	@worksheets = $workbook->worksheets();
    }
}

#Check to see if appropriate sheets exist
my ($compounds,$reactions,$media)=(0,0,0);
foreach my $sheet (@worksheets){
    $compounds=$sheet if $sheet->{Name} =~ /compounds/i;
    $reactions=$sheet if $sheet->{Name} =~ /reactions/i;
    $media=$sheet if $sheet->{Name} =~ /media/i;
}

if((!$reactions || !$compounds) && !$media){
    die("$In_File does not contain sheets for compounds, reactions, or media, which should be named 'Compounds', 'Reactions', and 'Media' respectively");
}

#special case, where, if compounds present, reactions should be
if(!$reactions && $compounds){
    die("$In_File contains a compounds sheet but not a reaction sheet, which is necessary for model construction");
}

#Check Headers, must be in first row
my %Headers=();
foreach my $col ($compounds->{MinCol}..$compounds->{MaxCol}) {
    my $cell = $compounds->{Cells}[$compounds->{MinRow}][$col];
    $Headers{uc($cell->{Val})}=1;
}

if(!exists($Headers{ID}) || !exists($Headers{NAME}) || !exists($Headers{CHARGE}) || !exists($Headers{FORMULA})){
    die("Sheet named ".$compounds->{Name}." in $In_File does not contain the obligatory headers for compounds (ID,NAME,CHARGE,FORMULA)\n");
}

undef(%Headers);
foreach my $col ($reactions->{MinCol}..$reactions->{MaxCol}) {
    my $cell = $reactions->{Cells}[$reactions->{MinRow}][$col];
    $Headers{uc($cell->{Val})}=1;
}

if(!exists($Headers{ID}) || !exists($Headers{DIRECTION}) || !exists($Headers{GPR}) || !exists($Headers{EQUATION})){
    die("Sheet named ".$reactions->{Name}." in $In_File does not contain the obligatory headers for reactions (ID,DIRECTION,GPR,EQUATION)\n");
}

#Media sheet requires commonly named headers, so exit now if they are present
exit(0) if scalar(keys %Headers);

undef(%Headers);
foreach my $col ($media->{MinCol}..$media->{MaxCol}) {
    my $cell = $media->{Cells}[$media->{MinRow}][$col];
    $Headers{uc($cell->{Val})}=1;
}

if(!exists($Headers{ID}) || !exists($Headers{NAME})){
    die("Sheet named ".$media->{Name}." in $In_File does not contain the obligatory headers for media (ID,NAME)\n");
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

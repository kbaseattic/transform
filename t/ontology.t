#! /usr/bin/env perl

use strict vars;

use Carp;
use Test::More;
use Data::Dumper;
use English;
use Getopt::Long;
use JSON;

my $usage = "$0 [options] [test1 test2 ...]\n";

my $command = "../plugins/scripts/core/obo.pl";
my ($help, $dir, $dry);

my $rc = GetOptions("h|help"  => \$help,
                    "d|dir=s" => \$dir,
                    "dry"     => \$dry,
                   ) or die $usage;

my @all_tests = discover_own_tests();

print("Test list:");
print(join(', ', @all_tests));

my @tests = @ARGV > 0 ? @ARGV : @all_tests;

if ($dir) {
    run("mkdir -p $dir");
    chdir($dir);
}

my $testCount = 0;
foreach my $testname (@tests) {
    my $test = "test_" . $testname;
    print "\n> Testing $testname...\n";
    if (!defined &$test) {
        print "Test routine doesn't exist: $test\n";
        next;
    }
    &$test();
}
done_testing($testCount);

sub test_transformation {
    transform_from_and_back_to_obo("Toy_Ontology");
}

sub transform_from_and_back_to_obo {
    my ($filebase) = @_;
    my $obo = "$filebase.obo";
    my $json = "$filebase.json";
    sysrun("$command --to-json $obo >$json");
    sysrun("$command --from-json $json >$obo.2");
    system("diff $obo $obo.2 > $obo.diff");
    my $out = sysout("cat $obo.diff");
    ok($out eq '', "No diff between $obo and $obo.2"); $testCount++;
}

sub discover_own_tests {
    my $self = $0;
    my @funcs = map { /^sub test_(\S+)/ ? $1 : () } `cat $self`;
    wantarray ? @funcs : \@funcs;
}

sub sysrun {
    my ($command, $message) = @_;
    $message ||= abbrev_cmd($command);

    if ($dry) {
        print $command."\n"; return;
    }

    $testCount++;
    eval { !system($command) or die $ERRNO };
    diag("unable to run: $command") if $EVAL_ERROR;
    ok(!$EVAL_ERROR, (caller(1))[3] ." > ". $message);

    exit_if_ctrl_c($CHILD_ERROR);
}

sub sysout {
    my ($command, $message, $expected_error) = @_;
    $message ||= abbrev_cmd($command);

    $testCount++;

    my $out;
    if (! $expected_error) {
        eval { $out = `$command` };
        diag("unable to run: $command") if $EVAL_ERROR;
        ok(!$CHILD_ERROR, (caller(1))[3] ." > ". $message);
        diag("errno: $CHILD_ERROR") if $CHILD_ERROR;
    } else {
        eval { $out = `$command 2>/dev/stdout` };
        my $rc = ($CHILD_ERROR >> 8);
        ok($rc == $expected_error || $rc == 255, # perl die returns 65280 (=255<<8)
           "Expecting error $expected_error: ". (caller(1))[3] ." > ". $message);
    }

    exit_if_ctrl_c($CHILD_ERROR);

    chomp($out); $out =~ s/\n$//;
    wantarray ? split(/\n/, $out) : $out;
}

sub exit_if_ctrl_c {
    my ($errno) = @_;
    if ($errno != -1 && (($errno & 127) == 2) && (!($errno & 128))) {
        print "\nTest terminated by user interrupt.\n\n";
        exit;
    }
}

sub abbrev_cmd { length $_[0] < 60 ? $_[0] : substr($_[0], 0, 60)."..." }

sub whoami { (caller(1))[3] }

sub run { system(@_) == 0 or confess("FAILED: ". join(" ", @_)); }

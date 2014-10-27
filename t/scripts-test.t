use strict;
use warnings;
use Bio::KBase::workspaceService::Client;
use Bio::KBase::AuthToken;
use Bio::KBase::CoExpression::Client;
use JSON::XS;
use Test::More;
use Data::Dumper;
use File::Temp qw(tempfile);
use Getopt::Long::Descriptive;
use Text::Table;
use Test::Cmd;


#by Fei, July 29, 2014.
# 1. use kbase-login as kbasetest before running this script
# 2. 


my $ws_id='kbasetest:home';
my $ws_url='http://localhost:7058';
my $in_id ='test_pair';
my $out_id ='test_pair2';

my $tmp;
my $bin="scripts";


my $tes = Test::Cmd->new(prog => "$bin/mys_example_wrapper.py", workdir => '', interpreter => '/usr/bin/python');
ok($tes, "creating Test::Cmd object for mys_example_wrapper.py");
$tes->run(args => '-h');
ok($? == 0,"Running mys_example_wrapper: producing help file");

$tes->run(args => "--ws_url=$ws_url  --ws_id=$ws_id   --in_id=$in_id --out_id=$out_id --method=anova --p_value=0.01");
ok($? == 0,"Running mys_example_wrapper, anova, 0.01 ");
$tmp=$tes->stdout;

# Add retrive data from WS and check the results are correct 

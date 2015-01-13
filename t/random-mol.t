use strict;
use Bio::KBase::Transform::Client;
use Test::More tests => 5;
use Data::Dumper;
use Test::Cmd;
use JSON;
use List::Util qw(shuffle);


die "Usage: perl $0 transform_url ws_name ws_obj_prefix num_random_test config_path" if $#ARGV !=4;
my $transform_url = $ARGV[0];
my $ws_name = $ARGV[1];
my $ws_obj_prefix = $ARGV[2];
my $num_random_test = $ARGV[3];
my $config_path = $ARGV[4];

my $SRC = 'http://www.microbesonline.org/cgi-bin/fetchGenome2.cgi?taxId=g1&byFavorites=1&includeVirusesPlasmids=1';

my @lines = `curl -s '$SRC'`;
my @tids = ();

foreach my $ln (@lines) {
  my @slns = split /HREF/, $ln;
  @slns = grep /genomeInfo/, @slns;
  for my $sln (@slns) {
    $sln =~ s/^.*tId=//;
    $sln =~ s/">.*$//;
    push @tids, $sln;
  }
}
# slow but doesn't matter
@tids = shuffle @tids;
@tids = shuffle @tids;

for( my $i = 0; $i < $num_random_test; $i++) {
  my $fn = "$config_path/upload-KBaseGenomes.GBK-to-KBaseGenomes.Genome_randomtest_s.$ws_obj_prefix.$i.$tids[$i].json";
  open CFG, ">$fn" or die "Couldn't open $fn\n";
  my $config = {};
  $config->{test_name} = "upload success test from MOL GBK to KB WS Genome - randomized test for MOL tax id = $tids[$i]";
  $config->{test_server_url} = $transform_url;
  $config->{input_data_url} = ["http://www.microbesonline.org/cgi-bin/genomeInfo.cgi?tId=$tids[$i];export=gbk;compress=zip"];
  $config->{external_type} = 'KBaseGenomes.FASTA';
  $config->{'kbase_type'}='KBaseGenomes.Genome';
  $config->{'ws_name'}=$ws_name;
  $config->{'obj_name'}="$ws_obj_prefix-$tids[$i]";
  $config->{'max_wait_sec'}='300';
  $config->{'check_interval'}='3';
  $config->{'optional_args'}='{}';
  $config->{'expected_result'}='1';
  $config->{'skip_server_test'}='true';
  my $cfg_json = to_json($config);
  print CFG $cfg_json;
  close CFG;

  # might execute test here
  
  
  my $fn = "$config_path/upload-KBaseGenomes.GBK-to-KBaseGenomes.Genome_randomtest_f_bad_input.$ws_obj_prefix.$i.$tids[$i].json";
  $config->{test_name} = "upload failure test from MOL GBK to KB WS Genome - randomized test for MOL tax id = $tids[$i] - bad input";
  $config->{input_data_url} = ["http://www.microbesonline.org/cgi-bin/genomeInfo.cgi?tId=$tids[$i];export=tab;compress=zip"];
  $config->{'expected_result'}='1';
  $cfg_json = to_json($config);
  open CFG, ">$fn" or die "Couldn't open $fn\n";
  print CFG $cfg_json;
  close CFG;

  # might execute test here
}

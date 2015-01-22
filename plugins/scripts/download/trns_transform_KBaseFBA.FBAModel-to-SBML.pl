use strict;

# BEGIN spec
# "KBaseFBA.FBAModel-to-SBML": {
#   "cmd_args": {
#     "input": "-i",
#	  "workspace": "-w",
#     "output": "-o",
#     },
#     "cmd_description": "KBaseFBA.FBAModel to SBML",
#     "cmd_name": "trns_transform_KBaseFBA.FBAModel-to-SBML.pl",
#     "max_runtime": 3600,
#     "opt_args": {
# 	 }
#   }
# }
# END spec

#PERL USE
use JSON::XS;
use Getopt::Long::Descriptive;

#KBASE USE
use Bio::KBase::workspace::Client;
use Bio::KBase::Transform::ScriptHelpers qw(getStderrLogger write_csv_tables get_input_fh get_output_fh load_input write_output write_text_output genome_to_gto);
use Bio::KBase::fbaModelServices::ScriptHelpers qw(fbaws get_fba_client runFBACommand universalFBAScriptCode );

my($opt, $usage) = describe_options("%c %o",
				    ['input_file_name|i=s', 'workspace object id from which the input is to be read'],
				    ['workspace_name|w=s', 'workspace id from which the input is to be read'],
				    ['url=s', 'URL for the genome annotation service'],
				    ['help|h', 'show this help message'],
				    );

print($usage->text), exit  if $opt->help;
print($usage->text), exit 1 unless @ARGV == 0;

my $logger = getStderrLogger();
$logger->info("Generating SBML for WS model");

my $output;
use Capture::Tiny qw( capture );
my ($stdout, $stderr, @result) = capture {
    my $fba = get_fba_client();
    $output = $fba->export_fbamodel({
    	workspace => $opt->{workspace_name},
    	model => $opt->{input_file_name},
    	format => "sbml"
    });
};

$logger->info("fbaModelServices export_fbamodel() informational messages\n".$stdout) if $stdout;
$logger->warn("fbaModelServices export_fbamodel() warning messages\n".$stderr) if $stderr;
$logger->info("Export of FBAModel to SBML complete");

open(OUT, "> ".$opt->{workspace_name}."-".$opt->{input_file_name}."-SBML.xml");
print OUT $output;
close(OUT);

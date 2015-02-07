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
				    ['object_name=s', 'workspace object name from which the input is to be read'],
				    ['workspace_name=s', 'workspace name from which the input is to be read'],
				    ['fba_service_url=s', 'fba service url to use'],
				    ['workspace_service_url=s', 'workspace service url to pull from'],
				    ['help|h', 'show this help message'],
				    );

print($usage->text), exit  if $opt->help;
print($usage->text), exit 1 unless @ARGV == 0;

my $logger = getStderrLogger();
$logger->info("Generating SBML for WS model");

my $output;
use Capture::Tiny qw( capture );
my ($stdout, $stderr, @result) = capture {
    my $fba = get_fba_client($opt->{fba_service_url});
    my $input = {
    	workspace => $opt->{workspace_name},
    	model => $opt->{object_name},
    	format => "sbml"
    };
    if (defined($opt->{workspace_service_url})) {
    	$input->{wsurl} = $opt->{workspace_service_url};
    }
    $output = $fba->export_fbamodel($input);
};

$logger->info("fbaModelServices export_fbamodel() informational messages\n".$stdout) if $stdout;
$logger->warn("fbaModelServices export_fbamodel() warning messages\n".$stderr) if $stderr;
$logger->info("Export of FBAModel to SBML complete");

open(OUT, "> ".$opt->{workspace_name}."-".$opt->{object_name}."-SBML.xml");
print OUT $output;
close(OUT);
